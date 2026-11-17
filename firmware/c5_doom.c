/* SPDX-License-Identifier: GPL-2.0-or-later
 * Standalone native DOOM; every resource is read from local compressed Flash.
 * Bootloader private LCD/USB ABI is pinned to the owner's verified image.
 */
#include <stdint.h>
#include <stddef.h>
#include "assets.h"
#include "display.h"
#include "pc.h"
#define REG(a) (*(volatile uint32_t *)(a))
#define BYTE(a) (*(volatile uint8_t *)(a))
#define CALL0(a) ((uint32_t (*)(void))((a)|1u))
#define CALL1(a) ((void (*)(uint32_t))((a)|1u))
#define CALL2(a) ((void (*)(uint32_t,uint32_t))((a)|1u))
#define CALL3(a) ((void (*)(uint32_t,uint32_t,uint32_t))((a)|1u))
#define TICKS REG(0x2000013c)
extern uint32_t _sdata[],_edata[],_sidata[],_sbss[],_ebss[];
extern const uint8_t font8x8[95][8];
extern void km_doom_init(void),km_doom_step(void);
extern int km_doom_menu(void);
static void service(void);
void km_fail(const char *) __attribute__((noreturn));
static uint32_t state,frames,core_clock,first_frame_ms,render_ms,present_ms;
static unsigned lcd_ready,usb_ready,has_session;
static uint8_t session[8];
static unsigned stable_keys,candidate_keys;
static uint32_t key_changed,session_tick;
static uint16_t error_code;
static char error_text[36];

static void put32(uint8_t *p,uint32_t v) { for(unsigned i=0;i<4;++i)p[i]=(uint8_t)(v>>(i*8)); }
static void put16(uint8_t *p,unsigned v) { p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8); }
void systick_handler(void) { TICKS++; }
static unsigned raw_keys(void) {
    unsigned a=REG(0x40010808),b=REG(0x40010c08);
    return (!(b&0x4000))|((!(b&0x8000))<<1)|((!(a&0x2000))<<2)|((!(a&0x4000))<<3);
}
static void keys_update(void) {
    unsigned k=raw_keys();
    if(k!=candidate_keys){candidate_keys=k;key_changed=TICKS;}
    if((uint32_t)(TICKS-key_changed)>=20)stable_keys=k;
}
static void window(unsigned x,unsigned y,unsigned w,unsigned h) {
    CALL3(0x08001d70)(0x2a,x,x+w-1);
    CALL3(0x08001d70)(0x2b,y+34,y+h-1+34);
    CALL1(0x08001d4c)(0x2c);
}
static void rect(unsigned x,unsigned y,unsigned w,unsigned h,uint16_t color) {
    if(!w||!h||x+w>320||y+h>172)return;
    window(x,y,w,h);CALL2(0x08001dd4)(color,w*h);
}
static void label(unsigned x,unsigned y,const char *s,uint16_t color) {
    for(;*s && x+8<=320;s++,x+=8) {
        unsigned c=(uint8_t)*s;if(c<32||c>126)c='?';
        for(unsigned r=0;r<8;r++)for(unsigned col=0;col<8;col++)
            if(font8x8[c-32][r]&(128u>>col))rect(x+col,y+r,1,1,color);
    }
}
static unsigned stack_free(void) {
    const volatile uint32_t *p=_ebss;
    while((uintptr_t)p<0x20015000u && *p==0xa55aa55au)p++;
    return (unsigned)((uintptr_t)p-(uintptr_t)_ebss);
}
static void reply_status(const uint8_t *req) {
    uint8_t p[52];
    for(unsigned i=0;i<16;i++)p[i]=req[10+i];
    p[16]=(uint8_t)state;p[17]=(uint8_t)stable_keys;put16(p+18,error_code);
    put32(p+20,TICKS);put32(p+24,frames);put32(p+28,c5_pc_held_keys(TICKS));
    put32(p+32,first_frame_ms);put16(p+36,render_ms>65535?65535:render_ms);put16(p+38,present_ms>65535?65535:present_ms);
    put32(p+40,c5_assets_decodes());put32(p+44,core_clock);put32(p+48,stack_free());
    ((void (*)(unsigned,const void*,unsigned))0x08002ec1)(0x91,p,52);
}
static void service(void) {
    keys_update();
    if(!usb_ready)return;
    volatile uint8_t *rx=(volatile uint8_t *)0x200001e4;
    if(!rx[8] || !((unsigned (*)(unsigned))0x08002ba9)(1))return;
    uint8_t req[64];
    __asm volatile("cpsid i":::"memory");
    for(unsigned i=0;i<64;i++)req[i]=rx[i];rx[8]=0;
    __asm volatile("cpsie i":::"memory");
    CALL0(0x0800289c)();
    if(req[9]<16 || req[9]>52 || req[10]!='C'||req[11]!='5'||req[12]!='D'||req[13]!='9')return;
    unsigned same=has_session;
    for(unsigned i=0;i<8;i++)if(session[i]!=req[18+i])same=0;
    if(has_session && !same && (uint32_t)(TICKS-session_tick)>2000 && req[8]==0x90 && req[9]==16){has_session=0;c5_pc_release();}
    if(!has_session) {
        if(req[8]!=0x90 || req[9]!=16)return;
        unsigned nonzero=0;for(unsigned i=0;i<8;i++)nonzero|=req[18+i];if(!nonzero)return;
        for(unsigned i=0;i<8;i++)session[i]=req[18+i];has_session=1;
    }
    for(unsigned i=0;i<8;i++)if(session[i]!=req[18+i])return;
    session_tick=TICKS;
    if(req[8]==0x90 && req[9]==16) { /* status */ }
    else if(req[8]==0x98 && req[9]==18 && req[27]<=1){c5_pc_keys(req[26],req[27],TICKS);}
    else if(req[8]==0x9e && req[9]==18 && c5_settings_request(req[26],req[27])){
        uint8_t p[52]={0};for(unsigned i=0;i<16;i++)p[i]=req[10+i];
        c5_settings_info(p+16);((void (*)(unsigned,const void*,unsigned))0x08002ec1)(0x9f,p,52);return;
    }
    else if(req[8]==0x9a && req[9]==17 && req[26]<=1){
        if(!req[26])c5_pc_begin(TICKS);
        uint8_t p[52]={0};for(unsigned i=0;i<16;i++)p[i]=req[10+i];
        c5_pc_info(p+16,TICKS);
        ((void (*)(unsigned,const void*,unsigned))0x08002ec1)(0x9b,p,52);return;
    }
    else if(req[8]==0x9c && req[9]==22){
        uint32_t id=0;for(unsigned i=0;i<4;i++)id|=(uint32_t)req[26+i]<<(8*i);
        unsigned off=req[30]|((unsigned)req[31]<<8);
        uint8_t p[52]={0};for(unsigned i=0;i<16;i++)p[i]=req[10+i];
        put32(p+16,id);put16(p+20,off);p[22]=(uint8_t)c5_pc_chunk(id,off,p+24,TICKS);
        ((void (*)(unsigned,const void*,unsigned))0x08002ec1)(0x9d,p,52);return;
    }
    else if(req[8]==0x96 && req[9]==16) {
        uint8_t p[52];for(unsigned i=0;i<16;i++)p[i]=req[10+i];
        for(unsigned i=0;i<36;i++)p[16+i]=(uint8_t)error_text[i];
        ((void (*)(unsigned,const void*,unsigned))0x08002ec1)(0x97,p,52);return;
    } else return;
    reply_status(req);
}
void km_fail(const char *message) {
    if(!error_code)error_code=1;state=3;
    unsigned i=0;for(;i<35 && message[i];i++)error_text[i]=message[i];error_text[i]=0;
    if(lcd_ready){rect(0,0,320,32,0x7800);label(4,4,"C5 DOOM ERROR",0xffff);label(4,18,error_text,0xffff);}
    for(;;)service();
}
/* Exception handler resets only the stack, then shows fault registers. The
 * USB ISR cannot run inside HardFault; recovery is the already tested DFU path. */
static void fault_hex(unsigned y,const char *name,uint32_t v) {
    char s[9];
    for(unsigned i=0;i<8;i++)s[i]="0123456789ABCDEF"[(v>>(28-i*4))&15];s[8]=0;
    label(4,y,name,0xffff);label(60,y,s,0xffff);
}
void fault_display(const uint32_t *stack,uint32_t exc_return) __attribute__((noreturn));
void fault_display(const uint32_t *stack,uint32_t exc_return) {
    uint32_t cfsr=REG(0xe000ed28),pc=0,lr=0;
    uintptr_t at=(uintptr_t)stack;
    if((exc_return&0xffffffe0u)==0xffffffe0u) {
        if(!(exc_return&16u))at+=18*4; /* extended floating-point exception frame */
        if(!(at&3u) && at>=0x20000000u && at<=0x20018000u-32) {
            const uint32_t *frame=(const uint32_t *)at;pc=frame[6];lr=frame[5];
        }
    }
    if(lcd_ready) {
        rect(0,0,320,64,0xf800);label(4,4,"C5 CPU FAULT - RETURN TO DFU",0xffff);
        fault_hex(20,"CFSR",cfsr);fault_hex(34,"PC",pc);fault_hex(48,"LR",lr);
    }
    for(;;)__asm volatile("nop");
}
__attribute__((naked)) void fault_handler(void) {
    __asm volatile("cpsid i\ntst lr,#4\nite eq\nmrseq r0,msp\nmrsne r0,psp\nmov r1,lr\nldr r2,=0x20017000\nmsr msp,r2\nb fault_display");
}
uint32_t km_millis(void){return TICKS;}
void km_sleep(uint32_t ms){uint32_t start=TICKS;while((uint32_t)(TICKS-start)<ms)service();}
void km_exit(void){km_fail("EXIT - RECONNECT TO RESTART");}
uint32_t km_keys(void) {
    service();unsigned k=stable_keys,pc=c5_pc_poll_keys(TICKS);
    if(km_doom_menu())return pc|((k&1)?2u:0)|((k&2)?128u:0)|((k&4)?64u:0)|((k&8)?32u:0);
    if((k&12)==12)return pc|32;
    if((k&3)==3)return pc|16;
    return pc|((k&1)?4u:0)|((k&2)?8u:0)|((k&4)?2u:0)|((k&8)?1u:0);
}
void c5_asset_yield(void){service();}
void c5_jpeg_yield(void){service();}
/* Boot 08001E34 -> 0800138C -> 08002840 writes TIMER4 CCR3 at40000838.
 * Boot init 08001830 sets ARR=99, hence duty10..100 out of100. */
void c5_lcd_brightness(unsigned percent){CALL1(0x08001e34)(percent);}
void km_flash_read(uint32_t at,void *dst,uint32_t count) {
    if(!c5_assets_read(at,dst,count))km_fail("LOCAL ASSET DECODE");
}
void km_set_palette(const uint16_t *p){c5_frame_palette(p);}
void km_index_column(int x,int y,int h,const uint8_t *p,unsigned ui) {
    (void)ui;
    if(!c5_frame_column(x,y,h,p))km_fail("FRAME COLUMN RANGE");
    service();
}
void km_column(int x,int y,int h,const uint16_t *p) {
    if(!c5_frame_rgb_column(x,y,h,p))km_fail("FRAME RGB RANGE");
    service();
}
/* These registers and masks are reproduced from the hash-pinned boot ABI:
 * 08001DB0: PB4 D/C high, PA15 CS low/high; 08001A74: SPI3 +8 bits 2/128;
 * 080013FA: halfword store at SPI3 +12. Clock and mode remain boot-configured.
 * Keep CS low for the whole completed frame; wait TX empty per word and BUSY
 * only at the end. USB ISR does not use SPI3. No DMA or clock changes.
 */
#define SPI_STATUS (*(volatile uint16_t *)0x40003c08)
#define SPI_DATA (*(volatile uint16_t *)0x40003c0c)
static int frame_present(void) {
    window(0,0,320,172);
    REG(0x40010c10)=0x10;REG(0x40010814)=0x8000;
    uint32_t start=TICKS;
    for(unsigned y=0;y<172;y++) {
        for(unsigned x=0;x<320;x++) {
            while(!(SPI_STATUS&2u))if((uint32_t)(TICKS-start)>250)goto fail;
            SPI_DATA=c5_lcd_pixel(x,y);
        }
        service();
    }
    while(SPI_STATUS&128u)if((uint32_t)(TICKS-start)>250)goto fail;
    REG(0x40010810)=0x8000;c5_frame_presented();return 1;
fail:
    REG(0x40010810)=0x8000;return 0;
}
void reset_handler(void) {
    __asm volatile("cpsid i");REG(0xe000e010)=0;
    for(unsigned i=0;i<8;i++){REG(0xe000e180+i*4)=0xffffffffu;REG(0xe000e280+i*4)=0xffffffffu;}
    REG(0xe000ed04)=(1u<<25)|(1u<<27);REG(0xe000ed08)=0x08004000;
    REG(0xe000ed88)|=0xfu<<20; /* CP10/CP11 full access before hard-float engine */
    __asm volatile("dsb\nisb");
    uint32_t *p=_sdata;const uint32_t *q=_sidata;while(p<_edata)*p++=*q++;
    p=_sbss;while(p<_ebss)*p++=0;
    for(p=_ebss;(uintptr_t)p<0x20015000u;p++)*p=0xa55aa55au;
    uint32_t hash=2166136261u;
    for(unsigned i=0;i<0x3800;i++)hash=(hash^BYTE(0x08000000+i))*16777619u;
    if(hash!=0x966c2a7fu)fault_handler();
    REG(0x20000100)=CALL0(0x08002b14)();core_clock=REG(0x20000108);
    if(core_clock<8000000||core_clock>240000000)fault_handler();
    TICKS=0;REG(0xe000e014)=core_clock/1000-1;REG(0xe000e018)=0;REG(0xe000e010)=7;
    __asm volatile("movs r0,#0\nmsr basepri,r0\ncpsie i":::"r0","memory");
    CALL1(0x08001bcc)(120);CALL1(0x08001d4c)(0x36);CALL1(0x08001db0)(0x6000);
    rect(0,0,320,172,0);CALL1(0x08001e34)(30);lcd_ready=1;
    struct{uint16_t pins;uint8_t speed,mode;}cfg={0xc000,2,0x48};
    ((void(*)(uint32_t,const void*))0x08000f7d)(0x40010c00,&cfg);
    cfg.pins=0x6000;((void(*)(uint32_t,const void*))0x08000f7d)(0x40010800,&cfg);
    label(8,12,"C5 NATIVE DOOM 9.1",0xffff);label(8,36,"STANDALONE - LOCAL ASSETS",0x07e0);
    label(8,60,"LEFT RIGHT / OK MOVE / PA14 FIRE",0xffff);
    c5_assets_reset();c5_frame_reset();
    BYTE(0x200001ec)=0;BYTE(0x2000022c)=0;CALL0(0x08002a38)();usb_ready=1;
    c5_splash_draw();
    if(!frame_present()){lcd_ready=0;error_code=6;km_fail("BANNER TRANSFER TIMEOUT");}
    km_sleep(1200);c5_frame_reset();
    state=1;uint32_t game_start=TICKS;
    label(8,84,"LOADING FREEDOOM E1M1...",0xffe0);
    km_doom_init();rect(0,0,320,172,0);state=2;
    for(;;) {
        c5_settings_apply();
        uint32_t start=TICKS;km_doom_step();uint32_t elapsed=TICKS-start;
        if(c5_frame_dirty()) {
            start=TICKS;
            if(!frame_present()){lcd_ready=0;error_code=6;km_fail("LCD TRANSFER TIMEOUT");}
            present_ms=TICKS-start;render_ms=elapsed;frames++;
            if(frames==1)first_frame_ms=TICKS-game_start;
        }
        c5_pc_capture(frames,TICKS);service();if(stack_free()<1024){error_code=4;km_fail("STACK GUARD LOW");}
    }
}

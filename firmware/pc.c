/* SPDX-License-Identifier: GPL-2.0-or-later
 * Bounded JPEG snapshot; encoding precedes asynchronous USB download.
 */
#include "pc.h"
#include "display.h"
static uint8_t held,pressed;
static uint32_t key_tick;
static uint8_t preview[C5_PREVIEW_BYTES];
static uint32_t snapshot,snapshot_frame,image_hash,snapshot_tick;
static unsigned pending,ready;
static unsigned image_bytes,jpeg_scale=2;
static uint8_t brightness=30,flip,requested_brightness=30,requested_flip;
extern void c5_lcd_brightness(unsigned percent);
static void put32(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
void c5_pc_release(void){held=pressed=0;}
void c5_pc_keys(uint8_t mask,unsigned release_all,uint32_t now){
    if(release_all){c5_pc_release();return;}
    pressed|=mask&~held;held=mask;key_tick=now;
}
unsigned c5_pc_held_keys(uint32_t now){if((uint32_t)(now-key_tick)>500)c5_pc_release();return held|pressed;}
unsigned c5_pc_poll_keys(uint32_t now){unsigned k=c5_pc_held_keys(now);pressed=0;return k;}
void c5_pc_begin(uint32_t now){snapshot++;if(!snapshot)snapshot++;pending=1;ready=0;snapshot_tick=now;}
static void expire(uint32_t now){if((uint32_t)(now-snapshot_tick)>2000)ready=pending=0;}
void c5_pc_capture(uint32_t frame,uint32_t now){
    expire(now);if(!pending)return;
    pending=0;uint32_t id=snapshot;unsigned n=0;
    for(unsigned scale=jpeg_scale;scale<=16;scale*=2){
        n=c5_jpeg_encode(preview,sizeof(preview),scale);
        if(n){jpeg_scale=scale;break;}
    }
    if(id!=snapshot)return;
    image_bytes=n;image_hash=2166136261u;
    for(unsigned i=0;i<n;i++)image_hash=(image_hash^preview[i])*16777619u;
    snapshot_frame=frame;ready=n?1:2;
    if(n<3600 && jpeg_scale>2)jpeg_scale/=2;
}
void c5_pc_info(uint8_t *out,uint32_t now){
    expire(now);put32(out,snapshot);put32(out+4,snapshot_frame);put32(out+8,image_hash);
    out[12]=(uint8_t)image_bytes;out[13]=(uint8_t)(image_bytes>>8);
    out[14]=64;out[15]=1;out[16]=172;out[17]=0;out[18]=(uint8_t)ready;out[19]=1;
}
unsigned c5_pc_chunk(uint32_t id,unsigned offset,uint8_t *out,uint32_t now){
    expire(now);if(ready!=1||id!=snapshot||offset>=image_bytes)return 0;
    unsigned n=image_bytes-offset;if(n>28)n=28;
    for(unsigned i=0;i<n;i++)out[i]=preview[offset+i];return n;
}
int c5_settings_request(unsigned b,unsigned f){
    if(!b)return f==0;
    if(b<10||b>100||f>1)return 0;
    requested_brightness=(uint8_t)b;requested_flip=(uint8_t)f;c5_pc_release();return 1;
}
void c5_settings_apply(void){
    if(brightness!=requested_brightness){c5_lcd_brightness(requested_brightness);brightness=requested_brightness;}
    if(flip!=requested_flip){flip=requested_flip;c5_frame_redraw();}
}
unsigned c5_settings_flip(void){return flip;}
uint16_t c5_lcd_pixel(unsigned x,unsigned y){return c5_frame_pixel(flip?319-x:x,flip?171-y:y);}
void c5_settings_info(uint8_t *out){out[0]=brightness;out[1]=flip;out[2]=(brightness!=requested_brightness||flip!=requested_flip);out[3]=requested_brightness;out[4]=requested_flip;}

/* SPDX-License-Identifier: GPL-2.0-or-later
 * Compose before scanout. World columns already arrive in identical pairs in
 * the engine's low-detail mode. HUD retains all 320 columns. Message background
 * is transparent and its former dedicated band is reclaimed by the world.
 */
#include "display.h"
static uint8_t world[160*148],hud[320*24],message[160*6];
static uint16_t palette[256];
static unsigned dirty;
void c5_frame_reset(void) {
    for(unsigned i=0;i<sizeof(world);i++)world[i]=0;
    for(unsigned i=0;i<sizeof(hud);i++)hud[i]=0;
    for(unsigned i=0;i<sizeof(message);i++)message[i]=0;
    dirty=1;
}
void c5_frame_palette(const uint16_t *p) {
    for(unsigned i=0;i<256;i++)palette[i]=p[i];
    dirty=1;
}
static void pixel(unsigned x,unsigned y,uint8_t p) {
    if(y<200) {
        unsigned a=y*148/200,b=(y+1)*148/200;
        if((x&1) && b!=a)world[a*160+x/2]=p;
    } else if(y<208) {
        unsigned a=(y-200)*6/8,b=(y-199)*6/8;
        if((x&1) && b!=a)message[a*160+x/2]=p;
    } else {
        unsigned a=(y-208)*24/32,b=(y-207)*24/32;
        if(b!=a)hud[a*320+x]=p;
    }
}
int c5_frame_column(int x,int y,int h,const uint8_t *p) {
    if(x<0||x>=320||y<0||h<0||y>240||h>240-y)return 0;
    for(int i=0;i<h;i++)pixel((unsigned)x,(unsigned)(y+i),p[i]);
    if(h)dirty=1;
    return 1;
}
int c5_frame_rgb_column(int x,int y,int h,const uint16_t *p) {
    if(x<0||x>=320||y<0||h<0||y>240||h>240-y)return 0;
    for(int i=0;i<h;i++) {
        unsigned k=0;
        for(;k<256;k++)if(palette[k]==p[i])break;
        /* Engine fills are palette colors; never silently approximate them. */
        if(k==256)return 0;
        pixel((unsigned)x,(unsigned)(y+i),(uint8_t)k);
    }
    if(h)dirty=1;
    return 1;
}
uint8_t c5_frame_index(unsigned x,unsigned y) {
    if(x>=320||y>=172)return 0;
    uint8_t c;
    if(y>=148)c=hud[(y-148)*320+x];
    else {
        c=world[y*160+x/2];
        if(y>=142) {uint8_t m=message[(y-142)*160+x/2];if(m)c=m;}
    }
    return c;
}
int c5_frame_dirty(void){return (int)dirty;}
void c5_frame_redraw(void){dirty=1;}
void c5_frame_presented(void){dirty=0;}

uint16_t c5_frame_pixel(unsigned x,unsigned y){return palette[c5_frame_index(x,y)];}
uint32_t c5_palette_hash(void){uint32_t h=2166136261u;for(unsigned i=0;i<256;i++){h=(h^(palette[i]&255))*16777619u;h=(h^(palette[i]>>8))*16777619u;}return h;}
void c5_boot_pixel(unsigned x,unsigned y,uint8_t c){if(x>=320||y>=172)return;if(y<148)world[y*160+x/2]=c;else hud[(y-148)*320+x]=c;dirty=1;}

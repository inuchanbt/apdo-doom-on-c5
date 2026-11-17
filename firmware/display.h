/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
void c5_frame_redraw(void);
void c5_frame_reset(void);
void c5_frame_palette(const uint16_t *p);
int c5_frame_column(int x,int y,int h,const uint8_t *p);
int c5_frame_rgb_column(int x,int y,int h,const uint16_t *p);
uint16_t c5_frame_pixel(unsigned x,unsigned y);
int c5_frame_dirty(void);
void c5_frame_presented(void);

uint8_t c5_frame_index(unsigned x,unsigned y);
uint32_t c5_palette_hash(void);
void c5_boot_pixel(unsigned x,unsigned y,uint8_t c);

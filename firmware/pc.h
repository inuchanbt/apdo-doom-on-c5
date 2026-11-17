/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
#define C5_PREVIEW_WIDTH 320u
#define C5_PREVIEW_HEIGHT 172u
#define C5_PREVIEW_BYTES 7168u
void c5_pc_keys(uint8_t mask,unsigned release_all,uint32_t now);
unsigned c5_pc_poll_keys(uint32_t now);
unsigned c5_pc_held_keys(uint32_t now);
void c5_pc_release(void);
void c5_pc_begin(uint32_t now);
void c5_pc_capture(uint32_t frame,uint32_t now);
void c5_pc_info(uint8_t *out,uint32_t now);
unsigned c5_pc_chunk(uint32_t id,unsigned offset,uint8_t *out,uint32_t now);
void c5_splash_draw(void);
unsigned c5_jpeg_encode(uint8_t *dst,unsigned capacity,unsigned scale);
int c5_settings_request(unsigned brightness,unsigned flip);
void c5_settings_apply(void);
void c5_settings_info(uint8_t *out);
unsigned c5_settings_flip(void);
uint16_t c5_lcd_pixel(unsigned x,unsigned y);

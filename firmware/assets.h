/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdint.h>
int c5_lz_decode(const uint8_t *src,unsigned size,uint8_t *dst,unsigned count);
int c5_assets_read(uint32_t at,void *dst,uint32_t count);
void c5_assets_reset(void);
uint32_t c5_assets_decodes(void);
void c5_asset_yield(void);

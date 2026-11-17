/* SPDX-License-Identifier: GPL-2.0-or-later
 * Projection derived from DOOM, Copyright (C) 1993-1996 Id Software, Inc.
 * C5 output scales x by 1, y by 148/200=37/50. Compensate world projection.
 * Existing engine hook names retain the KWS ABI; UI initially fills LCD width.
 */
#include <stdint.h>
#include "doomdef.h"
#include "m_fixed.h"
#include "trig.h"
uint16_t kws_wide_xtva[321];
static int wide_width;
static int raw_column(unsigned angle) {
    int32_t tangent=dmc_finetangent(angle);
    int32_t center=(wide_width/2)<<16,focal=center/50*37;
    if(tangent>131072)return -1;
    if(tangent< -131072)return wide_width+1;
    return (center-FixedMul(tangent,focal)+65535)>>16;
}
void kws_wide_projection(int width) {
    wide_width=width;unsigned angle=0;
    for(int x=width;x>=0;x--){while(angle<4095 && raw_column(angle)>x)angle++;kws_wide_xtva[x]=angle;}
}
int kws_wide_angle_to_x(unsigned angle) {
    int x=raw_column(angle);return x<0?0:x>wide_width?wide_width:x;
}

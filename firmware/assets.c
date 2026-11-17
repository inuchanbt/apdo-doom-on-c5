/* SPDX-License-Identifier: GPL-2.0-or-later
 * Entire logical game pack is stored in read-only Flash, in independent blocks.
 * No allocator, USB dependency or runtime Flash writes.
 */
#include "assets.h"
#include "asset_meta.h"
extern const uint8_t c5_asset_blob[];
extern const uint32_t c5_asset_offsets[];
static uint8_t cache[1][1024];
static uint32_t tags[1],replace_slot,decodes;
int c5_lz_decode(const uint8_t *src,unsigned size,uint8_t *dst,unsigned count) {
    unsigned pos=0,out=0;
    while(out<count) {
        if(pos==size)return 0;
        unsigned flags=src[pos++];
        for(unsigned bit=0;bit<8 && out<count;bit++) {
            if(flags&(1u<<bit)) {
                if(pos==size)return 0;
                dst[out++]=src[pos++];
            } else {
                if(size-pos<2)return 0;
                unsigned code=src[pos]|((unsigned)src[pos+1]<<8);pos+=2;
                unsigned distance=(code>>4)+1,n=(code&15)+3;
                if(distance>out || n>count-out)return 0;
                while(n--){dst[out]=dst[out-distance];out++;}
            }
        }
    }
    return pos==size;
}
void c5_assets_reset(void) {
    for(unsigned i=0;i<1;i++)tags[i]=0xffffffffu;
    replace_slot=decodes=0;
}
uint32_t c5_assets_decodes(void){return decodes;}
int c5_assets_read(uint32_t at,void *dst,uint32_t count) {
    if(at>C5_PACK_BYTES || count>C5_PACK_BYTES-at)return 0;
    uint8_t *out=dst;
    while(count) {
        uint32_t page=at/1024,off=at%1024;unsigned slot;
        uint32_t entry=c5_asset_offsets[page];
        if(entry&0x80000000u) {
            unsigned n=1024-off;if(n>count)n=count;
            uint32_t start=entry&0x7fffffffu,end=c5_asset_offsets[page+1]&0x7fffffffu;
            unsigned page_bytes=C5_PACK_BYTES-page*1024;if(page_bytes>1024)page_bytes=1024;
            if(end<start || end>C5_BLOB_BYTES || end-start!=page_bytes)return 0;
            for(unsigned j=0;j<n;j++)out[j]=c5_asset_blob[start+off+j];
            at+=n;out+=n;count-=n;c5_asset_yield();continue;
        }
        for(slot=0;slot<1;slot++)if(tags[slot]==page)break;
        if(slot==1) {
            slot=replace_slot++%1;tags[slot]=0xffffffffu;
            unsigned n=C5_PACK_BYTES-page*1024;if(n>1024)n=1024;
            uint32_t a=c5_asset_offsets[page],b=c5_asset_offsets[page+1]&0x7fffffffu;
            uint32_t start=a&0x7fffffffu;
            if(start>b || b>C5_BLOB_BYTES)return 0;
            if(a&0x80000000u) {
                if(b-start!=n)return 0;
                for(unsigned j=0;j<n;j++)cache[slot][j]=c5_asset_blob[start+j];
            } else if(!c5_lz_decode(c5_asset_blob+start,b-start,cache[slot],n))return 0;
            tags[slot]=page;decodes++;
        }
        unsigned n=1024-off;if(n>count)n=count;
        for(unsigned j=0;j<n;j++)out[j]=cache[slot][off+j];
        at+=n;out+=n;count-=n;c5_asset_yield();
    }
    return 1;
}

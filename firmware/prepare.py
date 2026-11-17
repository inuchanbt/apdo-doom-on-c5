"""Create an immutable, complete E1M1 resource image; no USB access."""
from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'tools'))
from codec import encode,decode
def main():
    game=(HERE/'DOOM.DAT').read_bytes()
    assert len(game)==1056192
    assert hashlib.sha256(game).hexdigest()=='8e020d3822edf873b0209c92dfbb6518bb8a92c6fe9fdb64be17d66699ae2664'
    blocks=[game[i:i+1024] for i in range(0,len(game),1024)]
    encoded=[encode(b) for b in blocks]
    raw_pages={i for i,(a,b) in enumerate(zip(blocks,encoded)) if len(b)>=len(a)}
    refs=json.loads((HERE/'asset-trace.json').read_text())
    def simulate(raw,slots):
        from collections import Counter
        cache=[];pos=0;counts=Counter()
        for page in refs:
            if page in raw:continue
            if page not in cache:
                counts[page]+=1
                if len(cache)<slots:cache.append(page)
                else:cache[pos]=page;pos=(pos+1)%slots
        return counts
    before=sum(simulate(raw_pages,1).values());extra=0;selected=[]
    # Recompute misses in small batches because raw bypass also avoids eviction.
    while True:
        counts=simulate(raw_pages,1)
        candidates=sorted((i for i in counts if i not in raw_pages),key=lambda i:counts[i]/(len(blocks[i])-len(encoded[i])),reverse=True)
        added=0
        for i in candidates:
            cost=len(blocks[i])-len(encoded[i])
            if extra+cost<=40000:
                raw_pages.add(i);selected.append(i);extra+=cost;added+=1
                if added==8:break
        if not added:break
    after=sum(simulate(raw_pages,1).values())
    blob=bytearray();offsets=[]
    for i in range(0,len(game),1024):
        raw=game[i:i+1024];packed=encode(raw);assert decode(packed,len(raw))==raw
        use_raw=i//1024 in raw_pages
        offsets.append(len(blob)|(0x80000000 if use_raw else 0));blob+=raw if use_raw else packed
    offsets.append(len(blob))
    lines=['/* Generated from the complete Freedoom E1M1 half-art pack. */','#include <stdint.h>',
           'const uint8_t c5_asset_blob[] = {']
    lines+= [','.join(str(v) for v in blob[i:i+32])+',' for i in range(0,len(blob),32)]
    lines+=['};','const uint32_t c5_asset_offsets[] = {',','.join(hex(v)+'u' for v in offsets),'};']
    (HERE/'asset_data.c').write_text('\n'.join(lines)+'\n')
    (HERE/'asset_meta.h').write_text(f'#define C5_PACK_BYTES {len(game)}u\n#define C5_BLOB_BYTES {len(blob)}u\n')
    (HERE/'DOOM.DAT').write_bytes(game)
    report=dict(pack_bytes=len(game),pack_sha256=hashlib.sha256(game).hexdigest(),blob_bytes=len(blob),
                offset_bytes=4*len(offsets),stored_bytes=len(blob)+4*len(offsets),pages=len(offsets)-1,
                all_blocks_roundtrip=True,hardware_tested=False,raw_hot_pages=selected,extra_raw_bytes=extra,trace_lz_misses_before=before,trace_lz_misses_after=after)
    (HERE/'assets.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

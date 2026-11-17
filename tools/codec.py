"""Independent 1 KiB LZSS blocks: flag 1=literal, 0=12-bit distance/4-bit length."""
from collections import defaultdict
def encode(b):
    out=bytearray();positions=defaultdict(list);i=0
    while i<len(b):
        flag_at=len(out);out.append(0)
        for bit in range(8):
            if i==len(b):break
            best=0;distance=0
            for j in reversed(positions[b[i:i+3]][-128:]):
                if i-j>4096:break
                n=0
                while n<18 and i+n<len(b) and b[j+n]==b[i+n]:n+=1
                if n>best:best=n;distance=i-j
                if best==18:break
            if best>=3:
                code=((distance-1)<<4)|(best-3);out+=code.to_bytes(2,'little');n=best
            else:
                out[flag_at]|=1<<bit;out.append(b[i]);n=1
            for j in range(i,i+n):positions[b[j:j+3]].append(j)
            i+=n
    return bytes(out)
def decode(b,n):
    out=bytearray();i=0
    while len(out)<n:
        flags=b[i];i+=1
        for bit in range(8):
            if len(out)==n:break
            if flags&(1<<bit):out.append(b[i]);i+=1
            else:
                code=int.from_bytes(b[i:i+2],'little');i+=2
                distance=(code>>4)+1;count=(code&15)+3
                assert distance<=len(out) and len(out)+count<=n
                for _ in range(count):out.append(out[-distance])
    assert i==len(b)
    return bytes(out)
if __name__=='__main__':
    from pathlib import Path
    for name in ('half_walls','half_art','half_monsters'):
        b=(Path(__file__).parent/name/'DOOM.DAT').read_bytes();total=0
        for i in range(0,len(b),1024):
            block=b[i:i+1024];c=encode(block);assert decode(c,len(block))==block
            total+=min(len(c),len(block))
        print(name,total+4*((len(b)+1023)//1024+1),flush=True)

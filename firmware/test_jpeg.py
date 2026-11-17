"""Real engine scenes and bounded JPEG output; no USB or physical timing."""
import ctypes as C
import io,json,random,struct
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent

def main():
    d=C.CDLL(str(HERE/'host-build/c5-engine-test.dll'))
    d.km_host_error.restype=C.c_char_p
    game=(HERE/'DOOM.DAT').read_bytes();buf=(C.c_uint8*len(game)).from_buffer_copy(game)
    assert d.km_host_init(buf,len(game))==0,d.km_host_error()
    info=(C.c_uint8*36)();chunk=(C.c_uint8*28)();sizes=[]
    keys=[0]*40+[8]*40+[2]*100+[3]*100+[4]*40+[2]*100+[16]*12+[1]*80+[32,0,64,0]
    for frame,key in enumerate(keys):
        assert d.km_host_step(key)==0,d.km_host_error()
        if frame%4:continue
        now=1000+frame*100
        d.c5_test_begin(now);d.c5_test_capture(frame,now);d.c5_test_info(info,now)
        sid,f,digest,total,w,h,ready,fmt=struct.unpack_from('<IIIHHHBB',bytes(info))
        assert (f,w,h,ready,fmt)==(frame,320,172,1,1),(frame,total,ready)
        result=bytearray()
        for at in range(0,total,28):
            n=d.c5_test_chunk(sid,at,chunk,now);result+=bytes(chunk[:n])
        picture=Image.open(io.BytesIO(result));picture.load();assert picture.size==(320,172)
        sizes.append(total)
    # A tiny output must fail without writing through either boundary.
    sentinel=(C.c_uint8*48)(*([0xa5]*48))
    assert d.c5_test_jpeg(C.byref(sentinel,16),16,2)==0
    assert bytes(sentinel[:16])==b'\xa5'*16 and bytes(sentinel[32:])==b'\xa5'*16
    # Deliberately incompressible indexed frame exercises quality fallback.
    rng=random.Random(10);palette=(C.c_uint16*256)(*[rng.randrange(65536) for _ in range(256)])
    d.c5_test_palette(palette)
    for x in range(320):
        col=(C.c_uint8*200)(*[rng.randrange(256) for _ in range(200)])
        assert d.c5_test_column(x,0,200,col)
    d.c5_test_begin(90000);d.c5_test_capture(999,90000);d.c5_test_info(info,90000)
    assert info[18] in (1,2) # Bounded explicit failure is also valid for pathological noise.
    report=dict(real_engine_jpegs=len(sizes),min_bytes=min(sizes),max_bytes=max(sizes),
                all_decode_320x172=True,tiny_buffer_canaries=True,noise_ready=int(info[18]),hardware_tested=False)
    (HERE/'host-build/jpeg-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()

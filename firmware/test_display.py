"""Gap coverage, message overlay, full HUD width and real-engine composition."""
import ctypes as C,json
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
def main():
    d=C.CDLL(str(HERE/'host-build/c5-engine-test.dll'))
    d.c5_test_pixel.restype=C.c_uint16;d.km_host_error.restype=C.c_char_p
    d.km_host_screen.restype=C.POINTER(C.c_uint16)
    palette=(C.c_uint16*256)(*range(256));d.c5_test_palette(palette);d.c5_test_reset()
    world=(C.c_uint8*200)(*[17]*200);hud=(C.c_uint8*32)(*[31]*32);msg=(C.c_uint8*8)()
    for x in range(320):
        assert d.c5_test_column(x,0,200,world)
        assert d.c5_test_column(x,208,32,hud)
        assert d.c5_test_column(x,200,8,msg)
    assert all(d.c5_test_pixel(x,y)==(17 if y<148 else 31) for y in range(172) for x in range(320))
    msg[7]=90;d.c5_test_column(1,200,8,msg)
    assert d.c5_test_pixel(0,147)==90 and d.c5_test_pixel(1,147)==90 and d.c5_test_pixel(2,147)==17
    msg[7]=0;d.c5_test_column(1,200,8,msg);assert d.c5_test_pixel(0,147)==17
    for x in range(320):
        val=(C.c_uint8*32)(*[x%256]*32);d.c5_test_column(x,208,32,val)
    assert all(d.c5_test_pixel(x,171)==x%256 for x in range(320))
    assert not d.c5_test_column(320,0,1,msg)
    assert not d.c5_test_column(0,239,2,msg)
    assert not d.c5_test_column(-1,0,1,msg)
    assert d.c5_test_dirty();d.c5_test_presented();assert not d.c5_test_dirty()
    # Capture source palette indices independently from the production compositor.
    logical=bytearray(320*240);pal=[0]*256
    COL=C.CFUNCTYPE(None,C.c_int,C.c_int,C.c_int,C.POINTER(C.c_uint8),C.c_uint)
    PAL=C.CFUNCTYPE(None,C.POINTER(C.c_uint16))
    @COL
    def column(x,y,h,p,ui):
        for i in range(h):logical[(y+i)*320+x]=p[i]
    @PAL
    def colors(p):pal[:]=p[:256]
    d.km_host_display_callbacks(column,colors)
    pack=(HERE/'DOOM.DAT').read_bytes();buf=(C.c_uint8*len(pack)).from_buffer_copy(pack)
    assert d.km_host_init(buf,len(pack))==0,d.km_host_error()
    actual=(C.c_uint16*(320*172))();checked=0
    for i,k in enumerate([0]*8+[8]*20+[2]*30+[3]*30+[4]*20+[16]*4+[0]*8+[32]+[0]*8+[32]+[0]*8):
        assert d.km_host_step(k)==0,(i,d.km_host_error())
        d.c5_test_copy_frame(actual)
        # Logical column stream uses identical pairs for the 3D view; HUD full width.
        expected=[]
        for y in range(172):
            for x in range(320):
                if y<148:
                    sy=((y+1)*200+147)//148-1;sx=(x//2)*2+1
                    index=logical[sy*320+sx]
                    if y>=142:
                        my=200+((y-141)*8+5)//6-1;m=logical[my*320+sx]
                        if m:index=m
                else:
                    sy=208+((y-147)*32+23)//24-1;index=logical[sy*320+x]
                expected.append(pal[index])
        assert list(actual)==expected,('compositor mismatch',i)
        checked+=1
        if i in (0,7,57,87,120):
            rgb=bytes(c for v in actual for c in (((v>>11)&31)*255//31,((v>>5)&63)*255//63,(v&31)*255//31))
            Image.frombytes('RGB',(320,172),rgb).save(HERE/f'host-build/frame-{i:03}.png')
        d.c5_test_presented()
    result=dict(gap_free_rows=172,hud_columns_preserved=320,message_transparency=True,
                dirty_tracking=True,real_engine_frames_compared=checked,physical_spi_tested=False)
    (HERE/'host-build/display-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()

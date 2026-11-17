"""PC input leases, coherent snapshots, original banner and host protocol tests."""
import ctypes as C,struct,json,hashlib
from pathlib import Path
from PIL import Image
import controller,monitor
HERE=Path(__file__).resolve().parent
def save_image(pixels,path):
    rgb=bytes(v for c in pixels for v in (((c>>11)&31)*255//31,((c>>5)&63)*255//63,(c&31)*255//31))
    Image.frombytes('RGB',(320,172),rgb).save(path)
def main():
    d=C.CDLL(str(HERE/'host-build/c5-engine-test.dll'));d.km_host_error.restype=C.c_char_p
    d.c5_test_pixel.restype=C.c_uint16
    # A quick press+release survives until one real input poll, then releases.
    d.c5_test_keys(0,1,0);d.c5_test_keys(3,0,100);d.c5_test_keys(0,0,110)
    assert d.c5_test_poll(120)==3 and d.c5_test_poll(121)==0
    d.c5_test_keys(255,0,200);assert d.c5_test_poll(700)==255 and d.c5_test_poll(701)==0
    d.c5_test_keys(1,0,0xfffffff0);assert d.c5_test_poll(20)==1 and d.c5_test_poll(600)==0
    d.c5_test_keys(255,0,800);d.c5_test_keys(0,1,801);assert d.c5_test_poll(802)==0
    # Capture original banner pixels through the same hardware frame composer.
    banner=(HERE/'freedoom-banner.bin').read_bytes();meta=json.loads((HERE/'freedoom-banner.json').read_text())
    assert hashlib.sha256(banner).hexdigest()==meta['sha256']
    d.c5_test_banner();screen=(C.c_uint16*(320*172))();d.c5_test_copy_frame(screen)
    for y in range(172):
        for x in range(320):
            c=0
            if 16<=x<304 and 52<=y<119:
                sx=((x-16)//2*2+1)*159//288;sy=(y-52)*37//67
                index=banner[138+sy*159+sx];c=struct.unpack_from('<H',banner,6+index*2)[0]
            assert screen[y*320+x]==c,(x,y)
    save_image(screen,HERE/'host-build/banner.png')
    # Real game snapshot; metadata/palette correspond to the captured completed image.
    game=(HERE/'DOOM.DAT').read_bytes();buf=(C.c_uint8*len(game)).from_buffer_copy(game)
    assert d.km_host_init(buf,len(game))==0,d.km_host_error();assert d.km_host_step(0)==0
    d.c5_test_copy_frame(screen);d.c5_test_begin(1000);info=(C.c_uint8*36)();d.c5_test_info(info,1000);assert info[18]==0
    d.c5_test_capture(42,1001);d.c5_test_info(info,1001)
    sid,frame,digest,total,w,h,ready,fmt=struct.unpack_from('<IIIHHHBB',bytes(info))
    assert (frame,w,h,ready,fmt)==(42,320,172,1,1) and 100<total<=7168
    chunk=(C.c_uint8*28)();result=bytearray()
    for at in range(0,total,28):
        n=d.c5_test_chunk(sid,at,chunk,1100);assert n==min(28,total-at);result+=bytes(chunk[:n])
    assert controller.fnv(result)==digest
    import io
    picture=Image.open(io.BytesIO(result));picture.load();assert picture.size==(320,172)
    (HERE/'host-build/preview.jpg').write_bytes(result)
    save_image(screen,HERE/'host-build/source-frame.png')
    # Game continues after capture; saved JPEG remains immutable.
    for _ in range(8):assert d.km_host_step(8)==0
    again=bytearray()
    for at in range(0,total,28):
        n=d.c5_test_chunk(sid,at,chunk,1100);again+=bytes(chunk[:n])
    assert again==result
    assert d.c5_test_chunk(sid+1,0,chunk,1100)==0
    assert d.c5_test_chunk(sid,total,chunk,1100)==0
    assert d.c5_test_chunk(sid,0,chunk,3001)==0
    # Actual scanout accessor implements a rotation, not a mirror or crop.
    d.c5_test_copy_frame(screen);d.c5_test_lcd_pixel.restype=C.c_uint16
    settings=(C.c_uint8*5)();d.c5_test_settings_info(settings);assert list(settings)==[30,0,0,30,0]
    for b,f in ((9,0),(101,0),(50,2),(0,1)):assert d.c5_test_settings(b,f)==0
    assert d.c5_test_settings(75,1)==1;d.c5_test_settings_info(settings);assert list(settings)==[30,0,1,75,1]
    d.c5_test_apply();d.c5_test_settings_info(settings);assert list(settings)==[75,1,0,75,1]
    for y in range(172):
        for x in range(320):assert d.c5_test_lcd_pixel(x,y)==screen[(171-y)*320+319-x]
    assert d.c5_test_settings(30,0)==1;d.c5_test_apply()
    # Exercise actual host request serialization and nonce/checksum validation.
    class Device:
        corrupt=False
        def write(self,b):
            assert len(b)==65 and b[0]==0;self.req=b[1:];return 65
        def read(self,n,timeout):
            r=self.req;assert r[62]==sum(r[8:62])&255 and r[63]==sum(r[:62])&255
            p=bytearray(52);p[:16]=r[10:26]
            if r[8]==0x9a:
                struct.pack_into('<IIIHHHBB',p,16,7,42,digest,total,320,172,1,1);cmd=0x9b
            elif r[8]==0x9c:
                ident,at=struct.unpack_from('<IH',r,26);count=min(28,total-at);struct.pack_into('<IHBB',p,16,ident,at,count,0);p[24:24+count]=result[at:at+count];cmd=0x9d
            else:
                struct.pack_into('<BBHIIIIHHIII',p,16,2,0,0,1000,42,3,165,39,37,10,192000000,1300);cmd=0x91
            b=bytearray(64);b[:2]=b'\xff\x55';b[8:10]=bytes([cmd,52]);b[10:62]=p;b[62]=sum(b[8:62])&255;b[63]=sum(b[:62])&255
            if self.corrupt:b[18]^=1
            return b
    dev=Device();client=controller.Client(dev)
    assert client.exchange(0x98,b'\3\0')['pc_keys']==3
    assert client.exchange(0x9a,b'\0')['snapshot']==7
    assert client.exchange(0x9c,struct.pack('<IH',7,0))==result[:28]
    dev.corrupt=True
    try:client.exchange(0x9a,b'\1')
    except ValueError:pass
    else:raise AssertionError('Corrupt preview accepted')
    report=dict(input_tap_latch=True,input_release=True,input_timeout_and_tick_wrap=True,
                banner_matches_original=True,jpeg_dimensions=[320,172],jpeg_bytes=total,jpeg_integrity=True,rotation_all_pixels=True,brightness_bounds_and_ack=True,preview_survives_rendering=True,
                preview_expiry_and_bounds=True,host_packet_checks=True,hardware_tested=False)
    (HERE/'host-build/pc-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

"""Exhaustive local asset reads, malformed decoder input, real-engine comparisons."""
import ctypes as C
import json,random,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'tools'))
from codec import encode
def main():
    game=(HERE/'DOOM.DAT').read_bytes();buf=(C.c_uint8*len(game)).from_buffer_copy(game)
    new=C.CDLL(str(HERE/'host-build/c5-engine-test.dll'))
    ref=C.CDLL(str(HERE/'host-reference/c5-engine-test.dll'))
    for d in (new,ref):
        d.km_host_error.restype=C.c_char_p
        d.km_host_screen.restype=C.POINTER(C.c_uint16)
        assert d.km_host_init(buf,len(game))==0,d.km_host_error()
    out=(C.c_uint8*len(game))()
    assert new.c5_test_read(0,out,len(game))==1 and bytes(out)==game
    rng=random.Random(601116)
    for _ in range(3000):
        at=rng.randrange(len(game));n=min(rng.randrange(1,3000),len(game)-at)
        assert new.c5_test_read(at,out,n)==1 and bytes(out[:n])==game[at:at+n]
    assert not new.c5_test_read(len(game),out,1)
    assert not new.c5_test_read(0xffffffff,out,2)
    assert new.c5_test_read(len(game),out,0)
    # Valid blocks include overlap backreferences, incompressible data and final short pages.
    count=0
    for raw in [b'A'*1024,bytes(range(256))*4,b'abc'*341,b'X',b'',rng.randbytes(1024)]+[game[i:i+1024] for i in range(0,len(game),1024)]:
        packed=encode(raw);src=(C.c_uint8*len(packed)).from_buffer_copy(packed)
        assert new.c5_test_decode(src,len(packed),out,len(raw))==1
        assert bytes(out[:len(raw)])==raw
        if packed:assert not new.c5_test_decode(src,len(packed)-1,out,len(raw))
        count+=1
    for bad,size in [(b'\0\0\0',3),(b'\0\xff\xff',18),(b'\1A\0\0',1)]:
        src=(C.c_uint8*len(bad)).from_buffer_copy(bad)
        assert not new.c5_test_decode(src,len(bad),out,size)
    keys=[0]*40+[8]*40+[2]*100+[3]*100+[4]*40+[2]*100+[16]*12+[1]*80
    frame_hashes=[]
    import hashlib
    for i,k in enumerate(keys):
        for d in (new,ref):assert d.km_host_step(k)==0,(i,d.km_host_error())
        a=C.string_at(new.km_host_screen(),320*240*2)
        assert a==C.string_at(ref.km_host_screen(),320*240*2),i
        for name in ('km_host_player_x','km_host_player_y','km_host_player_angle','km_host_player_health','km_host_player_ammo','km_host_player_kills'):
            assert getattr(new,name)()==getattr(ref,name)(),(i,name)
        if i in (0,39,79,179,279,319,419,511):frame_hashes.append([i,hashlib.sha256(a).hexdigest()])
    result=dict(full_pack_byte_exact=True,random_reads=3000,decoder_vectors=count,
                truncated_inputs_rejected=True,frames_identical=len(keys),frame_hashes=frame_hashes,
                comparison='Compressed vs raw same reduced-art pack; real engine, PC execution',hardware_fps_measured=False)
    (HERE/'host-build/local-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()

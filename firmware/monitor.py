"""Optional read-only monitor for standalone C5 v9. No asset transfers or start commands."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import secrets
import struct
import time

MAGIC=b'C5D9'
STATES=('WAIT','LOAD','PLAY','ERROR')

def frame(command,payload):
    if command not in (0x90,0x96) or len(payload)!=16:
        raise ValueError('Only bounded application commands are supported')
    b=bytearray(64);b[:2]=b'\xff\x55';b[4]=128
    b[8]=command;b[9]=len(payload);b[10:10+len(payload)]=payload
    b[62]=sum(b[8:62])&255;b[63]=sum(b[:62])&255
    return bytes(b)

def parse(raw,seq,nonce,expected=0x91):
    if len(raw)==65 and raw[0]==0:raw=raw[1:]
    if len(raw)!=64 or raw[:2]!=b'\xff\x55':raise ValueError('Bad HID frame')
    if raw[62]!=sum(raw[8:62])&255 or raw[63]!=sum(raw[:62])&255:raise ValueError('Checksum mismatch')
    if raw[8:10]!=bytes([expected,52]):raise ValueError('Not native C5 DOOM v9')
    p=raw[10:62]
    if p[:16]!=MAGIC+struct.pack('<I',seq)+nonce:raise ValueError('Stale sequence/session response')
    if expected==0x97:return {'error_text':p[16:].split(b'\0')[0].decode('ascii','replace')}
    state,keys,error,uptime,frames,token,base,filled,need,misses,clock,guard=struct.unpack_from('<BBHIIIIHHIII',p,16)
    if state>3 or keys>15:raise ValueError('Invalid status fields')
    if token>255:raise ValueError('Invalid PC input mask')
    return dict(state=STATES[state],keys=keys,error=error,uptime_ms=uptime,frames=frames,
                pc_keys=token,render_ms=filled,present_ms=need,first_frame_ms=base,local_page_decodes=misses,core_clock_hz=clock,unused_guard_bytes=guard)

class Client:
    def __init__(self,device):
        self.device=device;self.nonce=secrets.token_bytes(8);self.seq=0;self.requests=0
    def exchange(self,command=0x90,extra=b''):
        seq=self.seq;self.seq+=1
        tx=frame(command,MAGIC+struct.pack('<I',seq)+self.nonce+extra)
        if self.device.write(b'\0'+tx)!=65:raise IOError('Incomplete HID write')
        self.requests+=1
        raw=bytes(self.device.read(65,10000))
        if not raw:raise TimeoutError('No application response. No retry. Check C5 screen, cable and mode.')
        return parse(raw,seq,self.nonce,0x97 if command==0x96 else 0x91)

def run(output,seconds):
    import hid
    report={'schema':'c5-native-doom-v9-session','utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'all_resources_local':True,'device_programming_commands_implemented':False,'status':'starting'}
    device=None;client=None;started=time.monotonic();sent=0;first_frame=None;status=None
    log_path=output.with_suffix('.jsonl')
    with log_path.open('x',encoding='utf8') as log:
        try:
            candidates=hid.enumerate(0x0716,0x5053)
            if len(candidates)!=1 or candidates[0].get('serial_number')!='20211222':
                raise RuntimeError('Expected exactly the previously verified owner C5')
            device=hid.device();device.open_path(candidates[0]['path']);device.set_nonblocking(True)
            for _ in range(16):
                if not device.read(65):break
            else:raise RuntimeError('Continuous traffic: close other HID clients')
            device.set_nonblocking(False);client=Client(device)
            status=client.exchange()
            report['initial']=status
            print(f"[OK] Native C5 nonce handshake; core {status['core_clock_hz']/1e6:g} MHz.",flush=True)
            print('[MONITOR] Standalone game is already running. Ctrl+C stops monitoring only.',flush=True)
            last_print=time.monotonic();last_frames=status['frames'];last_print_time=last_print
            while not seconds or time.monotonic()-started<seconds:
                now=time.monotonic()
                if status['state']=='ERROR':
                    message=client.exchange(0x96)['error_text']
                    raise RuntimeError(f"C5 error {status['error']}: {message}")
                if status['frames'] and first_frame is None:
                    first_frame=status['first_frame_ms']/1000
                    print(f'[BOOT FIRST FRAME] {first_frame:.3f}s from game initialization.',flush=True)
                if now-last_print>=1:
                    elapsed=now-started;fps=(status['frames']-last_frames)/max(now-last_print_time,0.001)
                    sample={'elapsed_s':round(elapsed,3),'served_bytes':sent,'fps_interval':round(fps,3),**status}
                    log.write(json.dumps(sample)+'\n');log.flush()
                    print(f"[{status['state']}] {elapsed:.0f}s frames={status['frames']} fps={fps:.2f} "
                          f"render={status['render_ms']}ms lcd={status['present_ms']}ms local_decodes={status['local_page_decodes']} USB_data=0 keys=0x{status['keys']:x}",flush=True)
                    last_print=now;last_frames=status['frames'];last_print_time=now
                time.sleep(0.05)
                status=client.exchange()
            report['status']='duration_complete'
        except KeyboardInterrupt:
            report['status']='stopped_by_user';print('\n[STOP] Monitoring stopped; game continues.',flush=True)
        except Exception as e:
            report['status']='failed';report['error']=f'{type(e).__name__}: {e}';print('[STOP] '+report['error'],flush=True)
        finally:
            if device is not None:device.close()
            report.update(elapsed_s=round(time.monotonic()-started,3),served_bytes=sent,
                          requests=client.requests if client else 0,first_frame_seconds=first_frame,last_status=status)
            output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
            print('Result:',output,flush=True)
    return 2 if report['status']=='failed' else 0

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=0,help='0: monitor until Ctrl+C')
    a=p.parse_args()
    if a.seconds<0:p.error('seconds must be nonnegative')
    if a.output.exists() or a.output.with_suffix('.jsonl').exists():p.error('Use a fresh output filename')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    return run(a.output,a.seconds)
if __name__=='__main__':raise SystemExit(main())

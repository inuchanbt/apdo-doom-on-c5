"""Loopback browser controls and coherent full-panel C5 JPEG snapshots. No flashing."""
from collections import deque
import argparse,json,secrets,struct,threading,time,webbrowser
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import monitor
HERE=Path(__file__).resolve().parent
def fnv(b):
    h=2166136261
    for v in b:h=((h^v)*16777619)&0xffffffff
    return h
class Client:
    def __init__(self,device):self.device=device;self.seq=0;self.nonce=secrets.token_bytes(8)
    def exchange(self,command=0x90,extra=b''):
        sizes={0x90:0,0x96:0,0x98:2,0x9a:1,0x9c:6,0x9e:2}
        if command not in sizes or len(extra)!=sizes[command]:raise ValueError('Unsupported command')
        seq=self.seq;self.seq+=1
        payload=monitor.MAGIC+struct.pack('<I',seq)+self.nonce+extra
        frame=bytearray(64);frame[:2]=b'\xff\x55';frame[4]=128;frame[8]=command;frame[9]=len(payload);frame[10:10+len(payload)]=payload
        frame[62]=sum(frame[8:62])&255;frame[63]=sum(frame[:62])&255
        if self.device.write(b'\0'+frame)!=65:raise IOError('Incomplete HID write')
        raw=bytes(self.device.read(65,1500))
        if len(raw)==65 and raw[0]==0:raw=raw[1:]
        if command in (0x90,0x96,0x98):return monitor.parse(raw,seq,self.nonce,0x97 if command==0x96 else 0x91)
        expected={0x9a:0x9b,0x9c:0x9d,0x9e:0x9f}[command]
        if len(raw)!=64 or raw[:2]!=b'\xff\x55' or raw[8:10]!=bytes([expected,52]):raise ValueError('Not C5 v9 preview transport')
        if raw[62]!=(sum(raw[8:62])&255) or raw[63]!=(sum(raw[:62])&255):raise ValueError('Preview checksum mismatch')
        if raw[10:26]!=payload[:16]:raise ValueError('Stale preview nonce/sequence')
        p=raw[26:62]
        if command==0x9e:
            b,f,pending,desired_b,desired_f=p[:5]
            if not 10<=b<=100 or f>1 or pending>1 or not 10<=desired_b<=100 or desired_f>1:raise ValueError('Invalid display settings reply')
            return dict(brightness=b,flip=bool(f),pending=bool(pending))
        if command==0x9a:
            snap,game_frame,digest,total,w,h,ready,fmt=struct.unpack_from('<IIIHHHBB',p)
            if not snap or (w,h,fmt)!=(320,172,1) or ready>2 or total>7168:raise ValueError('Invalid snapshot metadata')
            if ready==2:raise ValueError('JPEG snapshot exceeds bounded buffer')
            if ready==1 and total<100:raise ValueError('Incomplete JPEG snapshot')
            self.total=total
            return dict(snapshot=snap,game_frame=game_frame,digest=digest,total=total,ready=ready)
        snap,offset,count,reserved=struct.unpack_from('<IHBB',p)
        requested,at=struct.unpack('<IH',extra)
        if snap!=requested or offset!=at or reserved or count!=min(28,self.total-at) or at>=self.total:raise ValueError('Expired or invalid snapshot chunk')
        return bytes(p[8:8+count])
class Bridge:
    def __init__(self,preview=True):
        self.lock=threading.Lock();self.stop=threading.Event();self.token=secrets.token_urlsafe(32)
        self.connected=False;self.error='Waiting for C5 v9';self.reply={};self.fps=0.;self.buttons=0;self.updated=0.;self.release=True;self.input_queue=deque()
        self.preview=preview;self.picture=None;self.screen=None;self.connection=0;self.frame_seq=0
        self.display={};self.desired_display=None
        self.worker=threading.Thread(target=self.run,daemon=True);self.worker.start()
    def keys(self,value,release=False):
        if type(value)is not int or not 0<=value<=255:raise ValueError('Invalid input mask')
        with self.lock:
            if not self.connected and value:raise ValueError('Meter not connected')
            if release:self.input_queue.clear()
            elif value!=self.buttons:
                if len(self.input_queue)>=32:self.input_queue.clear();self.release=True
                else:self.input_queue.append(value)
            self.buttons=value;self.updated=time.monotonic();self.release|=release
    def status(self):
        with self.lock:return dict(connected=self.connected,error=self.error,reply=self.reply,fps=self.fps,preview_enabled=self.preview,screen=self.screen,connection_id=self.connection,display=self.display)
    def settings(self,b,f):
        if type(b)is not int or not 10<=b<=100 or type(f)is not bool:raise ValueError('Invalid display settings')
        with self.lock:
            if not self.connected:raise ValueError('Meter not connected')
            self.desired_display=(b,int(f));self.buttons=0;self.input_queue.clear();self.release=True
    def run(self):
        import hid
        while not self.stop.is_set():
            device=client=None
            try:
                found=hid.enumerate(0x0716,0x5053)
                if len(found)!=1 or found[0].get('serial_number')!='20211222':raise RuntimeError('Connect the owner C5 running v9; close WITRNUP and other monitors.')
                device=hid.device();device.open_path(found[0]['path']);device.set_nonblocking(True)
                for _ in range(16):
                    if not device.read(65):break
                else:raise RuntimeError('Another HID client is active')
                device.set_nonblocking(False);client=Client(device);state=client.exchange()
                with self.lock:
                    self.connected=True;self.connection+=1;self.error='';self.reply=state;self.buttons=0;self.release=True;self.screen=None;self.picture=None;self.input_queue.clear()
                last_control=0.;last_rate=time.monotonic();last_frames=state['frames'];next_preview=0.;capture=None;data=bytearray();waiting=False;last_settings=0.
                with self.lock:self.display={};self.desired_display=None
                while not self.stop.is_set():
                    now=time.monotonic()
                    with self.lock:
                        release=self.release;self.release=False
                        if now-self.updated>=0.35:self.input_queue.clear();self.buttons=0
                        queued=bool(self.input_queue) and not release
                        mask=self.input_queue.popleft() if queued else self.buttons
                        enabled=self.preview
                        desired=self.desired_display
                    if release or queued or now-last_control>=0.04:
                        state=client.exchange(0x98,bytes([0 if release else mask,1 if release else 0]));last_control=now
                        if state['state']=='ERROR':raise RuntimeError(client.exchange(0x96)['error_text'])
                        with self.lock:
                            self.reply=state
                            if now-last_rate>=0.5:
                                self.fps=(state['frames']-last_frames)/(now-last_rate);last_frames=state['frames'];last_rate=now
                        continue
                    if desired is not None or now-last_settings>=0.5:
                        setting=client.exchange(0x9e,bytes(desired) if desired is not None else b'\0\0');last_settings=now
                        with self.lock:
                            self.display=setting
                            if self.desired_display==desired:self.desired_display=None
                        continue
                    if not enabled:capture=None;waiting=False;self.stop.wait(0.005);continue
                    if capture is None and now>=next_preview:
                        capture=client.exchange(0x9a,b'\0');waiting=True;data=bytearray()
                    elif capture is not None and waiting:
                        capture=client.exchange(0x9a,b'\1')
                        if capture['ready']:waiting=False
                        else:self.stop.wait(0.01)
                    elif capture is not None:
                        data+=client.exchange(0x9c,struct.pack('<IH',capture['snapshot'],len(data)))
                        if len(data)==capture['total']:
                            if fnv(data)!=capture['digest'] or data[:2]!=b'\xff\xd8' or data[-2:]!=b'\xff\xd9':raise ValueError('JPEG snapshot integrity mismatch')
                            picture=bytes(data);self.frame_seq+=1
                            with self.lock:
                                self.picture=picture;self.screen=dict(sequence=self.frame_seq,game_frame=capture['game_frame'],width=320,height=172)
                            capture=None;next_preview=now+0.08
                    else:self.stop.wait(0.005)
            except Exception as e:
                with self.lock:self.connected=False;self.error=f'{type(e).__name__}: {e}';self.buttons=0;self.screen=None;self.picture=None
            finally:
                if client:
                    try:client.exchange(0x98,b'\0\1')
                    except Exception:pass
                if device:device.close()
                with self.lock:self.connected=False;self.buttons=0
            self.stop.wait(1)
    def close(self):self.stop.set();self.worker.join(timeout=2)
def handler_for(bridge):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def valid_host(self):return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
        def send(self,data,kind='application/json',code=200):
            if isinstance(data,dict):data=json.dumps(data).encode()
            self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.end_headers();self.wfile.write(data)
        def do_GET(self):
            if not self.valid_host():return self.send({'error':'Host rejected'},code=403)
            path=self.path.split('?')[0]
            if path=='/api/session':return self.send({'token':bridge.token})
            if path=='/api/status':return self.send(bridge.status())
            if path=='/api/frame.jpg':
                with bridge.lock:data=bridge.picture
                return self.send(data or b'',kind='image/jpeg',code=200 if data else 404)
            files={'/':('index.html','text/html; charset=utf-8'),'/controller.js':('controller.js','text/javascript'),'/style.css':('style.css','text/css'),'/WITRN_C5.png':('WITRN_C5.png','image/png')}
            if path not in files:return self.send({'error':'Not found'},code=404)
            name,kind=files[path];return self.send((HERE/'web'/name).read_bytes(),kind)
        def do_POST(self):
            origin=self.headers.get('Origin')
            if not self.valid_host() or (origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}')) or not secrets.compare_digest(self.headers.get('X-C5-Token',''),bridge.token):return self.send({'error':'Request rejected'},code=403)
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=4096 or self.headers.get('Content-Type')!='application/json':raise ValueError('Invalid JSON body')
                data=json.loads(self.rfile.read(n))
                if not isinstance(data,dict):raise ValueError('Expected object')
                if self.path=='/api/keys':bridge.keys(data['buttons'])
                elif self.path=='/api/release':bridge.keys(0,True)
                elif self.path=='/api/display':bridge.settings(data['brightness'],data['flip'])
                elif self.path=='/api/preview':
                    if type(data.get('enabled'))is not bool:raise ValueError('Expected boolean')
                    with bridge.lock:bridge.preview=data['enabled']
                else:return self.send({'error':'Not found'},code=404)
                self.send({'ok':True})
            except (ValueError,KeyError,TypeError) as e:self.send({'error':str(e)},code=400)
    return Handler
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8768);p.add_argument('--no-browser',action='store_true');p.add_argument('--no-preview',action='store_true');a=p.parse_args()
    bridge=Bridge(not a.no_preview)
    try:
        with ThreadingHTTPServer(('127.0.0.1',a.port),handler_for(bridge)) as server:
            print(f'C5 controller: http://127.0.0.1:{server.server_port}/',flush=True)
            print('Close WITRNUP/monitor-doom.ps1. Ctrl+C stops PC control; the game continues.',flush=True)
            if not a.no_browser:webbrowser.open(f'http://127.0.0.1:{server.server_port}/')
            try:server.serve_forever()
            except KeyboardInterrupt:pass
    finally:bridge.close()
if __name__=='__main__':main()

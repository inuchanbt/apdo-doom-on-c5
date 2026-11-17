"""Explicit browser-test fixture, no HID access. Never used by play-pc.ps1."""
import threading,time,json
from pathlib import Path
from http.server import ThreadingHTTPServer
import controller
HERE=Path(__file__).resolve().parent
class Fixture:
    def __init__(self):
        self.lock=threading.Lock();self.token='local-test-token';self.preview=True;self.picture=(HERE/'host-build/preview.jpg').read_bytes();self.events=[];self.display=dict(brightness=30,flip=False,pending=False)
    def keys(self,value,release=False):
        if type(value)is not int or not 0<=value<=255:raise ValueError('Invalid mask')
        self.events.append(dict(buttons=value,release=release))
        (HERE/'host-build/web-events.json').write_text(json.dumps(self.events))
    def settings(self,b,f):
        if type(b)is not int or not 10<=b<=100 or type(f)is not bool:raise ValueError('Invalid settings')
        self.display=dict(brightness=b,flip=f,pending=False)
    def status(self):return dict(connected=True,error='',fps=13.4,reply=dict(render_ms=39,present_ms=37),preview_enabled=self.preview,screen=dict(sequence=1,game_frame=42,width=320,height=172),connection_id=1,display=self.display)
if __name__=='__main__':
    fixture=Fixture()
    with ThreadingHTTPServer(('127.0.0.1',8769),controller.handler_for(fixture)) as server:
        print('TEST FIXTURE http://127.0.0.1:8769',flush=True);server.serve_forever()

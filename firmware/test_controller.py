"""HTTP handler and background input scheduling with in-memory transports only."""
from collections import deque
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
import json,threading,time
from pathlib import Path
import controller
from test_web_server import Fixture
HERE=Path(__file__).resolve().parent

def main():
    fixture=Fixture();Handler=controller.handler_for(fixture)
    class Connection:
        def __init__(self,data):self.input=BytesIO(data);self.output=bytearray()
        def makefile(self,*a):return self.input
        def sendall(self,data):self.output+=data
    def request(route,body=None,headers=None):
        data=b'' if body is None else json.dumps(body).encode()
        h={'Host':'127.0.0.1:8769','Content-Type':'application/json','X-C5-Token':fixture.token,'Content-Length':str(len(data)),**(headers or {})}
        wire=(('GET' if body is None else 'POST')+' '+route+' HTTP/1.0\r\n'+''.join(k+': '+v+'\r\n' for k,v in h.items())+'\r\n').encode()+data
        c=Connection(wire);Handler(c,('127.0.0.1',1),SimpleNamespace(server_port=8769))
        head,body=bytes(c.output).split(b'\r\n\r\n',1)
        return int(head.split()[1]),body
    assert request('/api/status')[0]==200
    assert request('/api/frame.jpg')[1][:2]==b'\xff\xd8'
    assert request('/api/keys',{'buttons':3})[0]==200 and fixture.events[-1]['buttons']==3
    assert request('/api/release',{})[0]==200 and fixture.events[-1]['release']
    for buttons in (-1,256,True,'3',None):assert request('/api/keys',{'buttons':buttons})[0]==400
    assert request('/api/preview',{'enabled':False})[0]==200 and not fixture.preview
    assert request('/api/preview',{'enabled':1})[0]==400
    for headers in ({'Host':'untrusted.invalid'},{'Origin':'https://untrusted.invalid'},{'X-C5-Token':'bad'}):assert request('/api/keys',{'buttons':1},headers)[0]==403
    assert request('/../DOOM.DAT')[0]==404
    assert request('/api/session',headers={'Host':'untrusted.invalid'})[0]==403
    assert request('/api/display',{'brightness':75,'flip':True})[0]==200 and fixture.display['brightness']==75
    for b,f in ((0,False),(101,False),(50,1)):
        assert request('/api/display',{'brightness':b,'flip':f})[0]==400
    # Real background scheduler, fake HID and Client. No OS USB methods run.
    sent=[]
    class Device:
        def open_path(self,p):pass
        def set_nonblocking(self,v):pass
        def read(self,n):return []
        def close(self):pass
    class Client:
        def __init__(self,d):pass
        def exchange(self,command=0x90,extra=b''):
            if command==0x9e:return dict(brightness=30,flip=False,pending=False)
            if command==0x98:sent.append((time.monotonic(),extra))
            time.sleep(.001)
            return {'state':'PLAY','frames':len(sent),'render_ms':39,'present_ms':37}
    hid=SimpleNamespace(enumerate=lambda *a:[{'serial_number':'20211222','path':b'test'}],device=Device)
    def until(fn):
        deadline=time.monotonic()+2
        while not fn():
            if time.monotonic()>deadline:raise AssertionError('Scheduler timed out')
            time.sleep(.005)
    with patch.dict('sys.modules',{'hid':hid}),patch.object(controller,'Client',Client):
        b=controller.Bridge(False)
        try:
            until(lambda:b.status()['connected']);until(lambda:bool(sent))
            b.keys(3);b.keys(0)
            until(lambda:any(e==b'\3\0' for _,e in sent))
            at=next(i for i,(_,e) in enumerate(sent) if e==b'\3\0')
            until(lambda:any(e==b'\0\0' for _,e in sent[at+1:]))
            b.keys(128);until(lambda:sent[-1][1]==b'\x80\0')
            until(lambda:sent[-1][1]==b'\0\0') # silent browser expires
            b.keys(255);b.keys(0,True);until(lambda:sent[-1][1]==b'\0\1')
        finally:b.close()
        assert not b.worker.is_alive() and sent[-1][1]==b'\0\1'
    report=dict(http_routes=True,invalid_requests_rejected=True,loopback_host_origin_token=True,
                queued_tap_preserved=True,silent_browser_expires=True,explicit_and_shutdown_release=True,
                fake_hid_only=True,hardware_tested=False)
    (HERE/'host-build/controller-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()

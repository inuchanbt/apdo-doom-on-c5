// Browser integration through local CDP pipes and intercepted fixture responses.
// No network connection or HID access; HTTP handler is tested separately.
import {spawn} from 'node:child_process';
import os from 'node:os';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.dirname(fileURLToPath(import.meta.url));
const out=path.join(root,'host-build');
await mkdir(out,{recursive:true});
const chrome=spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',[
  '--headless=new','--no-sandbox','--disable-gpu','--no-first-run','--no-default-browser-check',
  '--remote-debugging-pipe',`--user-data-dir=${path.join(os.tmpdir(),'c5-chrome-test-pipe')}`,'about:blank'
],{windowsHide:true,stdio:['ignore','ignore','ignore','pipe','pipe']});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let session,serial=0,buffer='';const pending=new Map();const errors=[],events=[];let preview=true,display={brightness:30,flip:false,pending:false};
async function fixture(p){
 const url=new URL(p.request.url);let body,kind='application/json',responseCode=200;
 if(url.pathname==='/api/session')body=JSON.stringify({token:'local-test-token'});
 else if(url.pathname==='/api/status')body=JSON.stringify({connected:true,error:'',fps:13.4,reply:{render_ms:39,present_ms:37},preview_enabled:preview,screen:{sequence:1,game_frame:42},connection_id:1,display});
 else if(url.pathname==='/api/keys'||url.pathname==='/api/release'){
   events.push({buttons:JSON.parse(p.request.postData).buttons||0,release:url.pathname==='/api/release'});body='{"ok":true}';
 }else if(url.pathname==='/api/display'){display={...JSON.parse(p.request.postData),pending:false};body='{"ok":true}';}
 else if(url.pathname==='/api/preview'){preview=JSON.parse(p.request.postData).enabled;body='{"ok":true}';}
 else if(url.pathname==='/api/frame.jpg'){body=await readFile(path.join(out,'preview.jpg'));kind='image/jpeg';}
 else{
   const files={'/':['index.html','text/html; charset=utf-8'],'/controller.js':['controller.js','text/javascript'],'/style.css':['style.css','text/css'],'/WITRN_C5.png':['WITRN_C5.png','image/png']};
   const f=files[url.pathname];if(f){body=await readFile(path.join(root,'web',f[0]));kind=f[1];}else{body='';responseCode=404;}
 }
 await send('Fetch.fulfillRequest',{requestId:p.requestId,responseCode,responseHeaders:[{name:'Content-Type',value:kind}],body:Buffer.from(body).toString('base64')});
}
chrome.stdio[4].on('data',d=>{buffer+=d.toString();let at;while((at=buffer.indexOf('\0'))>=0){const m=JSON.parse(buffer.slice(0,at));buffer=buffer.slice(at+1);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(p)m.error?p.reject(m.error):p.resolve(m.result);}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params);else if(m.method==='Fetch.requestPaused')fixture(m.params).catch(e=>errors.push(String(e)));}});
async function waitFor(fn){for(let i=0;i<100;i++){try{const r=await fn();if(r)return r;}catch{}await delay(100);}throw Error('Timed out');}
function send(method,params={}){const id=++serial;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout: '+method));},5000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v);},reject:e=>{clearTimeout(timer);reject(e);}});chrome.stdio[3].write(JSON.stringify({id,method,params,sessionId:method.startsWith('Target.')||method.startsWith('Browser.')?undefined:session})+'\0');});}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
try{
 const t=await send('Target.createTarget',{url:'about:blank'});
 session=(await send('Target.attachToTarget',{targetId:t.targetId,flatten:true})).sessionId;
 await send('Runtime.enable');await send('Page.enable');
 await send('Fetch.enable',{patterns:[{urlPattern:'*'}]});
 await send('Emulation.setDeviceMetricsOverride',{width:1200,height:930,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:'http://c5-fixture.test/'});
 await waitFor(()=>evaluate(`document.getElementById('screen')?.naturalWidth===320 && !document.getElementById('enable').disabled`));
 const event=(type,code)=>evaluate(`window.dispatchEvent(new KeyboardEvent('${type}',{code:'${code}',bubbles:true,cancelable:true}))`);
 await evaluate(`document.getElementById('enable').click()`);
 await event('keydown','KeyW');await event('keydown','Space');await delay(120);
 await event('keyup','KeyW');await event('keyup','Space');await delay(120);
 await event('keydown','ArrowDown');await delay(100);
 await evaluate(`window.dispatchEvent(new Event('blur'))`);await delay(100);
 await evaluate(`document.getElementById('preview').click()`);await delay(350);
 assert.equal(await evaluate(`document.getElementById('preview').checked`),false);
 await evaluate(`document.getElementById('preview').click()`);await delay(350);
 await evaluate(`document.getElementById('enlarge').click()`);
 assert.equal(await evaluate(`document.getElementById('large').open`),true);
 await evaluate(`document.getElementById('close').click()`);
 // Real CDP pointer input exercises setPointerCapture and pointer release.
 const rect=await evaluate(`(()=>{let r=document.querySelector('[data-key="16"]').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
 await send('Input.dispatchMouseEvent',{type:'mousePressed',...rect,button:'left',clickCount:1});await delay(120);
 await send('Input.dispatchMouseEvent',{type:'mouseReleased',...rect,button:'left',clickCount:1});await delay(120);
 await evaluate(`document.getElementById('flip').click()`);await delay(400);
 assert.equal(await evaluate(`document.querySelector('.device').classList.contains('flipped')`),true);
 await evaluate(`document.getElementById('brightness').value=75;document.getElementById('brightness').dispatchEvent(new Event('change'))`);await delay(400);
 assert.equal(display.brightness,75);assert.equal(display.flip,true);
 const flipped=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await writeFile(path.join(out,'controller-flipped.png'),Buffer.from(flipped.data,'base64'));
 await evaluate(`document.getElementById('flip').click()`);await delay(400);
 const desktop=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await writeFile(path.join(out,'controller-desktop.png'),Buffer.from(desktop.data,'base64'));
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await delay(400);
 assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true);
 const mobile=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await writeFile(path.join(out,'controller-mobile.png'),Buffer.from(mobile.data,'base64'));
 await writeFile(path.join(out,'web-events.json'),JSON.stringify(events,null,2));
 for(const buttons of [2,3,1,0,128,16])assert(events.some(e=>e.buttons===buttons),`Missing mask ${buttons}`);
 assert(events.some(e=>e.release&&e.buttons===0));assert.equal(errors.length,0);
 const report={display_flip_and_brightness:true,keyboard_combinations:true,pointer_controls:true,blur_release:true,preview_toggle:true,expanded_preview:true,mobile_no_overflow:true,browser_errors:errors.length,fixture_only:true,hardware_tested:false};
 await writeFile(path.join(out,'web-validation.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{try{await send('Browser.close');}catch{}chrome.kill();}

"""Build the first native C5 DOOM application offline; never opens USB."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from operator import xor
import hashlib
import json
import subprocess
import struct
import sys
import os
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SRC=ROOT/'vendor/dmc100-doom'
LLVM=Path(os.environ['APDO_LLVM_BIN']) if os.environ.get('APDO_LLVM_BIN') else Path(shutil.which('clang.exe') or shutil.which('clang') or ROOT/'tools/llvm-mingw-20261020-ucrt-x86_64/bin/clang.exe').parent
OUT=HERE/'build'
sys.path.insert(0,str(ROOT/'tools'))
from c5_compare import DECODE,FAMILY,decode_package
def sha(b):return hashlib.sha256(b).hexdigest()
def run(args):return subprocess.run([str(a) for a in args],check=True,capture_output=True,text=True).stdout

def main():
    global OUT
    host_test='--host-test' in sys.argv or '--host-reference' in sys.argv
    if host_test:OUT=HERE/('host-reference' if '--host-reference' in sys.argv else 'host-build')
    OUT.mkdir(exist_ok=True)
    if not (LLVM/'clang.exe').is_file():
        raise RuntimeError('Set APDO_LLVM_BIN to the llvm-mingw bin directory; see docs/BUILD.md')
    # Only hashes identify the private development baseline. No owner flash is
    # redistributed or needed to compile this source. Qualify each device separately.
    baseline_sha='fc128f7dccd16a163fbd8836b775befeda72719063a8a62edd1637fa2fc38cef'
    boot_sha='aaf175a47bda0ad2f4a5b66f6759ac157b16fb4cccd565a13b63b0e182cab30d'
    game=(HERE/'DOOM.DAT').read_bytes()
    assert len(game)==1056192 and sha(game)==json.loads((HERE/'assets.json').read_text())['pack_sha256']
    # Locally preserve the exact tested game pack; host pins its hash before USB.
    (OUT/'DOOM.DAT').write_bytes(game)
    excluded={'am_map.c','w_wad.c','w_file.c','z_zone.c'}
    sources=[p for p in (SRC/'engine').glob('*.c') if p.name not in excluded]
    for folder in ['port/data','port/render','port/obj','port/math']:
        sources += [p for p in (SRC/folder).glob('*.c') if p.name not in
                    {'img.c','img_check.c','fat_write.c','fat12.c','extents.c'}]
    sources += [SRC/p for p in ['port/game/fe_glue.c','port/game/l_menu.c','port/game/l_wi.c',
                'port/game/l_finale.c','port/game/i_input.c','port/game/libc_dmc.c',
                'platform/rt.c','platform/text.c','platform/font8x8.c']]
    sources+=list((SRC/'gen').glob('*.c'))
    sources+=[HERE/'assets.c',HERE/'asset_data.c',HERE/'display.c',HERE/'pc.c',HERE/'jpeg.c',HERE/'splash.c',ROOT/'native/doom_bridge.c',HERE/'wide_view.c',HERE/'c5_doom.c']
    flags=['--target=thumbv7em-none-eabihf','-mcpu=cortex-m4','-mthumb','-mfpu=fpv4-sp-d16',
           '-mfloat-abi=hard','-Oz','-std=gnu11','-ffreestanding','-fno-common','-fno-builtin',
           '-fwrapv','-fsigned-char','-ffunction-sections','-fdata-sections',
           '-fstack-usage','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-fno-stack-protector',
           '-DDMC_FW','-DPLAT_HOST','-DDMC_SINE_L1','-DKM_CACHE_KIB=1','-DKM_INPUT_AT_FRAME','-DKWS_WIDE_VIEW']
    if host_test:
        sources[-1]=HERE/'host_harness.c'
        flags=flags[5:]
        if '--host-reference' in sys.argv:flags += ['-DC5_HOST_RAW']
    for folder in ['gen','engine/stub/include','engine','port/data','port/render','port/obj',
                   'port/math','platform','port/game','port/ovl']:flags+=['-I',str(SRC/folder)]
    def compile_one(item):
        index,src=item;obj=OUT/f'{index:03}-{src.stem}.o'
        warnings=['-Wall','-Wextra','-Werror'] if src.parent==HERE and src.name not in ('host_harness.c','jpeg.c') else ['-w']
        extra=['-U_WIN32'] if host_test and src.name!='host_harness.c' else []
        opt=['-O2'] if src.name in ('assets.c','display.c','c5_doom.c','jpeg.c') else []
        try:run([LLVM/'clang.exe',*flags,*opt,*warnings,*extra,'-c',src,'-o',obj])
        except subprocess.CalledProcessError as e:raise RuntimeError(e.stderr) from e
        return obj
    with ThreadPoolExecutor(max_workers=8) as pool:objects=list(pool.map(compile_one,enumerate(sources)))
    if host_test:
        print(run([LLVM/'clang.exe','-shared','-Wl,--gc-sections',*objects,'-o',OUT/'c5-engine-test.dll']))
        print('Built host engine with C5 projection (hardware not emulated).')
        return
    vec=['.syntax unified','.thumb','.section .vectors,"a",%progbits','.word 0x20017000','.word reset_handler']
    vec+=['.word '+('systick_handler' if i==15 else '0x080029ed' if i==36 else 'fault_handler') for i in range(2,256)]
    (OUT/'vectors.S').write_text('\n'.join(vec)+'\n',encoding='ascii')
    elf=OUT/'c5-native-doom.elf'
    try:run([LLVM/'clang.exe',*flags,'-nostdlib','-fuse-ld=lld','-Wl,--gc-sections','-Wl,--build-id=none',
             '-Wl,-T,'+str(HERE/'memory.ld'),'-Wl,-Map,'+str(OUT/'c5-native-doom.map'),OUT/'vectors.S',*objects,'-o',elf])
    except subprocess.CalledProcessError as e:raise RuntimeError(e.stderr) from e
    assert not run([LLVM/'llvm-nm.exe','--undefined-only',elf]).strip()
    run([LLVM/'llvm-objcopy.exe','-O','binary',elf,OUT/'c5-native-doom.raw'])
    raw=(OUT/'c5-native-doom.raw').read_bytes()
    assert len(raw)<=0xdffd0
    payload=raw.ljust(0xdffd0,b'\xff') # file exactly896KiB; 448 x2KiB pages
    sp,entry=struct.unpack_from('<II',payload)
    assert sp==0x20017000 and entry&1 and 0x08005000<=entry<0x080e3fd0
    assert payload[0x810:0x814]==b'C400' and payload[0xc00:0xc04]==b'\xff'*4
    assert struct.unpack_from('<I',payload,36*4)[0]==0x080029ed
    head=bytearray(b'\xff'*48);head[:7]=b'gzutapp';struct.pack_into('<HBB',head,7,2026,11,16)
    head[20:36]=FAMILY;struct.pack_into('<III',head,36,len(payload),reduce(xor,payload,0),sum(payload)&0xffffffff)
    package=(bytes(head)+payload).translate(bytes(DECODE.index(i) for i in range(256)))
    assert decode_package(package)==payload and len(package)==0xe0000
    (OUT/'C5-native-doom-v9.1.c4ser').write_bytes(package)
    (OUT/'c5-native-doom.bin').write_bytes(payload)
    disasm=run([LLVM/'llvm-objdump.exe','-d','--mcpu=cortex-m4',elf])
    assert '<unknown>' not in disasm, 'Unsupported instruction in Cortex-M4 disassembly'
    (OUT/'isa-validation.json').write_text(json.dumps({'fpu':'fpv4-sp-d16','cortex_m4_unknown_instructions':0,'hardware_tested':False},indent=2)+'\n')
    (OUT/'c5-native-doom.disasm.txt').write_text(disasm,encoding='utf8')
    sizes=run([LLVM/'llvm-size.exe','-A',elf]);print(sizes)
    sections={}
    for line in sizes.splitlines():
        p=line.split()
        if len(p)==3 and p[0].startswith('.') and p[1].isdigit():sections[p[0]]=int(p[1])
    assert sections['.data']+sections['.bss']<=80*1024
    manifest={'schema':'c5-native-doom-v9.1','hardware_tested':False,'package_bytes':len(package),
              'payload_bytes':len(payload),'raw_image_bytes':len(raw),'package_sha256':sha(package),
              'baseline_sha256':baseline_sha,'boot_sha256':boot_sha,
              'app_start':'0x08004000','payload_end':'0x080e3fd0','expected_erase_end':'0x080e4000',
              'initial_sp':hex(sp),'reset_vector':hex(entry),'sections':sections,
              'static_ram_bytes':sections['.data']+sections['.bss'],
              'game_pack_bytes':len(game),'game_pack_sha256':sha(game),
              'runtime_flash_programming':False,'boot_private_abi':True,'pc_required':False,'all_resources_local':True}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    inputs=sources+list(SRC.rglob('*.h'))+[HERE/'memory.ld',HERE/'assets.h',HERE/'display.h',HERE/'pc.h',HERE/'asset_meta.h',HERE/'prepare.py',HERE/'build.py',HERE/'adapt_jpeg.py',HERE/'tiny_jpeg.original.h',HERE/'jpeg-source.json',ROOT/'SOURCE_LOCK.json']
    (OUT/'source-hashes.json').write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in inputs},indent=2)+'\n',encoding='utf8')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()

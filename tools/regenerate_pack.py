"""Regenerate the shipped half-art Freedoom E1M1 resource pack from its pinned ZIP."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'vendor/dmc100-doom'
sys.path.insert(0, str(SRC))
from tools.conv import fetch, wadread, info, pack, plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freedoom-zip', type=Path, required=True)
    args = parser.parse_args()
    wad_bytes, notices = fetch.extract(str(args.freedoom_zip))
    wad = wadread.Wad(wad_bytes)
    upstream = json.loads((SRC / 'build/conv/upstream.json').read_text())
    dehacked = wadread.dehacked(wad)
    inf, dense = info.build(wad, upstream, dehacked)
    context = pack.Ctx(wad, wad_bytes, notices, upstream, dehacked, inf, dense, plan.load_layout(None))
    config = dict(pack.PACKS['E1M1'])
    config.update(base=1, mips=1, xshift=1, ui_exclude=('HELP1', 'CREDIT'), ui_half=('TITLEPIC', 'WIMAP0'))
    built = pack.build_image(context, 'E1M1', config, {})
    data, _, _ = pack.finish(context, 'E1M1', built)
    expected = json.loads((ROOT / 'SOURCE_LOCK.json').read_text())['c5']['game_pack_sha256']
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Regenerated pack differs from this source revision.')
    (ROOT / 'firmware/DOOM.DAT').write_bytes(data)
    print('Verified and regenerated', len(data), 'bytes; then run firmware/prepare.py.')


if __name__ == '__main__':
    main()

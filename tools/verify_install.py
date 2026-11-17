"""Offline comparison of your own before/after DFU backups; never writes a device."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
from qualify_backup import qualify

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'firmware'))
import audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--package', type=Path, default=ROOT / 'firmware/build/C5-native-doom-v9.1.c4ser')
    args = parser.parse_args()
    qualify(args.before)
    qualify(args.after)
    package = args.package.read_bytes()
    expected = json.loads((ROOT / 'SOURCE_LOCK.json').read_text())['c5']['package_sha256']
    if hashlib.sha256(package).hexdigest() != expected:
        parser.error('Package does not match this source revision.')
    before = (args.before / 'flash-pass1.bin').read_bytes()
    after = (args.after / 'flash-pass1.bin').read_bytes()
    result = audit.audit(after, package, before)
    output = args.after / 'installation-audit.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('Audit:', output)
    return 0 if result['installation_matches_bounded_erase_model'] else 3


if __name__ == '__main__':
    raise SystemExit(main())

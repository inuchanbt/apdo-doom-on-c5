"""Offline qualification of your own two-pass backup. Never opens USB."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def qualify(folder):
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    first = (folder / 'flash-pass1.bin').read_bytes()
    second = (folder / 'flash-pass2.bin').read_bytes()
    if manifest.get('status') != 'verified_identical' or len(first) != 0x100000 or first != second:
        raise ValueError('Need a verified, byte-identical two-pass 1 MiB backup.')
    digest = hashlib.sha256(first).hexdigest()
    if digest != manifest.get('sha256'):
        raise ValueError('Backup manifest hash differs from the files.')
    expected = json.loads((ROOT / 'SOURCE_LOCK.json').read_text())['c5']
    boot_hash = hashlib.sha256(first[:expected['boot_prefix_bytes']]).hexdigest()
    if boot_hash != expected['boot_prefix_sha256']:
        raise ValueError('Bootloader differs from this C5 target. Do not install this candidate.')
    return dict(full_flash_sha256=digest, boot_prefix_sha256=boot_hash,
                two_complete_identical_reads=True, matches_target_bootloader=True,
                restore_tested=False, runtime_timing_or_hardware_success_proven=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    args = parser.parse_args()
    print(json.dumps(qualify(args.backup), indent=2))


if __name__ == '__main__':
    main()

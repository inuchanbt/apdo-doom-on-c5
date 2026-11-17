"""Windows kit entry point. Flashing is performed manually in the official updater."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def self_check():
    expected = json.loads((ROOT / 'SOURCE_LOCK.json').read_text())['c5']['package_sha256']
    package = ROOT / 'firmware/build/C5-native-doom-v9.1.c4ser'
    if hashlib.sha256(package.read_bytes()).hexdigest() != expected:
        raise ValueError('Firmware hash mismatch.')
    for name in ('firmware/controller.py', 'firmware/monitor.py', 'firmware/web/index.html',
                 'firmware/web/controller.js', 'firmware/web/style.css', 'firmware/web/WITRN_C5.png',
                 'tools/c5_probe.py', 'tools/c5_backup.py', 'docs/INSTALL.md', 'docs/INSTALL.ja.md',
                 'LICENSE', 'notices/freedoom-0.13.0/COPYING.txt', 'notices/freedoom-0.13.0/CREDITS.txt'):
        if not (ROOT / name).is_file():
            raise FileNotFoundError(name)
    sums = ROOT / 'SHA256SUMS.txt'
    if sums.exists():
        for line in sums.read_text().splitlines():
            digest, name = line.split('  ', 1)
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('Kit checksum mismatch: ' + name)
    print('Firmware and kit files verified. No USB device accessed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', choices=('check', 'controller', 'monitor', 'backup'))
    args = parser.parse_args()
    action = args.action
    if action is None:
        print('APDO DOOM on WITRN C5 - v9.1 OWNER-TESTED PRE-RELEASE (ONE C5)')
        print('1 Check files / 2 PC controller / 3 Monitor / 4 Read-only DFU backup / 0 Exit')
        action = {'1': 'check', '2': 'controller', '3': 'monitor', '4': 'backup'}.get(input('> ').strip())
    if action is None:
        return 0
    self_check()
    if action == 'check':
        return 0
    if action == 'controller':
        command = [ROOT / 'firmware/controller.py']
    elif action == 'monitor':
        output = ROOT / 'captures' / datetime.datetime.now().strftime('doom-%Y%m%d-%H%M%S.json')
        command = [ROOT / 'firmware/monitor.py', '--output', output]
    else:
        print('Close WITRNUP/controller. Hold OK when connecting; C5 must display DFU.')
        if input('Type DFU to start read-only backup: ').strip() != 'DFU':
            return 0
        command = [ROOT / 'tools/backup_device.py', '--dfu']
    return subprocess.call([sys.executable, '-X', 'utf8', *map(str, command)], cwd=ROOT)


if __name__ == '__main__':
    raise SystemExit(main())

"""Read-only DFU probe, two full reads, then offline bootloader qualification."""
from pathlib import Path
import argparse
import datetime
import json
import subprocess
import sys
from qualify_backup import qualify

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dfu', action='store_true', required=True, help='C5 must show DFU; hold OK when connecting')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    folder = (args.output or ROOT / 'backups' / datetime.datetime.now().strftime('c5-%Y%m%d-%H%M%S')).resolve()
    proof = folder.with_name(folder.name + '.probe.json')
    if folder.exists() or proof.exists():
        parser.error('Use a new output folder; existing backups are never overwritten.')
    proof.parent.mkdir(parents=True, exist_ok=True)
    for command in ([ROOT / 'tools/c5_probe.py', '--dfu', '--read-info', '--output', proof],
                    [ROOT / 'tools/c5_backup.py', '--dfu', '--probe-json', proof, '--output-dir', folder]):
        subprocess.run([sys.executable, '-X', 'utf8', *map(str, command)], check=True)
    result = qualify(folder)
    with (folder / 'qualification.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('Verified backup and target bootloader:', folder)
    print('This is a readback check, not a demonstrated restore. Keep this backup private.')


if __name__ == '__main__':
    main()

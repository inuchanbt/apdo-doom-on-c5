"""Prepare local review archives only. No git or network operations."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.0-rc.1'
DIRECTORIES = ('docs', 'firmware', 'native', 'notices', 'patches', 'tools', 'vendor')
ROOT_FILES = ('README.md', 'README.ja.md', 'LICENSE', 'COPYING', 'THIRD_PARTY_NOTICES.md',
              'CHANGELOG.md', 'SOURCE_LOCK.json', 'requirements.txt', 'requirements-dev.txt',
              'setup.cmd', 'C5-Tools.cmd', '.gitignore', '.gitattributes')
BUILD_FILES = ('C5-native-doom-v9.1.c4ser', 'manifest.json', 'source-hashes.json',
               'offline-validation.json', 'isa-validation.json')


def source_files():
    for name in ROOT_FILES:
        yield name, (ROOT / name).read_bytes()
    for directory in DIRECTORIES:
        for path in sorted((ROOT / directory).rglob('*')):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            parts = relative.parts
            if any(part in ('.git', '__pycache__', '.venv', 'dl') for part in parts):
                continue
            if directory == 'firmware' and parts[1] in ('build', 'host-build', 'host-reference', 'captures'):
                continue
            if directory == 'tools' and parts[1].startswith('llvm-mingw-'):
                continue
            if path.suffix.lower() in ('.pyc', '.o', '.exe', '.dll', '.a', '.elf', '.so'):
                continue
            if directory == 'vendor' and 'build' in parts and relative.as_posix() != 'vendor/dmc100-doom/build/conv/upstream.json':
                continue
            yield relative.as_posix(), path.read_bytes()


def archive(path, top, files):
    normalized = {name: (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n') if name.endswith('.cmd') else data)
                  for name, data in files.items()}
    sums = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in sorted(normalized.items()))
    normalized['SHA256SUMS.txt'] = sums.encode('utf-8')
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for name, data in sorted(normalized.items()):
            info = zipfile.ZipInfo(top + '/' + name, date_time=(2026, 11, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            out.writestr(info, data)
    with zipfile.ZipFile(path) as check:
        assert check.testzip() is None
    return {'file': path.name, 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'entries': len(normalized)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = dict(source_files())
    package = ROOT / 'firmware/build/C5-native-doom-v9.1.c4ser'
    expected = json.loads((ROOT / 'SOURCE_LOCK.json').read_text())['c5']['package_sha256']
    assert hashlib.sha256(package.read_bytes()).hexdigest() == expected
    offline = json.loads((ROOT / 'firmware/build/offline-validation.json').read_text())
    assert offline['source_hashes_match'] and offline['package_pin_matches']
    for name, digest in json.loads((ROOT / 'firmware/build/source-hashes.json').read_text()).items():
        assert name in source and hashlib.sha256(source[name]).hexdigest() == digest, name
    # Reject unit dumps and opaque executables even if a future edit broadens the file list.
    for name in source:
        assert not any(part in ('backups', 'captures', 'metadata', 'offline-updater', 'c5-standalone-rs') for part in Path(name).parts), name
        assert 'flash-pass' not in name.lower() and not name.lower().endswith('.c4ser'), name
    kit = dict(source)
    for name in BUILD_FILES:
        kit['firmware/build/' + name] = (ROOT / 'firmware/build' / name).read_bytes()
    report = {'version': VERSION, 'release_published': False, 'hardware_verified': False,
              'firmware_sha256': expected, 'source_included': True, 'archives': []}
    for suffix, files in [('source', source), ('install', kit)]:
        filename = f'APDO-DOOM-C5-{VERSION}-{suffix}.zip'
        report['archives'].append(archive(args.output / filename, f'APDO-DOOM-C5-{VERSION}', files))
    (args.output / 'SHA256SUMS.txt').write_text(''.join(item['sha256']+'  '+item['file']+'\n' for item in report['archives']))
    (args.output / 'package-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

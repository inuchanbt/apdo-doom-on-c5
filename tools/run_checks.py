"""Build and run existing offline C5 tests. No USB or physical-device operations."""
from pathlib import Path
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'verification'


def main():
    OUT.mkdir(exist_ok=True)
    commands = [('tools-unit-tests', ['-m', 'unittest', 'discover', '-s', 'tools', '-p', 'test_*.py'])]
    commands += [(label, ['firmware/build.py', *args]) for label, args in
                 [('target-build', []), ('host-build', ['--host-test']), ('host-reference', ['--host-reference'])]]
    commands += [(name, [f'firmware/{name}.py']) for name in
                 ('test_package', 'test_local', 'test_display', 'test_pc', 'test_jpeg', 'test_controller')]
    commands += [('kit-self-check', ['tools/launcher.py', 'check'])]
    results = []
    for label, command in commands:
        print('RUN', label, flush=True)
        started = time.monotonic()
        result = subprocess.run([sys.executable, '-X', 'utf8', *command], cwd=ROOT,
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        (OUT / (label + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        results.append(dict(check=label, exit_code=result.returncode, seconds=round(time.monotonic()-started, 2)))
        (OUT / 'checks.json').write_text(json.dumps(results, indent=2) + '\n')
        if result.returncode:
            print(result.stdout[-3000:] + result.stderr[-3000:])
            raise SystemExit(result.returncode)
        print('PASS', label, flush=True)
    print('All offline checks passed; hardware remains unverified.')


if __name__ == '__main__':
    main()

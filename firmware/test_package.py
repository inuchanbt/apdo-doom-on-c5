"""Offline package bounds, source pin and telemetry protocol checks. No USB."""
from pathlib import Path
import hashlib,json,struct
import audit,monitor
HERE=Path(__file__).resolve().parent
def main():
    package=(HERE/'build/C5-native-doom-v9.1.c4ser').read_bytes()
    # Deterministic synthetic bytes exercise protected-region checks without
    # publishing a device's bootloader, calibration or unit-specific contents.
    baseline=bytes(range(256))*4096
    actual=bytearray(baseline)
    actual[0x4000:0xe4000]=audit.decode_package(package)+b'\xff'*48
    actual[0x4c00:0x4c04]=b'\xfe\xff\xff\xff'
    assert audit.audit(bytes(actual),package,baseline)['installation_matches_bounded_erase_model']
    for offset in (0,0x3800,0x8000,0x4c00,0xe3fff,0xe4000,0xff800):
        damaged=actual.copy();damaged[offset]^=1
        assert not audit.audit(bytes(damaged),package,baseline)['installation_matches_bounded_erase_model']
    for path,expected in json.loads((HERE/'build/source-hashes.json').read_text()).items():
        assert hashlib.sha256((HERE.parent/path).read_bytes()).hexdigest()==expected,path
    sha=hashlib.sha256(package).hexdigest()
    assert sha==json.loads((HERE.parent/'SOURCE_LOCK.json').read_text())['c5']['package_sha256']
    seq=7;nonce=b'abcdefgh'
    payload=monitor.MAGIC+struct.pack('<I',seq)+nonce+struct.pack('<BBHIIIIHHIII',2,15,0,5000,123,0,321,130,28,456,192000000,1780)
    response=bytearray(64);response[:2]=b'\xff\x55';response[8:10]=bytes([0x91,52]);response[10:62]=payload
    response[62]=sum(response[8:62])&255;response[63]=sum(response[:62])&255
    status=monitor.parse(bytes(response),seq,nonce)
    assert status['render_ms']==130 and status['present_ms']==28 and status['frames']==123
    for command in (0x92,0x94,0x05):
        try:monitor.frame(command,payload[:16])
        except ValueError:pass
        else:raise AssertionError('Non-telemetry command accepted')
    for s,n in ((8,nonce),(7,b'badnonce')):
        try:monitor.parse(bytes(response),s,n)
        except ValueError:pass
        else:raise AssertionError('Wrong nonce/sequence accepted')
    bad=response.copy();bad[40]^=1
    try:monitor.parse(bytes(bad),seq,nonce)
    except ValueError:pass
    else:raise AssertionError('Checksum mismatch accepted')
    result=dict(package_sha256=sha,audit_expected_installation=True,audit_corruption_rejections=7,
                source_hashes_match=True,package_pin_matches=True,monitor_read_only_commands=True,
                monitor_timing_parser=True,hardware_tested=False,baseline='synthetic, not a device capture')
    (HERE/'build/offline-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()

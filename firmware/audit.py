"""Offline audit for the exact 896 KiB native C5 v9.1 package envelope."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'tools'))
from c5_compare import compare_dump,decode_package,differences

def audit(actual,package,baseline):
    profile_bytes=(HERE/'vendor-geometry.json').read_bytes()
    assert hashlib.sha256(profile_bytes).hexdigest()=='45efa16e4a898f7fd15b2d1b1c96f0376c5d94bc5e30e8049c726b0f22c6b0cc'
    profile=json.loads(profile_bytes)
    assert profile['profile']=='C4/5 Series' and profile['app_start']==0x08004000
    assert len(package)==0xe0000 and set(profile['page_bytes'][:448])=={2048}
    payload=decode_package(package);assert len(payload)==0xdffd0
    result=compare_dump(actual,package,baseline)
    start=0x4000;end=start+len(payload);erase_end=start+sum(profile['page_bytes'][:448])
    assert erase_end==0xe4000
    tail=actual[end:erase_end]
    result['vendor_erase_model']={
        'basis':'Pure C4/C5 profile 060000ba/060000b4: 2048-byte pages; 060000a5 consumes full file length',
        'profile_file_sha256':hashlib.sha256(profile_bytes).hexdigest(),
        'physical_candidate_readback_verified':False,
        'payload_end_exclusive':hex(0x08000000+end),'erase_end_exclusive':hex(0x08000000+erase_end),
        'erase_tail_bytes':len(tail),'erase_tail_all_ff':tail==b'\xff'*48,
        'after_erase_range':differences(actual[erase_end:],baseline[erase_end:],0x08000000+erase_end)}
    r=result['baseline_regions'];m=result['vendor_erase_model']
    result['installation_matches_bounded_erase_model']=(result['matches_package_with_observed_activation']
        and result['activation_word']=='0xfffffffe' and r['boot_below_factory_header']['identical']
        and r['factory_header_to_app_start']['identical'] and r['upper_2k_profile_area']['identical']
        and m['erase_tail_all_ff'] and m['after_erase_range']['identical'])
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('dump','package','baseline','output'):p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args();result=audit(a.dump.read_bytes(),a.package.read_bytes(),a.baseline.read_bytes())
    with a.output.open('x',encoding='utf8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('flash_sha256','activation_word','all_checked_outside_payload_regions_unchanged','installation_matches_bounded_erase_model')},indent=2))
    print('Audit:',a.output)
    return 0 if result['installation_matches_bounded_erase_model'] else 3
if __name__=='__main__':raise SystemExit(main())

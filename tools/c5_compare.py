"""Offline comparison of a verified C5 dump with an owner-supplied .c4ser.

No USB access. Preserves raw differences; the one observed activation byte is
reported explicitly, not silently ignored. Boot acceptance evidence applies to
the owner's captured 2024-08-06 bootloader, not every WITRN model/version.
"""
import argparse
from functools import reduce
import hashlib
import json
from operator import xor
from pathlib import Path
import struct

FLASH_BYTES = 0x100000
APP_OFFSET = 0x4000
MARKER_OFFSET = 0xC00
FAMILY = bytes.fromhex("ef3d7b682c3b634d93b922b17b051a12")
DECODE = bytes.fromhex(
    "1ab6b7f17b8cd53c7c90d2f435f21be9db12775b3d7f3fbd2d472a50dcc3ff578283"
    "60fc9b4e88d0005f2e592bf9c638f0c88e8044fd737e0b2919afd89671b362e6e511"
    "919c4615c4c2a552b966acb22253ee54aab474cfb06c72a7925a56e785ecc19fce6ea"
    "e3b788f5d4be2640c4c1363c0414fbae41004a63e31e1b8486705d39869bf3665be06"
    "515cc78b0937c5a9a870d4871dda0df37630ad1794e0b114ed0e08429a33b555d9453"
    "9e37d4d01cb27ef256a3a7a796d164061a402ab860f346feb6bf728dea3cc752cca5e81"
    "0afa68f8070324cd1fa22f32439df5d7bc9ebb494ad68a84a121df97fe20d11e931c8d"
    "fb261895f6c9ddea9923e8a05889"
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode_package(raw):
    data = raw.translate(DECODE)
    if len(data) < 48 or data[:7] != b"gzutapp" or data[20:36] != FAMILY:
        raise ValueError("Not a recognized C4/C5 package")
    length, byte_xor, byte_sum = struct.unpack_from("<III", data, 36)
    payload = data[48:]
    if length != len(payload) or not 0xC04 <= length <= FLASH_BYTES - APP_OFFSET:
        raise ValueError("Invalid payload length")
    if reduce(xor, payload, 0) != byte_xor or sum(payload) & 0xFFFFFFFF != byte_sum:
        raise ValueError("Firmware package checksum mismatch")
    return payload


def differences(actual, reference, address):
    if len(actual) != len(reference):
        raise ValueError("Comparison regions differ in length")
    count, samples = 0, []
    for offset, (a, b) in enumerate(zip(actual, reference)):
        if a != b:
            count += 1
            if len(samples) < 32:
                samples.append({"address": hex(address + offset), "actual": f"{a:02x}", "reference": f"{b:02x}"})
    return {"bytes": len(actual), "identical": count == 0, "different_bytes": count,
            "actual_sha256": sha(actual), "reference_sha256": sha(reference), "first_differences": samples}


def compare_dump(flash, package, baseline=None):
    if len(flash) != FLASH_BYTES or baseline is not None and len(baseline) != FLASH_BYTES:
        raise ValueError("Expected a complete 1 MiB internal-flash dump")
    payload = decode_package(package)
    app = flash[APP_OFFSET:APP_OFFSET + len(payload)]
    comparison = differences(app, payload, 0x08004000)
    activated = (comparison["different_bytes"] == 1 and
                 payload[MARKER_OFFSET:MARKER_OFFSET + 4] == b"\xff" * 4 and
                 app[MARKER_OFFSET:MARKER_OFFSET + 4] == b"\xfe\xff\xff\xff")
    result = {"schema": "witrn-c5-offline-comparison-v1", "flash_sha256": sha(flash),
              "package_sha256": sha(package), "package_checksums_valid": True,
              "payload": comparison, "exact_payload_match": comparison["identical"],
              "only_observed_activation_byte_differs": activated,
              "matches_package_with_observed_activation": comparison["identical"] or activated,
              "activation_word": hex(struct.unpack_from("<I", app, MARKER_OFFSET)[0]),
              "application_family_tag": app[0x810:0x814].decode("ascii", errors="replace"),
              "restore_tested": False}
    if baseline is not None:
        result["baseline_regions"] = {
            name: differences(flash[start:end], baseline[start:end], 0x08000000 + start)
            for name, (start, end) in {
                "boot_below_factory_header": (0, 0x3800),
                "factory_header_to_app_start": (0x3800, APP_OFFSET),
                "all_bytes_after_new_payload": (APP_OFFSET + len(payload), FLASH_BYTES),
                "upper_2k_profile_area": (0xFF800, FLASH_BYTES),
            }.items()}
        result["all_checked_outside_payload_regions_unchanged"] = all(
            region["identical"] for region in result["baseline_regions"].values())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new filename")
    try:
        result = compare_dump(args.dump.read_bytes(), args.package.read_bytes(),
                              args.baseline.read_bytes() if args.baseline else None)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf8") as out:
            json.dump(result, out, indent=2)
            out.write("\n")
        print(json.dumps(result, indent=2))
        if not result["matches_package_with_observed_activation"]:
            return 2
        if result.get("all_checked_outside_payload_regions_unchanged") is False:
            return 3  # Package matches, but outside-payload differences need review.
        return 0
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())

"""Exercise the full backup workflow with a simulated HID device, never hardware."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

import c5_backup as backup
import c5_probe as protocol


class SimulatedHid:
    def __init__(self, change_second_pass=False, fail_after=None):
        self.flash = bytearray((i * 13 + (i >> 8) + (i >> 16)) & 255 for i in range(backup.FLASH_BYTES))
        struct.pack_into("<II", self.flash, 0x4000, 0x20017D08, 0x08004311)
        self.descriptor = {"path": b"test-device", "vendor_id": protocol.VID, "product_id": protocol.PID,
                           "serial_number": "test", "release_number": 512, "product_string": "WITRN.C4",
                           "interface_number": 0}
        self.pending = b""
        self.addresses = []
        self.change_second_pass = change_second_pass
        self.fail_after = fail_after
        self.closed = False

    def enumerate(self, vid, pid): return [self.descriptor]
    def device(self): return self
    def open_path(self, path): assert path == self.descriptor["path"]
    def close(self): self.closed = True
    def set_nonblocking(self, enabled): pass
    def read(self, size, timeout=None):
        result, self.pending = self.pending, b""
        return result

    def write(self, report):
        assert len(report) == 65 and report[0] == 0
        assert report[1:3] == b"\xff\x55" and report[9:11] == b"\x0a\x05", "Only read command 10 allowed"
        address, count = struct.unpack_from("<IB", report, 11)
        assert protocol.FLASH_START <= address < address + count <= protocol.FLASH_END
        assert count == 32
        assert not self.pending, "Only one outstanding request permitted"
        offset = address - protocol.FLASH_START
        self.addresses.append(address)
        if self.fail_after is not None and len(self.addresses) > self.fail_after:
            return 65
        if self.change_second_pass and len(self.addresses) == 12 + backup.FLASH_BYTES // 32 + 1:
            self.flash[0x40000] ^= 1
        reply = bytearray(64)
        reply[:2] = b"\xff\x55"
        reply[8:10] = bytes((10, count))
        reply[10:10 + count] = self.flash[offset:offset + count]
        reply[62] = sum(reply[8:62]) % 256
        reply[63] = sum(reply[:62]) % 256
        self.pending = bytes(reply)
        return 65

    def proof(self):
        return {"schema": "witrn-c5-read-probe-v1", "status": "read_complete_not_a_full_backup",
                "devices": [protocol.json_device(self.descriptor)],
                "regions": {name: {"address": hex(address), "hex": self.flash[address - protocol.FLASH_START:
                    address - protocol.FLASH_START + size].hex()} for name, (address, size) in protocol.REGIONS.items()}}


class BackupTests(unittest.TestCase):
    def run_backup(self, hid, root):
        proof = hid.proof()
        path = root / "proof.json"
        path.write_text(json.dumps(proof))
        args = argparse.Namespace(output_dir=root / "backup", path_hex=None, probe_json=path)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = backup.execute(args, hid, backup.load_proof(path))
        return code, json.loads((args.output_dir / "manifest.json").read_text()), args.output_dir

    def test_full_size_dual_read_and_reverse_order(self):
        hid = SimulatedHid()
        with tempfile.TemporaryDirectory() as directory:
            code, manifest, out = self.run_backup(hid, Path(directory))
            self.assertEqual(code, 0)
            self.assertEqual(manifest["status"], "verified_identical")
            for number in (1, 2):
                self.assertEqual((out / f"flash-pass{number}.bin").read_bytes(), hid.flash)
            start = protocol.FLASH_START
            end = protocol.FLASH_END
            self.assertEqual(hid.addresses[12:12 + 32768], list(range(start, end, 32)))
            self.assertEqual(hid.addresses[12 + 32768:], list(range(end - 32, start - 1, -32)))
            self.assertFalse(manifest["restore_tested"])
            self.assertTrue(hid.closed)

    def test_changed_second_read_is_not_verified(self):
        hid = SimulatedHid(change_second_pass=True)
        with tempfile.TemporaryDirectory() as directory:
            code, manifest, out = self.run_backup(hid, Path(directory))
            self.assertEqual(code, 3)
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["first_difference_address"], "0x8040000")
            self.assertNotEqual((out / "flash-pass1.bin").read_bytes(), (out / "flash-pass2.bin").read_bytes())
            self.assertTrue(all(p["status"] != "verified_identical" for p in manifest["passes"]))

    def test_interrupted_read_preserves_partial_and_stops(self):
        hid = SimulatedHid(fail_after=15)
        with tempfile.TemporaryDirectory() as directory:
            code, manifest, out = self.run_backup(hid, Path(directory))
            self.assertEqual(code, 3)
            self.assertEqual(len(hid.addresses), 16)
            self.assertEqual(manifest["passes"][0]["bytes_read"], 96)
            self.assertEqual((out / "flash-pass1.partial").stat().st_size, 96)
            self.assertFalse((out / "flash-pass1.bin").exists())
            self.assertTrue(hid.closed)

    def test_existing_backup_directory_is_never_reused(self):
        hid = SimulatedHid()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "backup").mkdir()
            (root / "backup/keep.txt").write_text("keep")
            with self.assertRaises(FileExistsError):
                self.run_backup(hid, root)
            self.assertEqual((root / "backup/keep.txt").read_text(), "keep")
            self.assertEqual(hid.addresses, [])


if __name__ == "__main__":
    unittest.main()

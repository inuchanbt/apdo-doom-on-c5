"""Offline checks; no attached hardware is needed or accessed."""
import argparse
import json
from pathlib import Path
import unittest

import c5_probe as probe


class ProbeTests(unittest.TestCase):
    def test_request_matches_actual_vendor_builder(self):
        fixture = json.loads(Path(__file__).with_name("vendor_read_fixture.json").read_text())
        actual = probe.build_read_request(fixture["address"], fixture["count"], fixture["ticks"])
        self.assertEqual(actual.hex(), fixture["frame_hex"])

    def test_rejects_reads_outside_fixed_flash_window_or_packet_capacity(self):
        for address, size in [(0, 16), (0x1FFFF7E8, 16), (0x080FFFF0, 32),
                              (0x08004000, 0), (0x08004000, 33)]:
            with self.subTest(address=address, size=size), self.assertRaises(ValueError):
                probe.build_read_request(address, size, 0)

    def test_reply_validation_and_corruption(self):
        # A valid *synthetic* reply; deliberately not presented as device evidence.
        frame = bytearray(64)
        frame[:2] = b"\xff\x55"
        frame[8:10] = b"\x0a\x04"
        frame[10:14] = b"ABCD"
        frame[62] = 24  # (10 + 4 + 65 + 66 + 67 + 68) modulo 256
        frame[63] = 108  # (255 + 85 + 24) modulo 256
        self.assertEqual(probe.parse_reply(bytes(frame), 4), b"ABCD")
        self.assertEqual(probe.parse_reply(b"\0" + frame, 4), b"ABCD")
        for offset in [0, 1, 8, 9, 10, 61, 62, 63]:
            bad = bytearray(frame)
            bad[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                probe.parse_reply(bytes(bad), 4)
        for data, count in [(frame[:-1], 4), (frame, 3)]:
            with self.assertRaises(ValueError):
                probe.parse_reply(bytes(data), count)

    def test_enumeration_never_opens_a_device(self):
        class Hid:
            def enumerate(self, vid, pid):
                return [{"path": b"test", "vendor_id": vid, "product_id": pid}]
            def device(self):
                raise AssertionError("Enumeration must not open a device")
        report, code = probe.run(argparse.Namespace(read_info=False), Hid())
        self.assertEqual(code, 0)
        self.assertEqual(report["requests"], [])

    def test_ambiguous_devices_never_open(self):
        class Hid:
            def enumerate(self, vid, pid):
                return [{"path": b"a"}, {"path": b"b"}]
            def device(self):
                raise AssertionError("Ambiguous selection must stop")
        report, code = probe.run(argparse.Namespace(read_info=True, dfu=True, path_hex=None), Hid())
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "ambiguous_device")

    def test_timeout_stops_after_one_read_request(self):
        class Device:
            def open_path(self, path): pass
            def close(self): pass
            def read(self, size, timeout): return []
            def write(self, data):
                self.assert_read_only(data)
                return len(data)
            def assert_read_only(self, data):
                if data[0] != 0 or data[9] != 10:
                    raise AssertionError("Unexpected command")
        class Hid:
            def enumerate(self, vid, pid): return [{"path": b"test"}]
            def device(self): return Device()
        report, code = probe.run(argparse.Namespace(read_info=True, dfu=True, path_hex=None), Hid())
        self.assertEqual(code, 3)
        self.assertEqual(len(report["requests"]), 1)
        self.assertIn("TimeoutError", report["error"])


if __name__ == "__main__":
    unittest.main()

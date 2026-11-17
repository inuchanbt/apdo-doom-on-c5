"""Offline package/activation comparison checks; no hardware access."""
from functools import reduce
from operator import xor
import struct
import unittest

import c5_compare as compare


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.payload = bytearray(b"\xff" * 4096)
        struct.pack_into("<II", self.payload, 0, 0x20017D08, 0x08004311)
        self.payload[0x810:0x814] = b"C400"
        header = bytearray(48)
        header[:7] = b"gzutapp"
        header[20:36] = compare.FAMILY
        struct.pack_into("<III", header, 36, len(self.payload), reduce(xor, self.payload, 0), sum(self.payload))
        encode = bytes(compare.DECODE.index(i) for i in range(256))
        self.package = bytes(header + self.payload).translate(encode)
        self.flash = bytearray(b"\xff" * compare.FLASH_BYTES)
        self.flash[0x4000:0x5000] = self.payload

    def test_exact_and_observed_activation_are_distinguished(self):
        exact = compare.compare_dump(self.flash, self.package)
        self.assertTrue(exact["exact_payload_match"])
        self.assertFalse(exact["only_observed_activation_byte_differs"])
        self.flash[0x4C00] = 0xFE
        activated = compare.compare_dump(self.flash, self.package)
        self.assertFalse(activated["exact_payload_match"])
        self.assertTrue(activated["only_observed_activation_byte_differs"])
        self.assertEqual(activated["payload"]["different_bytes"], 1)

    def test_activation_does_not_hide_another_difference(self):
        self.flash[0x4C00] = 0xFE
        self.flash[0x4500] ^= 1
        result = compare.compare_dump(self.flash, self.package)
        self.assertFalse(result["matches_package_with_observed_activation"])

    def test_other_marker_values_are_not_treated_as_matching(self):
        self.flash[0x4C00] = 0xFC
        result = compare.compare_dump(self.flash, self.package)
        self.assertFalse(result["matches_package_with_observed_activation"])

    def test_outside_changes_are_reported_even_when_app_matches(self):
        baseline = bytes(self.flash)
        self.flash[0x3800] ^= 1
        self.flash[0xFF800] ^= 1
        result = compare.compare_dump(self.flash, self.package, baseline)
        self.assertTrue(result["matches_package_with_observed_activation"])
        self.assertFalse(result["all_checked_outside_payload_regions_unchanged"])
        self.assertTrue(result["baseline_regions"]["boot_below_factory_header"]["identical"])
        self.assertEqual(result["baseline_regions"]["factory_header_to_app_start"]["different_bytes"], 1)

    def test_corrupt_package_is_rejected(self):
        bad = bytearray(self.package)
        bad[-1] ^= 1
        with self.assertRaises(ValueError):
            compare.decode_package(bad)


if __name__ == "__main__":
    unittest.main()

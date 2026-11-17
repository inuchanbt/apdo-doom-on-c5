"""Synthetic before/after and refusal checks; no owner flash or USB needed."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import qualify_backup as qb


class QualificationTests(unittest.TestCase):
    def make_backup(self, folder):
        data = bytes(range(256)) * 4096
        for number in (1, 2):
            (folder / f'flash-pass{number}.bin').write_bytes(data)
        (folder / 'manifest.json').write_text(json.dumps(dict(status='verified_identical', sha256=hashlib.sha256(data).hexdigest())))
        return data

    def test_mismatched_bootloader_refused(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            self.make_backup(folder)
            with self.assertRaisesRegex(ValueError, 'Bootloader differs'):
                qb.qualify(folder)

    def test_second_read_must_match(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            self.make_backup(folder)
            (folder / 'flash-pass2.bin').write_bytes(b'\0' * 0x100000)
            with self.assertRaisesRegex(ValueError, 'byte-identical'):
                qb.qualify(folder)

    def test_matching_synthetic_target_and_hash_tampering(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            folder = root / 'backup'
            folder.mkdir()
            data = self.make_backup(folder)
            (root / 'SOURCE_LOCK.json').write_text(json.dumps({'c5': {'boot_prefix_bytes': 0x3800,
                'boot_prefix_sha256': hashlib.sha256(data[:0x3800]).hexdigest()}}))
            with patch.object(qb, 'ROOT', root):
                self.assertTrue(qb.qualify(folder)['matches_target_bootloader'])
                self.assertFalse(qb.qualify(folder)['restore_tested'])
                (folder / 'manifest.json').write_text(json.dumps(dict(status='verified_identical', sha256='bad')))
                with self.assertRaisesRegex(ValueError, 'manifest hash'):
                    qb.qualify(folder)


if __name__ == '__main__':
    unittest.main()

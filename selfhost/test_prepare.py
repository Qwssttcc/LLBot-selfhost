import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import prepare


def archive(entries):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as output:
        for name, data, kind in entries:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.type = kind
            output.addfile(info, io.BytesIO(data) if kind == tarfile.REGTYPE else None)
    return stream.getvalue()


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dest = Path(self.temp.name) / 'out'

    def test_exact_native_members_and_hash(self):
        data = archive([('package/native', b'original', tarfile.REGTYPE)])
        prepare.extract_checked(data, self.dest, {'package/native': hashlib.sha256(b'original').hexdigest()})
        self.assertEqual((self.dest / 'native').read_bytes(), b'original')

    def test_path_traversal_rejected_before_any_write(self):
        data = archive([('package/good', b'a', tarfile.REGTYPE), ('package/../../outside', b'b', tarfile.REGTYPE)])
        with self.assertRaises(ValueError): prepare.extract_checked(data, self.dest)
        self.assertFalse(self.dest.exists())

    def test_symlink_rejected(self):
        with self.assertRaises(ValueError):
            prepare.extract_checked(archive([('package/link', b'', tarfile.SYMTYPE)]), self.dest)

    def test_duplicate_member_rejected(self):
        with self.assertRaises(ValueError):
            prepare.extract_checked(archive([('package/a', b'1', tarfile.REGTYPE), ('package/a', b'2', tarfile.REGTYPE)]), self.dest)

    def test_missing_native_member_rejected(self):
        with self.assertRaises(ValueError):
            prepare.extract_checked(archive([('package/a', b'1', tarfile.REGTYPE)]), self.dest, {'package/b': '0' * 64})

    def test_changed_native_binary_rejected(self):
        with self.assertRaises(ValueError):
            prepare.extract_checked(archive([('package/a', b'changed', tarfile.REGTYPE)]), self.dest, {'package/a': '0' * 64})
        self.assertFalse(self.dest.exists())

    def test_corrupted_cache_rejected(self):
        old_root, old_manifest = prepare.ROOT, prepare.MANIFEST
        try:
            prepare.ROOT = Path(self.temp.name)
            prepare.MANIFEST = {'artifacts': {'test': {'cache_file': 'bad.tgz', 'sha256': '0' * 64}}}
            cache = prepare.ROOT / 'selfhost/cache/bad.tgz'
            cache.parent.mkdir(parents=True)
            cache.write_bytes(b'bad')
            with self.assertRaises(ValueError): prepare.fetch('test')
        finally:
            prepare.ROOT, prepare.MANIFEST = old_root, old_manifest

if __name__ == '__main__':
    unittest.main()

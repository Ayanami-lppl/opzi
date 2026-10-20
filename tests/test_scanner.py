import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scanner import Scanner


class ScannerTests(unittest.TestCase):
    def finish(self, scanner):
        deadline = time.monotonic() + 5
        while scanner.status()['state'] == 'scanning' and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertNotEqual(scanner.status()['state'], 'scanning')

    def test_sizes_relationships_hidden_search_and_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'nested').mkdir()
            (p / 'empty').mkdir()
            (p / 'nested' / 'large.dat').write_bytes(b'x' * 900)
            (p / '.hidden').write_bytes(b'y' * 100)
            scanner = Scanner()
            scanner.start(tmp)
            self.finish(scanner)
            root = scanner.node(str(p.resolve()))
            self.assertEqual(root['size'], 1000)
            self.assertEqual(root['total_children'], 3)
            large = scanner.search('LARGE')[0]
            detail = scanner.node(large['id'])
            self.assertEqual(detail['parent_size'], 900)
            self.assertEqual(detail['root_size'], 1000)
            self.assertEqual(len(detail['breadcrumbs']), 3)
            self.assertTrue(scanner.search('.hidden')[0]['hidden'])
            self.assertEqual(scanner.status()['files'], 2)
            self.assertEqual(scanner.node(str(p / 'empty'))['size'], 0)

    def test_invalid_path_and_file_rejected(self):
        scanner = Scanner()
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'file'
            file.touch()
            with self.assertRaises(ValueError):
                scanner.start(file)
            with self.assertRaises(FileNotFoundError):
                scanner.start(Path(tmp) / 'missing')

    def test_cancel_keeps_coherent_totals(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(100):
                p = Path(tmp) / str(i)
                p.mkdir()
                (p / 'a').write_bytes(b'x' * 10)
            scanner = Scanner()
            scanner.start(tmp)
            scanner.cancel_event.set()
            self.finish(scanner)
            with scanner.lock:
                leaf_total = sum(n['size'] for n in scanner.nodes.values() if not n['directory'])
            self.assertEqual(scanner.status()['size'], leaf_total)
            self.assertEqual(scanner.status()['state'], 'cancelled')

    def test_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'data').write_bytes(b'x' * 42)
            try:
                os.symlink(p, p / 'loop', target_is_directory=True)
            except OSError:
                self.skipTest('当前系统不允许创建符号链接')
            scanner = Scanner()
            scanner.start(tmp)
            self.finish(scanner)
            self.assertEqual(scanner.status()['size'], 42)
            self.assertEqual(scanner.status()['skipped'], 1)


if __name__ == '__main__':
    unittest.main()

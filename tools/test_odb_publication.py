"""Verify blocked publication cannot write misleading canonical artifacts."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from odb_scaffold import ROOT


class ODBScaffoldPublicationTests(unittest.TestCase):
    def test_generation_and_check_fail_closed_without_output(self):
        for flags in ([], ['--check']):
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'publication'
                result = subprocess.run(
                    [sys.executable, str(ROOT / 'tools/generate_odb_publication.py'),
                     '--root', str(ROOT), '--output-dir', str(output), *flags],
                    capture_output=True, text=True, check=False)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn('HANDOFF BLOCKED', result.stderr)
                self.assertFalse(output.exists())

    def test_no_published_odb_artifacts(self):
        directory = ROOT / 'generated/obchodne-pripady'
        self.assertFalse(directory.exists())


if __name__ == '__main__':
    unittest.main()

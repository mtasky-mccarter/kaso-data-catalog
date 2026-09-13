"""Scaffold SQL gate: no diagnostic SQL is approved yet; no DB execution."""
import unittest

from odb_scaffold import ROOT, read_scaffold


class ODBScaffoldSQLSafetyTests(unittest.TestCase):
    def test_no_unapproved_sql_or_registry_entries(self):
        self.assertEqual([], read_scaffold()['sql-registry.yaml']['records'])
        directory = ROOT / 'sql/diagnostic/obchodne-pripady'
        self.assertTrue(directory.is_dir())
        self.assertEqual([], [p for p in directory.rglob('*') if p.is_file()
                              and p.name != 'README.md'])


if __name__ == '__main__':
    unittest.main()

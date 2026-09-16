"""Offline read-only and lossless SQL gate; no Oracle execution."""
import json
import re
import unittest
from odb_scaffold import ROOT
from validate_catalog import load_yaml

class ODBSQLSafetyTests(unittest.TestCase):
    def test_approved_sql_differs_only_by_whitespace(self):
        source=json.loads((ROOT/'evidence/source-extracts/odb/approved-contract.json').read_text())
        docs=load_yaml(ROOT/'catalog/sales/obchodne-pripady/sql-registry.yaml')['records']
        self.assertEqual(20,len(docs))
        for r in docs:
            block,part=map(int,r['sql_id'].removeprefix('odb.sql.doc_').split('_'))
            raw=source[block]['rows'][0][0].split(';')[part-1]+';'
            sql=(ROOT/r['sql_file']).read_text()
            self.assertEqual(re.sub(r'\s','',raw),re.sub(r'\s','',sql))
            self.assertTrue(sql.startswith('SELECT '))
            self.assertEqual(1,sql.count(';'))
            self.assertIsNone(re.search(r'\b(INSERT|UPDATE|DELETE|MERGE|ALTER|DROP|CREATE|TRUNCATE|EXECUTE|BEGIN|COMMIT|GRANT)\b',sql,re.I))
            self.assertIsNone(re.search(r'\b(FETCH FIRST|OFFSET|MATCH_RECOGNIZE)\b',sql,re.I))
            self.assertIn('\nFROM ',sql)

if __name__=='__main__':unittest.main()

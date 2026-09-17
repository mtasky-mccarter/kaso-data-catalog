"""Read-only SQL acceptance; never runs SQL against Oracle."""
import re
import unittest
from pathlib import Path
import yaml
from test_vyd_sql_safety import strip_comments_and_literals, FORBIDDEN, FOR_UPDATE

ROOT=Path(__file__).resolve().parents[1]

class ProductMasterSqlSafetyTests(unittest.TestCase):
    def test_every_registered_statement_is_read_only_and_documented(self):
        records=yaml.safe_load((ROOT/'catalog/master/skladove-karty/sql-registry.yaml').read_text())['records']
        self.assertGreaterEqual(len(records),25)
        paths=set()
        for r in records:
            paths.add(r['sql_file']);text=(ROOT/r['sql_file']).read_text()
            for marker in ['-- Scope:','-- Grain:','-- Fan-out:','-- Proves:','-- Does not prove:']:self.assertIn(marker,text)
            clean=strip_comments_and_literals(text)
            for statement in clean.split(';'):
                if statement.strip():self.assertRegex(statement.strip(),r'^(SELECT|WITH)\b')
            self.assertIsNone(FORBIDDEN.search(clean),r['sql_id'])
            self.assertIsNone(FOR_UPDATE.search(clean),r['sql_id'])
            self.assertIsNone(re.search(r'\b(?:EXECUTE|UTL_HTTP|DBMS_|SETC_FNCSESSION|GETX|FETCH\s+FIRST|OFFSET)\b',clean,re.I),r['sql_id'])
            for key in ['result_grain_sk','fanout_warning_sk','proves_sk','does_not_prove_sk']:self.assertTrue(r[key])
            self.assertIsNone(r['compatibility']['oracle_server_version'])
        self.assertEqual(paths,{p.relative_to(ROOT).as_posix() for p in (ROOT/'sql/diagnostic/skladove-karty').glob('*.sql')})

    def test_bom_and_report_limits_are_executable(self):
        bom=(ROOT/'sql/diagnostic/skladove-karty/bom-audit.sql').read_text()
        for s in ['FULL OUTER JOIN','NULL_INPUT_ROWS','TOKEN_POSITION','DU_8','DU_9','HMOTNOST_NETTO','COMPONENT_COUNT']:self.assertIn(s,bom)
        report=(ROOT/'sql/diagnostic/skladove-karty/recycling-reconciliation.sql').read_text()
        for s in ['TONY_ALL','TONY_FLAG12_OK','TONY_OTHER_OR_NULL',":market='CZ'",'date_to_exclusive']:self.assertIn(s,report)
        self.assertNotIn('SETC_FNCSESSION',report.upper())

if __name__=='__main__':unittest.main()

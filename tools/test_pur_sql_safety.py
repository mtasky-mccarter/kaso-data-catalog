"""Conservative offline purchasing SQL safety and semantic regressions."""
import re
import unittest
from validate_catalog import ROOT, load_yaml

SQL = ROOT / 'sql/diagnostic/purchasing'


def executable(text):
    text = re.sub(r'--[^\n]*|/\*.*?\*/', ' ', text, flags=re.S)
    return re.sub(r"'(?:''|[^'])*'", "''", text).upper()


class PurchasingSQLSafety(unittest.TestCase):
    def test_only_conservative_selects(self):
        registry = load_yaml(ROOT / 'catalog/purchasing/sql-registry.yaml')['records']
        self.assertEqual({p.name for p in SQL.glob('*.sql')}, {r['sql_file'].split('/')[-1] for r in registry})
        for r in registry:
            text = (ROOT / r['sql_file']).read_text()
            code = executable(text)
            self.assertTrue(all(s.strip().startswith('SELECT') for s in code.split(';') if s.strip()))
            self.assertIsNone(re.search(r'\b(INSERT|UPDATE|DELETE|MERGE|ALTER|DROP|TRUNCATE|CREATE|GRANT|REVOKE|EXECUTE|BEGIN|DECLARE|COMMIT|ROLLBACK)\b', code))
            self.assertIsNone(re.search(r'\b(MCCZ|TEST|TESTCZ|MC_WWW)\.', code))
            self.assertIsNone(re.search(r'FETCH\s+FIRST|MATCH_RECOGNIZE|\bAPPLY\b|\bPIVOT\b|\bOFFSET\b', code))
            # Only approved MC SQL-callable getter, no accidental mutating package calls.
            calls = re.findall(r'\bMC\.([A-Z_]+)\.([A-Z_]+)\s*\(', code)
            self.assertTrue(all(pair == ('D_OBJD_L', 'GETS_STAV') for pair in calls))
            for key in ('result_grain_sk', 'proves_sk', 'does_not_prove_sk', 'fanout_warning_sk'):
                self.assertTrue(r.get(key))

    def test_receipts_preaggregated_and_subtype_resolved(self):
        for name in ('pl_receipt', 'p_prij_lineage'):
            sql = (SQL / (name + '.sql')).read_text()
            self.assertIn('GROUP BY R.RID_V', sql)
            self.assertIn("L.TYP_CIS = '00029'", sql)
            self.assertNotIn("LIKE '020%'", sql)
        overdue = (SQL / 'overdue.sql').read_text()
        self.assertIn('NVL(O.TERMIN_DOD, NVL(L.TERMIN_DOD, L.DATUM_P)) < :p_as_of_date', overdue)
        self.assertIn('O.POCET - O.P_DEL - O.P_PRIJ - O.P_PL > 0', overdue)
        self.assertIn('MC.D_OBJD_L.GetS_STAV(L.FLAGS_S)', overdue)


if __name__ == '__main__':
    unittest.main()

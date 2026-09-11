"""Conservative read-only safety gate for canonical VYD SQL."""
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "catalog/warehouse/vydajky/sql-registry.yaml"
FORBIDDEN = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|"
    r"COMMIT|ROLLBACK|EXECUTE|EXEC|BEGIN|DECLARE)\b", re.IGNORECASE)
FOR_UPDATE = re.compile(r"\bFOR\s+UPDATE\b", re.IGNORECASE)


def strip_comments_and_literals(sql):
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\r\n]*", " ", sql)
    return re.sub(r"'(?:''|[^'])*'", "''", sql, flags=re.DOTALL)


class VYDSqlSafetyTests(unittest.TestCase):
    def test_all_vyd_canonical_sql_is_select_only(self):
        records = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["records"]
        self.assertEqual(8, len(records))
        for record in records:
            clean = strip_comments_and_literals((ROOT / record["sql_file"]).read_text(encoding="utf-8")).strip()
            first = re.match(r"([A-Za-z]+)", clean)
            self.assertIsNotNone(first, record["sql_id"])
            self.assertIn(first.group(1).upper(), {"SELECT", "WITH"}, record["sql_id"])
            self.assertIsNone(FORBIDDEN.search(clean), record["sql_id"])
            self.assertIsNone(FOR_UPDATE.search(clean), record["sql_id"])
            self.assertTrue(record["compatibility"]["read_only"])


if __name__ == "__main__":
    unittest.main()

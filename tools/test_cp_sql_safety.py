"""Conservative read-only lint for canonical CP diagnostic SQL.

This is a safety gate, not an Oracle parser and not proof of JOIN/business truth.
It rejects obvious mutating/DDL/PLSQL constructs after stripping comments and
string literals, and requires every canonical statement to begin with SELECT or
WITH. Oracle server-version compatibility remains separately unverified.
"""
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "catalog/transport/cestovne-prikazy/sql-registry.yaml"

FORBIDDEN = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|"
    r"COMMIT|ROLLBACK|EXECUTE|EXEC|BEGIN|DECLARE)\b",
    re.IGNORECASE,
)
FOR_UPDATE = re.compile(r"\bFOR\s+UPDATE\b", re.IGNORECASE)


def strip_comments_and_literals(sql):
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\r\n]*", " ", sql)
    # Oracle escaped quotes use doubled single quotes; q'[...]' is not expected
    # in the current diagnostic toolkit. Replacing normal literals is enough for
    # a conservative gate; any remaining mutating keyword is rejected.
    sql = re.sub(r"'(?:''|[^'])*'", "''", sql, flags=re.DOTALL)
    return sql


class CPSqlSafetyTests(unittest.TestCase):
    def test_all_canonical_sql_is_select_only(self):
        registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["records"]
        self.assertEqual(11, len(registry))
        for record in registry:
            path = ROOT / record["sql_file"]
            sql = path.read_text(encoding="utf-8")
            clean = strip_comments_and_literals(sql).strip()
            first = re.match(r"([A-Za-z]+)", clean)
            self.assertIsNotNone(first, record["sql_id"])
            self.assertIn(first.group(1).upper(), {"SELECT", "WITH"}, record["sql_id"])
            match = FORBIDDEN.search(clean)
            self.assertIsNone(match, f"{record['sql_id']}: forbidden token {match.group(0) if match else ''}")
            self.assertIsNone(FOR_UPDATE.search(clean), f"{record['sql_id']}: SELECT FOR UPDATE is not read-only")
            self.assertTrue(record["compatibility"]["read_only"], record["sql_id"])


if __name__ == "__main__":
    unittest.main()

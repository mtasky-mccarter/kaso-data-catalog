"""Publication provenance, completeness and deterministic rendering regressions."""
import hashlib
import re
import subprocess
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import yaml

from generate_publication import PUBLICATIONS, current_version, publication_basename
from generate_odb_publication import FONT_DIR, blocks, model, registry_parts, value_text
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated/obchodne-pripady"
BASENAME = "KASO Data Catalog - Technical & Diagnostic Reference - obchodné prípady v1.2"


def normalized(text):
    return re.sub(r"\s+", "", text.replace("\u200b", ""))


class ODBPublicationTests(unittest.TestCase):
    def test_identity_version_digest_and_artifact_hashes(self):
        manifest = yaml.safe_load((GENERATED / (BASENAME + ".manifest.yaml")).read_text())
        self.assertEqual("odb.contract.obchodne_pripady", manifest["contract_ref"])
        self.assertEqual("1.2", manifest["contract_version"])
        self.assertEqual("1.0", manifest["publication_layout_version"])
        self.assertEqual("obchodne-pripady", manifest["publication_slug"])
        self.assertEqual(BASENAME, manifest["publication_title"])
        self.assertEqual("tools/generate_publication.py", manifest["publication_orchestrator"])
        self.assertEqual("obchodné prípady", PUBLICATIONS["obchodne-pripady"]["subject_sk"])
        self.assertEqual(BASENAME, publication_basename(PUBLICATIONS["obchodne-pripady"], current_version(ROOT, PUBLICATIONS["obchodne-pripady"])))
        paths = (sorted((ROOT / "catalog/sales/obchodne-pripady").glob("*.yaml"))
                 + sorted((ROOT / "sql/diagnostic/obchodne-pripady").glob("*.sql"))
                 + sorted((ROOT / "evidence/manifests/odb").glob("*.yaml")))
        digest = hashlib.sha256()
        for path in paths:
            digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0")
            digest.update(path.read_bytes() + b"\0")
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in paths], manifest["canonical_inputs"])
        self.assertEqual(digest.hexdigest(), manifest["canonical_input_sha256"])
        expected = {f"generated/obchodne-pripady/{BASENAME}{ext}" for ext in (".docx", ".pdf")}
        self.assertEqual(expected, {r["path"] for r in manifest["artifacts"]})
        for artifact in manifest["artifacts"]:
            path = ROOT / artifact["path"]
            self.assertEqual(artifact["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertTrue((GENERATED / (BASENAME + ".docx")).read_bytes().startswith(b"PK"))
        self.assertTrue((GENERATED / (BASENAME + ".pdf")).read_bytes().startswith(b"%PDF"))

    def test_complete_canonical_values_and_sql_reach_docx(self):
        data = model(ROOT)
        with ZipFile(GENERATED / (BASENAME + ".docx")) as archive:
            xml = ET.fromstring(archive.read("word/document.xml"))
        text = normalized("".join(xml.itertext()))

        def assert_leaves(value):
            if isinstance(value, dict):
                for child in value.values():
                    assert_leaves(child)
            elif isinstance(value, list):
                for child in value:
                    assert_leaves(child)
            else:
                self.assertIn(normalized(value_text(value)), text, repr(value))

        for name, doc in data["docs"].items():
            if name.startswith(("api-references", "dependency-", "oracle-entities")):
                continue
            assert_leaves(doc)
        for sql in data["sql"].values():
            self.assertIn(normalized(sql), text)
        self.assertEqual(123, sum(len(d["records"]) for n, d in data["docs"].items() if n.startswith("fields-")))
        self.assertEqual(20, len(data["sql"]))
        self.assertEqual(8, len(data["docs"]["playbooks.yaml"]["records"]))
        self.assertEqual(4515, sum(len(d["records"]) for n,d in data["docs"].items() if n.startswith("api-references")))

    def test_publication_gate_rejects_missing_readiness(self):
        from unittest.mock import patch
        from odb_scaffold import publication_blockers
        docs = {"contract.yaml": {"maturity":"DIAGNOSTIC-GRADE"},
                "object-obj_odb_l.yaml": {"maturity":"AGENT-READY"},
                "object-obj_odb_o.yaml": {"maturity":"AGENT-READY"},
                "backlog.yaml": {"records":[]}, "revisions.yaml": {"records":[]}}
        with patch("odb_scaffold.read_scaffold", return_value=docs):
            reasons=publication_blockers(ROOT)
        self.assertEqual(2, len(reasons))

    def test_factoring_preserves_record_values_and_absence(self):
        rows = [{"id": "a", "nullable": None, "raw_value": "00028", "status": "TECHNICKY ZNÁME"},
                {"id": "b", "raw_value": "00029", "status": "TECHNICKY ZNÁME"}]
        shared, unique = registry_parts(rows)
        self.assertNotIn("nullable", shared)
        self.assertEqual(rows, [dict(shared, **r) for r in unique])
        for document in model(ROOT)["docs"].values():
            records = document.get("records", [])
            shared, unique = registry_parts(records)
            self.assertEqual(records, [dict(shared, **r) for r in unique])

    def test_publication_is_deterministically_current(self):
        subprocess.run([sys.executable, str(ROOT / "tools/generate_publication.py"), "obchodne-pripady", "--check"], cwd=ROOT, check=True)

    def test_pdf_fonts_cover_all_canonical_characters(self):
        characters = set(str(blocks(model(ROOT))))
        for path in FONT_DIR.glob("*.ttf"):
            font = TTFont(path.stem, path)
            self.assertEqual([], sorted(c for c in characters if ord(c) > 32 and ord(c) not in font.face.charToGlyph))


if __name__ == "__main__":
    unittest.main()

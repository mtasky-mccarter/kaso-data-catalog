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
from generate_pur_publication import FONT_DIR, blocks, model, registry_parts, value_text
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated/purchasing"
BASENAME = "KASO Data Catalog - Technical & Diagnostic Reference - nákupný lifecycle od návrhu po receiving boundary v1.0"


def normalized(text):
    return re.sub(r"\s+", "", text.replace("\u200b", ""))


class PurchasingPublicationTests(unittest.TestCase):
    def test_identity_version_digest_and_artifact_hashes(self):
        manifest = yaml.safe_load((GENERATED / (BASENAME + ".manifest.yaml")).read_text())
        self.assertEqual("pur.contract.purchasing.1_0", manifest["contract_ref"])
        self.assertEqual("1.0", manifest["contract_version"])
        self.assertEqual("1.0", manifest["publication_layout_version"])
        self.assertEqual("purchasing", manifest["publication_slug"])
        self.assertEqual(BASENAME, manifest["publication_title"])
        self.assertEqual("tools/generate_publication.py", manifest["publication_orchestrator"])
        contract = yaml.safe_load((ROOT / "catalog/purchasing/contract.yaml").read_text())
        self.assertEqual(contract["title_sk"].lower(), PUBLICATIONS["purchasing"]["subject_sk"])
        self.assertEqual(BASENAME, publication_basename(PUBLICATIONS["purchasing"], current_version(ROOT, PUBLICATIONS["purchasing"])))
        paths = (sorted((ROOT / "catalog/purchasing").glob("*.yaml"))
                 + sorted((ROOT / "sql/diagnostic/purchasing").glob("*.sql"))
                 + sorted((ROOT / "evidence/manifests/pur").glob("*.yaml")))
        digest = hashlib.sha256()
        for path in paths:
            digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0")
            digest.update(path.read_bytes() + b"\0")
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in paths], manifest["canonical_inputs"])
        self.assertEqual(digest.hexdigest(), manifest["canonical_input_sha256"])
        expected = {f"generated/purchasing/{BASENAME}{ext}" for ext in (".docx", ".pdf")}
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

        for doc in list(data["docs"].values()) + list(data["evidence"].values()):
            assert_leaves(doc)
        for sql in data["sql"].values():
            self.assertIn(normalized(sql), text)
        self.assertEqual(328, sum(len(d["records"]) for n, d in data["docs"].items() if n.startswith("fields-")))
        self.assertEqual(10, len(data["sql"]))
        self.assertEqual(7, len(data["docs"]["playbooks.yaml"]["records"]))
        self.assertEqual(700, len(data["docs"]["api-references.yaml"]["records"]))

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
        subprocess.run([sys.executable, str(ROOT / "tools/generate_publication.py"), "purchasing", "--check"], cwd=ROOT, check=True)

    def test_pdf_fonts_cover_all_canonical_characters(self):
        characters = set(str(blocks(model(ROOT))))
        for path in FONT_DIR.glob("*.ttf"):
            font = TTFont(path.stem, path)
            self.assertEqual([], sorted(c for c in characters if ord(c) > 32 and ord(c) not in font.face.charToGlyph))


if __name__ == "__main__":
    unittest.main()

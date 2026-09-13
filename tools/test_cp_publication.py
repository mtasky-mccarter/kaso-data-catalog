"""Checks that CP v1.1 publications are reproducible from canonical inputs."""
from pathlib import Path
import hashlib
import subprocess
import sys
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated" / "cestovne-prikazy"
DOMAIN = ROOT / "catalog/transport/cestovne-prikazy"
SQL_DIR = ROOT / "sql/diagnostic/cestovne-prikazy"
BASENAME = "KASO Data Catalog - Technical & Diagnostic Reference - cestovné príkazy v1.1"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest():
    digest = hashlib.sha256()
    paths = sorted(DOMAIN.glob("*.yaml")) + sorted(SQL_DIR.glob("*.sql"))
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


class CPV11PublicationTests(unittest.TestCase):
    def test_manifest_provenance_and_artifact_hashes(self):
        manifest = yaml.safe_load(
            (GENERATED / f"{BASENAME}.manifest.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual("mtasky-mccarter/kaso-data-catalog", manifest["repository"])
        self.assertEqual("main", manifest["canonical_branch"])
        self.assertEqual("cp.contract.cestovne_prikazy.1_1", manifest["contract_ref"])
        self.assertEqual("1.1", manifest["contract_version"])
        self.assertEqual("1.0", manifest["publication_layout_version"])
        self.assertEqual("cestovne-prikazy", manifest["publication_slug"])
        self.assertEqual(BASENAME, manifest["publication_title"])
        self.assertEqual(canonical_digest(), manifest["canonical_input_sha256"])
        for artifact in manifest["artifacts"]:
            path = ROOT / artifact["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(artifact["sha256"], sha256(path))
        self.assertTrue((GENERATED / f"{BASENAME}.docx").read_bytes().startswith(b"PK"))
        self.assertTrue((GENERATED / f"{BASENAME}.pdf").read_bytes().startswith(b"%PDF"))

    def test_publications_are_deterministically_current(self):
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/generate_publication.py"),
                "cestovne-prikazy",
                "--check",
            ],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()

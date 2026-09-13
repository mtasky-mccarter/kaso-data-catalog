"""Repository-level checks for generated publication naming and folder layout."""
from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"
PREFIX = "KASO Data Catalog - Technical & Diagnostic Reference - "
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSIONED_BASENAME_RE = re.compile(r"^KASO Data Catalog - Technical & Diagnostic Reference - .+ v\d+\.\d+$")


class PublicationLayoutTests(unittest.TestCase):
    def test_no_flat_generated_publications(self):
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in GENERATED.iterdir()
            if path.is_file() and (
                path.suffix.lower() in {".docx", ".pdf"} or path.name.endswith(".manifest.yaml")
            )
        ]
        self.assertEqual([], offenders, f"Generated publications must live in per-document folders: {offenders}")

    def test_publication_directories_and_filenames(self):
        for directory in sorted(path for path in GENERATED.iterdir() if path.is_dir()):
            with self.subTest(directory=directory.name):
                self.assertRegex(directory.name, SLUG_RE)
                files = [path for path in directory.iterdir() if path.is_file()]
                self.assertTrue(files, f"Empty generated publication directory: {directory}")
                for path in files:
                    if path.name.endswith(".manifest.yaml"):
                        basename = path.name[:-len(".manifest.yaml")]
                    else:
                        self.assertIn(path.suffix.lower(), {".docx", ".pdf"}, path)
                        basename = path.stem
                    self.assertTrue(basename.startswith(PREFIX), path)
                    self.assertRegex(basename, VERSIONED_BASENAME_RE)

    def test_manifest_paths_are_colocated_and_named_consistently(self):
        for manifest_path in sorted(GENERATED.glob("*/*.manifest.yaml")):
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            directory = manifest_path.parent
            basename = manifest_path.name[:-len(".manifest.yaml")]
            with self.subTest(manifest=manifest_path.name):
                self.assertEqual(directory.name, manifest.get("publication_slug"))
                self.assertEqual(basename, manifest.get("publication_title"))
                self.assertEqual("1.0", str(manifest.get("publication_layout_version")))
                expected_prefix = (Path("generated") / directory.name).as_posix() + "/"
                for artifact in manifest.get("artifacts", []):
                    artifact_path = artifact["path"]
                    self.assertTrue(artifact_path.startswith(expected_prefix), artifact_path)
                    resolved = ROOT / artifact_path
                    self.assertTrue(resolved.is_file(), resolved)
                    self.assertEqual(directory, resolved.parent)
                    self.assertTrue(resolved.name.startswith(basename + "."), resolved)


if __name__ == "__main__":
    unittest.main()

"""Repository layout guards for canonical catalog and evidence locations."""
from pathlib import Path
import unittest

from validate_catalog import ROOT


class RepositoryLayoutTests(unittest.TestCase):
    def test_no_evidence_manifests_at_evidence_root(self):
        evidence_root = ROOT / "evidence"
        stray = sorted(
            p.relative_to(ROOT).as_posix()
            for pattern in ("*.yaml", "*.yml")
            for p in evidence_root.glob(pattern)
        )
        self.assertEqual(
            [],
            stray,
            "Evidence manifests belong under evidence/manifests; top-level YAML is not canonical",
        )


if __name__ == "__main__":
    unittest.main()

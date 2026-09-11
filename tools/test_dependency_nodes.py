"""Consistency checks for dependency closure node registries."""
import copy
import unittest

from validate_catalog import ROOT, load_yaml


def summary_errors(document):
    if document.get("kind") != "dependency-nodes":
        return []
    records = document.get("records", [])
    inbound = [r for r in records if r.get("direction") == "INBOUND"]
    outbound = [r for r in records if r.get("direction") == "OUTBOUND"]
    actual = {
        "record_count": len(records),
        "inbound_count": len(inbound),
        "outbound_count": len(outbound),
        "max_inbound_depth": max((r.get("min_depth", 0) for r in inbound), default=0),
        "max_outbound_depth": max((r.get("min_depth", 0) for r in outbound), default=0),
    }
    declared = document.get("summary", {})
    return [f"{key}: declared {declared.get(key)!r}, actual {value!r}"
            for key, value in actual.items() if declared.get(key) != value]


class DependencyNodeTests(unittest.TestCase):
    def test_synthetic_summary_matches_records(self):
        doc = load_yaml(ROOT / "examples/schema-smoke-test/dependency-nodes.yaml")
        self.assertEqual([], summary_errors(doc))

    def test_summary_mismatch_is_detected(self):
        doc = copy.deepcopy(load_yaml(ROOT / "examples/schema-smoke-test/dependency-nodes.yaml"))
        doc["summary"]["inbound_count"] += 1
        self.assertTrue(summary_errors(doc))

    def test_all_catalog_dependency_node_summaries(self):
        errors = []
        for path in (ROOT / "catalog").rglob("*.yaml"):
            errors.extend(f"{path.relative_to(ROOT)}: {e}"
                          for e in summary_errors(load_yaml(path)))
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()

"""Consistency checks for raw ALL_DEPENDENCIES closure documents."""
from collections import Counter
import copy
from pathlib import Path
import unittest

from validate_catalog import ROOT, load_yaml


def summary_errors(document):
    if document.get('kind') != 'dependency-edges':
        return []
    records = document.get('records', [])
    counts = Counter(r.get('direction') for r in records)
    inbound_depths = [r.get('min_depth', 0) for r in records if r.get('direction') == 'INBOUND']
    outbound_depths = [r.get('min_depth', 0) for r in records if r.get('direction') == 'OUTBOUND']
    actual = {
        'record_count': len(records),
        'inbound_count': counts['INBOUND'],
        'outbound_count': counts['OUTBOUND'],
        'max_inbound_depth': max(inbound_depths, default=0),
        'max_outbound_depth': max(outbound_depths, default=0),
    }
    declared = document.get('summary', {})
    return [f'{key}: declared {declared.get(key)!r}, actual {value!r}'
            for key, value in actual.items() if declared.get(key) != value]


class DependencyEdgeTests(unittest.TestCase):
    def test_synthetic_summary_matches_records(self):
        path = ROOT / 'examples/schema-smoke-test/dependency-edges.yaml'
        doc = load_yaml(path)
        self.assertEqual([], summary_errors(doc))

    def test_summary_mismatch_is_detected(self):
        path = ROOT / 'examples/schema-smoke-test/dependency-edges.yaml'
        doc = copy.deepcopy(load_yaml(path))
        doc['summary']['record_count'] += 1
        self.assertTrue(summary_errors(doc))

    def test_all_catalog_dependency_edge_summaries(self):
        errors = []
        for path in (ROOT / 'catalog').rglob('*.yaml'):
            doc = load_yaml(path)
            errors.extend(f'{path.relative_to(ROOT)}: {e}' for e in summary_errors(doc))
        self.assertEqual([], errors)


if __name__ == '__main__':
    unittest.main()

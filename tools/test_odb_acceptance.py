"""Scaffold invariants only; passing is NOT production/semantic acceptance."""
import unittest

from odb_scaffold import read_scaffold


class ODBScaffoldAcceptanceTests(unittest.TestCase):
    def test_schema_references_and_complete_scaffold_surface(self):
        docs = read_scaffold()
        expected = {
            'contract', 'constraints', 'indexes', 'relationships', 'value-domains',
            'flows', 'mutations', 'temporal', 'data-quality', 'do-not-assume',
            'playbooks', 'backlog', 'revisions', 'oracle-entities', 'sql-registry',
            'dependencies', 'dependency-direct-edges', 'dependency-closure-edges',
            'dependency-closure-nodes', 'api-references',
            'object-obj_odb_l', 'object-obj_odb_o', 'fields-obj_odb_l', 'fields-obj_odb_o',
        }
        self.assertEqual({name + '.yaml' for name in expected}, set(docs))
        self.assertEqual('DISCOVERY', docs['contract.yaml']['maturity'])
        for name in ('obj_odb_l', 'obj_odb_o'):
            obj = docs[f'object-{name}.yaml']
            self.assertEqual(name.upper(), obj['oracle_name'])
            self.assertEqual('MC', obj['oracle_owner'])
            self.assertEqual('DISCOVERY', obj['maturity'])
            self.assertEqual('TREBA OVERIŤ', obj['status'])
            self.assertEqual([], obj['evidence_refs'])
            for key in ('grain_sk', 'identity_refs', 'business_object_sk',
                        'source_of_truth_summary_sk', 'temporal_summary_sk'):
                self.assertNotIn(key, obj)

    def test_unmaterialized_inventory_is_not_evidence(self):
        docs = read_scaffold()
        for name, doc in docs.items():
            if 'records' in doc and name not in ('backlog.yaml', 'do-not-assume.yaml'):
                self.assertEqual([], doc['records'], name)
            if 'summary' in doc:
                self.assertEqual({0}, set(doc['summary'].values()), name)
                source = doc.get('source_dataset', doc.get('source_view', ''))
                self.assertIn('HANDOFF BLOCKED', source)

    def test_required_handoff_gaps_remain_blocking(self):
        records = read_scaffold()['backlog.yaml']['records']
        self.assertEqual({f'odb.backlog.{suffix}' for suffix in
                          ('handoff', 'physical', 'semantics', 'source', 'evidence',
                           'diagnostics', 'acceptance')}, {r['backlog_id'] for r in records})
        for row in records:
            self.assertTrue(row['blocking'])
            self.assertEqual('DATA GAP', row['status'])
            self.assertIn('HANDOFF BLOCKED', row['question_sk'])
            self.assertTrue(row['closure_condition_sk'])


if __name__ == '__main__':
    unittest.main()

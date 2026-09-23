"""Approved alias delta: exact naming, unchanged semantics, safe replay."""
import copy
import hashlib
import json
import unittest

import yaml
from apply_pm_aliases import ROOT, DOMAIN, DELTA, CSV_NAME, REVISION, load_dictionary, apply_records


class ProductMasterAliasTests(unittest.TestCase):
    def setUp(self):
        self.fields = yaml.safe_load((ROOT / DOMAIN / 'fields-sklad_karta.yaml').read_text())['records']
        self.rows = load_dictionary(ROOT / DELTA / CSV_NAME)

    def test_exact_approved_mapping_and_basis(self):
        self.assertEqual(169, len(self.rows))
        self.assertEqual(169, len({r['canonical_alias'] for r in self.rows}))
        self.assertEqual(40, sum(r['alias_basis'] == 'TECHNICAL_NEUTRAL' for r in self.rows))
        self.assertEqual({r['oracle_name']:r['canonical_alias'] for r in self.rows},
                         {r['oracle_name']:r['canonical_alias'] for r in self.fields})
        apply_records(copy.deepcopy(self.fields), self.rows)

    def test_every_non_alias_property_matches_pre_delta_main(self):
        # Verified main 075ab49803d7953540cc2d433afec1afceb6f4cd, aliases excluded.
        data = [{k:v for k,v in r.items() if k != 'canonical_alias'} for r in self.fields]
        digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        self.assertEqual('5b630e33eead79de2363de9f77f277b3622c5075d750fd73a9174f46fd2ea1c7', digest)

    def test_initial_application_and_replay_are_idempotent(self):
        fields = copy.deepcopy(self.fields)
        for field in fields: field['canonical_alias'] = None
        apply_records(fields, self.rows)
        self.assertEqual(self.fields, fields)
        apply_records(fields, self.rows)
        self.assertEqual(self.fields, fields)

    def test_invalid_dictionary_cannot_partially_mutate_fields(self):
        for kind in ['duplicate_name', 'duplicate_alias', 'missing', 'ordinal', 'syntax', 'basis']:
            with self.subTest(kind=kind):
                rows = copy.deepcopy(self.rows)
                if kind == 'duplicate_name': rows[-1]['oracle_name'] = rows[0]['oracle_name']
                if kind == 'duplicate_alias': rows[-1]['canonical_alias'] = rows[0]['canonical_alias']
                if kind == 'missing': rows.pop()
                if kind == 'ordinal': rows[-1]['ordinal_position'] = '999'
                if kind == 'syntax': rows[-1]['canonical_alias'] = 'Invalid-Alias'
                if kind == 'basis': rows[-1]['alias_basis'] = 'GUESSED'
                fields = copy.deepcopy(self.fields)
                for field in fields: field['canonical_alias'] = None
                before = copy.deepcopy(fields)
                with self.assertRaises(ValueError): apply_records(fields, rows)
                self.assertEqual(before, fields)

    def test_existing_different_alias_requires_separate_revision(self):
        fields = copy.deepcopy(self.fields)
        fields[-1]['canonical_alias'] = 'previously_approved_alias'
        before = copy.deepcopy(fields)
        with self.assertRaises(ValueError): apply_records(fields, self.rows)
        self.assertEqual(before, fields)

    def test_revision_is_additive_and_backlog_unchanged(self):
        revisions = yaml.safe_load((ROOT / DOMAIN / 'revisions.yaml').read_text())['records']
        revision = next(r for r in revisions if r['revision_id'] == REVISION)
        self.assertFalse(revision['breaking_change'])
        self.assertEqual({r['field_id'] for r in self.fields}, set(revision['changed_record_refs']))
        backlog = yaml.safe_load((ROOT / DOMAIN / 'backlog.yaml').read_text())['records']
        self.assertEqual(7, len(backlog))
        self.assertFalse(any(r['blocking'] for r in backlog))


if __name__ == '__main__':
    unittest.main()

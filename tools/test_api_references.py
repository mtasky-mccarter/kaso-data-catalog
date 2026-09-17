"""Consistency checks for source API/member reference registries."""
import copy
import json
import unittest

from validate_catalog import ROOT, load_yaml, validate_document


def summary_errors(document):
    if document.get('kind') != 'api-references':
        return []
    records = document.get('records', [])
    callers = {(r.get('caller_owner'), r.get('caller_name'), r.get('caller_type')) for r in records}
    members = {(r.get('target_package'), r.get('member_name_normalized', r.get('member_name_raw'))) for r in records}
    actual = {
        'record_count': len(records),
        'caller_count': len(callers),
        'member_count': len(members),
    }
    declared = document.get('summary', {})
    errors = [f'{key}: declared {declared.get(key)!r}, actual {value!r}'
              for key, value in actual.items() if declared.get(key) != value]
    for r in records:
        if r.get('hit_count') != len(r.get('hit_lines', [])):
            errors.append(f"{r.get('api_reference_id')}: hit_count does not match hit_lines")
    return errors


class ApiReferenceTests(unittest.TestCase):
    def test_approved_cp_vyd_purchasing_and_pm_targets_validate(self):
        targets = ['D_CPR_L', 'D_CPR_O', 'D_VYDAJ_L', 'D_VYDAJ_L_B',
                   'D_VYDAJ_O', 'D_VYDAJ_O2', 'C_VYD_O_P_PRIJ', 'D_OBJD_L',
                   'D_OBJD_O', 'C_OBJ_D_KOMBAJN', 'C_REZ_OBJ_DOD',
                   'D_OBJ_ODB_L', 'D_OBJ_ODB_L_B', 'D_OBJ_ODB_O',
                   'C_SKLAD_KARTA', 'C_SKLAD_KARTA_LB', 'C_SKLAD_DODAVATEL',
                   'C_SK_NAKL_POL', 'C_NAKL_KOEF', 'C_CIS_POZNAMKY', 'MCCARTER_PLAN']
        schema = json.loads((ROOT / 'schema/api-references.schema.json').read_text())
        self.assertEqual(targets, schema['$defs']['record']['properties']['target_package']['enum'])
        for target in targets:
            with self.subTest(target=target):
                doc = copy.deepcopy(load_yaml(ROOT / 'examples/schema-smoke-test/api-references.yaml'))
                doc['records'][0]['target_package'] = target
                self.assertEqual([], validate_document(doc))

    def test_unapproved_api_target_remains_rejected(self):
        doc = copy.deepcopy(load_yaml(ROOT / 'examples/schema-smoke-test/api-references.yaml'))
        doc['records'][0]['target_package'] = 'UNAPPROVED_PACKAGE'
        self.assertTrue(any('target_package' in error for error in validate_document(doc)))

    def test_synthetic_summary_matches_records(self):
        doc = load_yaml(ROOT / 'examples/schema-smoke-test/api-references.yaml')
        self.assertEqual([], summary_errors(doc))

    def test_summary_mismatch_is_detected(self):
        doc = copy.deepcopy(load_yaml(ROOT / 'examples/schema-smoke-test/api-references.yaml'))
        doc['summary']['caller_count'] += 1
        self.assertTrue(summary_errors(doc))

    def test_hit_count_mismatch_is_detected(self):
        doc = copy.deepcopy(load_yaml(ROOT / 'examples/schema-smoke-test/api-references.yaml'))
        doc['records'][0]['hit_count'] += 1
        self.assertTrue(summary_errors(doc))

    def test_all_catalog_api_reference_summaries(self):
        errors = []
        for path in (ROOT / 'catalog').rglob('*.yaml'):
            doc = load_yaml(path)
            errors.extend(f'{path.relative_to(ROOT)}: {e}' for e in summary_errors(doc))
        self.assertEqual([], errors)


if __name__ == '__main__':
    unittest.main()

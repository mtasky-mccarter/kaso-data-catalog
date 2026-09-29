"""CoA delta: original UI provenance, uncertainty and unchanged canonical semantics."""
import copy
import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

import yaml
from validate_catalog import ROOT, validate_document

PUR = 'catalog/purchasing/'
PACKAGE = json.loads((ROOT / 'evidence/source-extracts/pur/coa-delta-20260929.json').read_text())
BASE = PACKAGE['base_commit']


def read(name):
    return yaml.safe_load((ROOT / PUR / (name + '.yaml')).read_text())


def old(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


class CoAMetadataTests(unittest.TestCase):
    def test_original_select_is_exact_and_bindings_match_projection_order(self):
        parent = (ROOT / 'evidence/snapshots/pur/coa-ui-submission-20260929.txt').read_text()
        raw = (ROOT / 'evidence/snapshots/pur/coa-ui-select-20260929.sql').read_text()
        self.assertEqual(parent[parent.index('SELECT  C.RID_O'):parent.index('\n\nDôležité:')], raw)
        compact = re.sub(r'\s+', '', raw).upper()
        for token in ('FROMOBJD_OC', 'ID_CIS=-1006', 'ID_R_V=0', "RID_O='020260003197'"):
            self.assertIn(token, compact)
        self.assertRegex(raw, r"GetTagValueNumT\(C.XML_DATA,'U1'.*AS colTag1,.*GetTagValueDateT\(C.XML_DATA,'U3'.*AS colTag2,.*GetTagValueT\(C.XML_DATA,'U2'.*AS colTag3")
        self.assertTrue(raw.endswith(':tblObjD_LFormular.m_sValues[155],:tblObjD_LFormular.m_sValues[156],:tblObjD_LFormular.m_sValues[157]'))

    def test_derived_fields_source_context_and_history(self):
        records = {r.get('canonical_alias'): r for r in read('temporal')['records'] if 'canonical_alias' in r}
        expected = {'coa_certificate_status': ('U1', 'GetTagValueNumT', 155), 'coa_batch': ('U2', 'GetTagValueT', 157), 'coa_expiry_date': ('U3', 'GetTagValueDateT', 156)}
        self.assertEqual(set(expected), set(records))
        for alias, (tag, function, binding) in expected.items():
            r = records[alias]
            self.assertEqual('mc.field.objd_o.xml_data', r['source_ref'])
            self.assertEqual('DERIVED CURRENT', r['classification'])
            self.assertEqual((tag, -2020), (r['xml_tag'], r['xml_context']))
            self.assertEqual(f"c_xml_tags.{function}(C.XML_DATA,'{tag}', -2020, NULL)", r['derivation_expression'])
            self.assertEqual(f'tblObjD_LFormular.m_sValues[{binding}]', r['ui_binding'])
            self.assertFalse(r['reconstructable'])
            self.assertEqual('POTVRDENÉ', r['status'])
            self.assertIn('pur.evidence.coa_ui.20260929', r['evidence_refs'])
            self.assertIn('pur.evidence.coa_business.20260929', r['evidence_refs'])
        self.assertIn('ID_CIS = -1006', records['coa_certificate_status']['display_expression'])

    def test_display_states_do_not_invent_raw_codes(self):
        values = [r for r in read('value-domains')['records'] if r['value_domain_id'].startswith('pur.value.coa.')]
        self.assertEqual({'', 'Nie', 'Áno'}, {r['canonical_value'] for r in values})
        for r in values:
            self.assertNotIn('raw_value', r)
            self.assertIn('TREBA OVERIŤ', ' '.join(r['limitations_sk']))

    def test_physical_fields_remain_distinct(self):
        before = {r['field_id']: r for r in yaml.safe_load(old(PUR + 'fields-objd_o.yaml'))['records']}
        after = {r['field_id']: r for r in read('fields-objd_o')['records']}
        self.assertEqual(set(before), set(after))
        for alias in ('sarza', 'datum_exp'):
            fid = 'mc.field.objd_o.' + alias
            for key in before[fid].keys() - {'limitations_sk', 'evidence_refs'}:
                self.assertEqual(before[fid][key], after[fid][key], key)
            self.assertIn('XML_DATA/', ' '.join(after[fid]['limitations_sk']))
            self.assertIn('neoznačovať ako nepoužívaný', ' '.join(after[fid]['limitations_sk']))
        self.assertEqual('RAW CURRENT', after['mc.field.objd_o.xml_data']['temporal_classification'])
        self.assertIn('CoA', after['mc.field.objd_o.xml_data']['business_definition_sk'])

    def test_existing_records_and_backlog_are_inherited(self):
        for name in ('contract', 'backlog', 'relationships', 'constraints', 'flows', 'mutations'):
            self.assertEqual(old(PUR + name + '.yaml'), (ROOT / PUR / (name + '.yaml')).read_bytes())
        for name in ('temporal', 'value-domains', 'do-not-assume', 'sql-registry', 'playbooks', 'revisions'):
            previous = yaml.safe_load(old(PUR + name + '.yaml'))['records']
            self.assertEqual(previous, read(name)['records'][:len(previous)])
        self.assertEqual('AGENT-READY', read('contract')['maturity'])
        self.assertEqual(7, len(read('backlog')['records']))
        self.assertFalse(any(r['blocking'] for r in read('backlog')['records']))

    def test_sql_and_playbook_keep_current_line_grain_and_limits(self):
        sql = (ROOT / 'sql/diagnostic/purchasing/coa_metadata.sql').read_text()
        code = re.sub(r'--[^\n]*', '', sql).upper()
        for alias in ('COA_CERTIFICATE_STATUS_RAW', 'COA_CERTIFICATE_STATUS', 'COA_BATCH', 'COA_EXPIRY_DATE'):
            self.assertIn('AS ' + alias, code)
        for term in ('C.SARZA', 'C.DATUM_EXP', ' JOIN ', '020260003197'):
            self.assertNotIn(term, code)
        for term in ('C.RID_O = :P_RID_O', 'C.ID_R = :P_ID_R', 'C.ID_R_V = 0'):
            self.assertIn(term, code)
        self.assertIn('UI query condition; business meaning not established.', sql)
        p = next(r for r in read('playbooks')['records'] if r['playbook_id'] == 'pur.playbook.coa_metadata')
        self.assertEqual('pur.sql.coa_metadata', p['first_sql_ref'])
        self.assertIn('Ako prvé skontrolovať current OBJD_O.XML_DATA', p['proves_sk'])
        rules = [r for r in read('do-not-assume')['records'] if r['rule_id'].startswith('pur.rule.coa.')]
        self.assertEqual(6, len(rules))

    def test_evidence_classes_checksums_and_user_boundary(self):
        for name, cls in [('ui', 'C'), ('business', 'D'), ('version', 'D')]:
            m = yaml.safe_load((ROOT / f'evidence/manifests/pur/coa-{name}-20260929.yaml').read_text())
            self.assertEqual(cls, m['evidence_class'])
            self.assertEqual(m['sha256'], hashlib.sha256((ROOT / m['repository_path']).read_bytes()).hexdigest())
        business = (ROOT / 'evidence/snapshots/pur/coa-business-handoff-20260929.txt').read_text()
        self.assertIn('same user-entry capability is not available on the receipt form', business)
        for x in PACKAGE['approval_sources']:
            self.assertEqual(x['sha256'], hashlib.sha256((ROOT / x['path']).read_bytes()).hexdigest())

    def test_revision_and_v10_artifacts_are_preserved(self):
        r = read('revisions')['records'][-1]
        self.assertEqual(('1.0', '1.1', 'NON_BREAKING_SEMANTIC', 'REGENERATE', False), tuple(r[k] for k in ('contract_version', 'documentation_version', 'change_classification', 'publication_impact', 'breaking_change')))
        paths = list((ROOT / 'generated/nakupne-objednavky').glob('* v1.0.*'))
        self.assertEqual(3, len(paths))
        for p in paths:
            self.assertEqual(old(p.relative_to(ROOT).as_posix()), p.read_bytes())
        snapshots = list((ROOT / 'evidence/snapshots/pur').glob('*.xlsx'))
        self.assertEqual(26, len(snapshots))
        for p in snapshots:
            self.assertEqual(old(p.relative_to(ROOT).as_posix()), p.read_bytes())

    def test_derived_extension_rejects_missing_source_and_raw_classification(self):
        d = read('temporal')
        self.assertEqual([], validate_document(d))
        for key, replacement in [('source_ref', None), ('classification', 'RAW CURRENT')]:
            bad = copy.deepcopy(d)
            r = next(r for r in bad['records'] if 'canonical_alias' in r)
            if replacement is None:
                del r[key]
            else:
                r[key] = replacement
            self.assertTrue(validate_document(bad))


if __name__ == '__main__':
    unittest.main()

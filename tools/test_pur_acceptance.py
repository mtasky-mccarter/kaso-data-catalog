"""Lossless purchasing handoff checks; no production SQL is executed."""
import copy
import hashlib
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from validate_catalog import ROOT, load_yaml, validate_document

PUR = ROOT / 'catalog/purchasing'
SNAP = ROOT / 'evidence/snapshots/pur'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def load(name):
    return load_yaml(PUR / (name + '.yaml'))


def source_rows(prefix):
    paths = list(SNAP.glob('PUR_' + prefix + '_*.xlsx'))
    if len(paths) != 1:
        raise AssertionError(f'Missing retained original evidence for {prefix}')
    with ZipFile(paths[0]) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(t.text or '' for t in si.findall('.//m:t', NS))
                       for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows = []
        for row in sheet.findall('.//m:sheetData/m:row', NS):
            cells = {}
            for c in row.findall('m:c', NS):
                label = re.match(r'[A-Z]+', c.attrib['r'])[0]
                pos = 0
                for ch in label:
                    pos = pos * 26 + ord(ch) - 64
                v = c.find('m:v', NS)
                value = v.text if v is not None else None
                if c.attrib.get('t') == 's' and value is not None:
                    value = strings[int(value)]
                elif c.attrib.get('t') == 'inlineStr':
                    value = ''.join(t.text or '' for t in c.findall('.//m:t', NS))
                cells[pos] = value
            rows.append(cells)
    headers = rows[0]
    return [{name: row.get(i) for i, name in headers.items()} for row in rows[1:]]


class PurchasingAcceptance(unittest.TestCase):
    def test_scope_and_core_identity(self):
        contract = load('contract')
        self.assertEqual(('MC', 'MC', 'purchasing'),
                         (contract['authoritative_environment'], contract['authoritative_owner'], contract['domain']))
        constraints = load('constraints')['records']
        for table, columns in {'objd_l': ['rid'], 'objd_o': ['rid_o', 'id_r'], 'obj_d_navrh': ['rid']}.items():
            pks = [r for r in constraints if r['object_ref'] == 'mc.object.' + table and r['constraint_type'] == 'PK']
            self.assertEqual(1, len(pks))
            self.assertEqual(['mc.field.' + table + '.' + c for c in columns], pks[0]['column_refs'])

    def test_full_available_fields_match_original(self):
        original = source_rows('MP01_B')
        expected = {(r['TABLE_NAME'], r['COLUMN_NAME']): r for r in original}
        actual = {}
        for path in PUR.glob('fields-*.yaml'):
            doc = load_yaml(path)
            table = load_yaml(PUR / ('object-' + path.stem[7:] + '.yaml'))['oracle_name']
            for r in doc['records']:
                actual[(table, r['oracle_name'])] = r
        self.assertEqual(set(expected), set(actual))
        for key, raw in expected.items():
            with self.subTest(field=key):
                record = actual[key]
                self.assertEqual(int(raw['COLUMN_ID']), record['ordinal_position'])
                self.assertEqual(raw['NULLABLE'] == 'Y', record['nullable'])
                self.assertEqual(raw['COMMENTS'], record.get('oracle_comment'))
                self.assertEqual(raw['DATA_DEFAULT'], record.get('default_raw'))

    def test_constraints_and_indexes_preserve_inventory(self):
        raw = source_rows('MP01_C')
        expected = {(r['TABLE_NAME'].lower(), r['CONSTRAINT_NAME']) for r in raw}
        records = load('constraints')['records']
        self.assertEqual(expected, {(r['object_ref'].split('.')[-1], r['oracle_name']) for r in records})
        reverse = next(r for r in records if r['oracle_name'] == 'XFK_OBJD_O_RID_N')
        self.assertEqual(('DISABLED', 'NOT VALIDATED'), (reverse['enabled_state'], reverse['validated_state']))
        expected_indexes = {(r['TABLE_NAME'].lower(), r['INDEX_NAME'], int(r['COLUMN_POSITION']), r['COLUMN_NAME']) for r in source_rows('MP01_D')}
        actual = set()
        for r in load('indexes')['records']:
            for c in r['column_or_expression_entries']:
                name = c.get('expression_raw') or c['field_ref'].split('.')[-1].upper()
                actual.add((r['object_ref'].split('.')[-1], r['oracle_name'], c['position'], name))
        self.assertEqual(expected_indexes, actual)

    def test_critical_semantics_and_fanout(self):
        temporal = {r['temporal_rule_id']: r for r in load('temporal')['records']}
        self.assertIn('GetS_STAV', temporal['pur.temporal.fulfilment']['transition_or_event_sk'])
        self.assertIn('Flag 11', temporal['pur.temporal.flags']['transition_or_event_sk'])
        self.assertIn('NVL(OBJD_O.TERMIN_DOD, NVL(OBJD_L.TERMIN_DOD, OBJD_L.DATUM_P))', temporal['pur.temporal.delivery']['transition_or_event_sk'])
        self.assertFalse(temporal['pur.temporal.receipt_history']['reconstructable'])
        self.assertEqual('DATA GAP', temporal['pur.temporal.receipt_history']['classification'])
        rel = {r['relationship_id']: r for r in load('relationships')['records']}
        for name in ['po_pl', 'pl_receipt', 'header_lines']:
            self.assertEqual('1:N', rel['pur.rel.' + name]['cardinality'])
        self.assertIn("O.RID_O || '!' || TO_CHAR(O.ID_R)", rel['pur.rel.proposal_po']['condition_sk'])
        handoff = (SNAP / 'accepted.txt').read_text()
        section = handoff.split('23. DO NOT ASSUME REGISTER')[1].split('24. TEMPORAL CLASSIFICATION')[0]
        expected = {' '.join(m[2].split()) for m in re.finditer(r'\n(\d+)\.\n(.*?)(?=\n\d+\.\n|\n=|\Z)', section, re.S)}
        self.assertEqual(expected, {r['statement_sk'] for r in load('do-not-assume')['records']})
        self.assertFalse(any(r['blocking'] for r in load('backlog')['records']))
        values = load('value-domains')['records']
        for state in (3, 4):
            item = next(r for r in values if r['scope_ref'] == 'mc.field.obj_d_navrh.stav' and r['raw_value'] == state)
            self.assertIs(item['observed_live'], False)
        self.assertEqual(7, len(load('playbooks')['records']))

    def test_subtype_codes_are_explicit_strings(self):
        records = [r for r in load('value-domains')['records']
                   if r['scope_ref'] == 'mc.field.objd_l.typ_cis']
        self.assertEqual({'00028', '00029', '00030'}, {r['raw_value'] for r in records})
        self.assertTrue(all(isinstance(r['raw_value'], str) for r in records))
        text = (PUR / 'value-domains.yaml').read_text()
        for code in ('00028', '00029', '00030'):
            self.assertIn("raw_value: '" + code + "'", text)

    def test_external_field_ids_are_owner_neutral(self):
        doc = load_yaml(ROOT / 'catalog/transport/cestovne-prikazy/oracle-entities.yaml')
        text = str(doc)
        self.assertNotIn('pur.boundary_field.', text)
        expected = {'b_users': 'id', 'miesta_zaujmu': 'id', 'obch_partneri': 'id',
                    'miesta_dodania': 'rid', 'cis_stavy_typy': 'skratka',
                    'bartex_pobocky': 'id', 'sklad_polohy': 'rid', 'cis_tree': 'id', 'depa': 'rid'}
        constraints = str(load('constraints'))
        for table, column in expected.items():
            canonical = f'mc.oracle.mc_{table}.field.{column}'
            self.assertIn(canonical, text)
            self.assertIn(canonical, constraints)
            for path in PUR.glob('*.yaml'):
                self.assertNotIn(f'pur.boundary_field.mc.{table}.{column}', path.read_text())

    def test_direct_po_receipt_is_technical_with_unproven_cardinality(self):
        records = [r for r in load('relationships')['records']
                   if r['relationship_id'] == 'pur.rel.po_receipt']
        self.assertEqual(1, len(records))
        rel = records[0]
        self.assertEqual('mc.object.objd_o', rel['from_object_ref'])
        self.assertEqual(['mc.field.objd_o.rid_o', 'mc.field.objd_o.id_r'], rel['from_field_refs'])
        self.assertEqual('pur.oracle.mc.prijemky_obsah.table', rel['to_object_ref'])
        self.assertEqual(['pur.boundary_field.mc.prijemky_obsah.rid_v'], rel['to_field_refs'])
        self.assertEqual('CONDITIONAL', rel['relationship_type'])
        self.assertIsNone(rel['cardinality'])
        self.assertEqual('TECHNICKY ZNÁME', rel['status'])
        for predicate in ("R.RID_V = O.RID_O || '!' || TO_CHAR(O.ID_R)",
                          'O.RID_O=L.RID', "L.TYP_CIS='00028'"):
            self.assertIn(predicate, rel['condition_sk'])
        self.assertIn('pur.evidence.accepted', rel['evidence_refs'])
        self.assertIn('pur.backlog.direct_receipt', rel['safe_usage_sk'])
        gap = next(r for r in load('backlog')['records'] if r['backlog_id'] == 'pur.backlog.direct_receipt')
        self.assertIs(gap['blocking'], False)
        self.assertEqual('TREBA OVERIŤ', gap['status'])

    def test_approved_api_capability_and_handygo_locus(self):
        for target in ('D_CPR_L', 'D_CPR_O', 'D_OBJD_L', 'D_OBJD_O', 'C_OBJ_D_KOMBAJN', 'C_REZ_OBJ_DOD'):
            doc = copy.deepcopy(load_yaml(ROOT / 'examples/schema-smoke-test/api-references.yaml'))
            doc['records'][0]['target_package'] = target
            self.assertEqual([], validate_document(doc), target)
        records = load('api-references')['records']
        matches = [r for r in records if r['caller_name'] == 'HANDYGO' and r['target_package'] == 'D_OBJD_L'
                   and r['member_name_raw'].lower() == 'ukonciprijempl']
        self.assertTrue(any(5027 in r['hit_lines'] for r in matches))
        self.assertTrue(all(r['classification'] == 'SOURCE MEMBER REFERENCE' for r in records))

    def test_evidence_retained_and_checksums(self):
        manifests = list((ROOT / 'evidence/manifests/pur').glob('*.yaml'))
        self.assertEqual(28, len(manifests))
        for p in manifests:
            doc = load_yaml(p)
            self.assertTrue(doc['raw_retained'])
            data = (ROOT / doc['repository_path']).read_bytes()
            self.assertEqual(doc['sha256'], hashlib.sha256(data).hexdigest())

    def test_dependency_roles_and_revision(self):
        self.assertTrue(all(r['role'] == 'DEPENDENCY ONLY' for r in load('inbound-closure')['records']))
        self.assertTrue(all('ACCESS CAPABILITY ONLY' in r['statement_sk'] for r in load('access-capabilities')['records']))
        readers = [r for r in load('dependencies')['records'] if r['role'] == 'READER']
        self.assertEqual({'mc.object.objd_l', 'mc.object.objd_o'}, {r['target_ref'] for r in readers})
        revisions = {r['revision_id']: r for r in load('revisions')['records']}
        self.assertTrue(revisions['pur.revision.semantic.1_0']['breaking_change'])
        self.assertFalse(revisions['pur.revision.schema.001']['breaking_change'])

    def test_mutation_surface_covers_critical_stored_fields(self):
        records = load('source-mutations')['records']
        targets = {t for r in records for t in r['target_refs']}
        self.assertTrue({'mc.field.objd_o.p_prij', 'mc.field.objd_o.p_pl', 'mc.field.objd_o.p_del',
                         'mc.field.objd_l.flags_s', 'mc.field.obj_d_navrh.stav'}.issubset(targets))
        for record in records:
            self.assertIn('pur.evidence.mp01_f', record['evidence_refs'])
            self.assertTrue(record['direct_mutations_sk'].lower().startswith('update '))


if __name__ == '__main__':
    unittest.main()

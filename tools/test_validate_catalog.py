"""Synthetic-only acceptance and rejection tests. Run with unittest discovery."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from validate_catalog import ROOT, load_yaml, validate_bundle, validate_document, validators


class CatalogValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checks = validators()
        cls.fixtures = {str(p.relative_to(ROOT)): load_yaml(p)
                        for p in (ROOT / 'examples/schema-smoke-test').rglob('*.yaml')}

    def fixture(self, kind):
        return copy.deepcopy(next(d for d in self.fixtures.values() if d['kind'] == kind))

    def assert_valid(self, document):
        self.assertEqual([], validate_document(document, self.checks))

    def assert_invalid(self, document):
        self.assertTrue(validate_document(document, self.checks))

    def registry(self, kind, record):
        return {'schema_version': '1.0', 'kind': kind, 'id': 'synthetic.registry.999',
                'records': [record]}

    def test_synthetic_bundle(self):
        self.assertEqual([], validate_bundle(self.fixtures))

    def test_status_maturity_temporal_and_retention(self):
        for kind, prop in [('object', 'status'), ('object', 'maturity'),
                           ('contract', 'maturity'), ('evidence-manifest', 'retention_class')]:
            with self.subTest(kind=kind, prop=prop):
                doc = self.fixture(kind)
                doc[prop] = 'UNKNOWN'
                self.assert_invalid(doc)
        doc = self.fixture('fields')
        doc['records'][0]['temporal_classification'] = 'UNKNOWN'
        self.assert_invalid(doc)

    def test_required_ids_and_envelopes(self):
        for original in self.fixtures.values():
            for key in ['schema_version', 'kind', next(k for k in original
                         if k == 'id' or k.endswith('_id'))]:
                with self.subTest(kind=original['kind'], key=key):
                    doc = copy.deepcopy(original)
                    del doc[key]
                    self.assert_invalid(doc)
        doc = self.fixture('fields')
        del doc['records'][0]['field_id']
        self.assert_invalid(doc)

    def test_technical_fact_needs_no_business_meaning(self):
        for kind in ['object', 'fields']:
            doc = self.fixture(kind)
            record = doc['records'][0] if kind == 'fields' else doc
            record['status'] = 'TECHNICKY ZNÁME'
            self.assert_valid(doc)

    def test_malformed_manifest(self):
        for prop, value in [('evidence_class', 'Z'), ('captured_at', 'yesterday'),
                            ('snapshot_date', '2026-02-30'), ('sha256', 'short'),
                            ('raw_retained', 'false'), ('supports_record_refs', 'x')]:
            with self.subTest(prop=prop):
                doc = self.fixture('evidence-manifest')
                doc[prop] = value
                self.assert_invalid(doc)

    def test_snapshot_requirements(self):
        doc = self.fixture('evidence-manifest')
        doc.update(retention_class='SNAPSHOT_CRITICAL', sha256='a' * 64,
                   raw_retained=True, repository_path='evidence/snapshots/synthetic.txt')
        self.assert_valid(doc)
        for key in ['sha256', 'raw_retained', 'repository_path']:
            bad = copy.deepcopy(doc)
            del bad[key]
            self.assert_invalid(bad)
        for key, value in [('sha256', None), ('raw_retained', False),
                           ('repository_path', 'elsewhere/synthetic.txt'),
                           ('repository_path', 'evidence/snapshots/../escape.txt')]:
            bad = copy.deepcopy(doc)
            bad[key] = value
            self.assert_invalid(bad)

    def test_retained_file_checksum_and_missing_file(self):
        doc = self.fixture('evidence-manifest')
        doc.update(retention_class='SNAPSHOT_CRITICAL', raw_retained=True,
                   repository_path='evidence/snapshots/synthetic.txt',
                   sha256=hashlib.sha256(b'synthetic').hexdigest())
        doc['supports_record_refs'] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(validate_bundle({'manifest': doc}, root))
            path = root / doc['repository_path']
            path.parent.mkdir(parents=True)
            path.write_bytes(b'synthetic')
            self.assertEqual([], validate_bundle({'manifest': doc}, root))
            path.write_bytes(b'changed')
            self.assertTrue(validate_bundle({'manifest': doc}, root))

    def test_nonretained_evidence(self):
        for retention in ['TRANSIENT', 'REPRODUCIBLE']:
            doc = self.fixture('evidence-manifest')
            doc['retention_class'] = retention
            doc['query_ref'] = 'synthetic.sql.001' if retention == 'REPRODUCIBLE' else None
            self.assert_valid(doc)

    def test_reference_integrity(self):
        docs = copy.deepcopy(self.fixtures)
        docs['duplicate'] = self.fixture('object')
        self.assertTrue(any('duplicate ID' in e for e in validate_bundle(docs)))
        docs = copy.deepcopy(self.fixtures)
        next(d for d in docs.values() if d['kind'] == 'object')['field_registry_ref'] = 'missing.id'
        self.assertTrue(any('unresolved' in e for e in validate_bundle(docs)))

    def test_hypothesis_cannot_confirm(self):
        docs = copy.deepcopy(self.fixtures)
        next(d for d in docs.values() if d['kind'] == 'object')['status'] = 'POTVRDENÉ'
        self.assertTrue(any('non-E evidence' in e for e in validate_bundle(docs)))

    def test_strict_yaml(self):
        for content in ['id: a\nid: b\n', 'id: 000012\n', 'x: &x [*x]\n',
                        'x: .nan\n', '1: value\n']:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / 'bad.yaml'
                p.write_text(content)
                with self.assertRaises(ValueError):
                    load_yaml(p)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'good.yaml'
            p.write_text('id: "000012"\nvalue: null\nflag: false\ndate: 2026-09-09\n')
            self.assertEqual(load_yaml(p), {'id': '000012', 'value': None,
                                            'flag': False, 'date': '2026-09-09'})

    def test_polymorphic_relationship(self):
        doc = self.fixture('relationships')
        r = doc['records'][0]
        r['relationship_type'] = 'POLYMORPHIC'
        del r['to_object_ref'], r['to_field_refs']
        r['selector_field_refs'] = ['synthetic.field.001']
        r['targets'] = [dict(to_object_ref='synthetic.object.001',
                            to_field_refs=['synthetic.field.001'],
                            selector_condition_sk=condition, status='TREBA OVERIŤ',
                            evidence_refs=['synthetic.evidence.001'])
                        for condition in ['Syntetická vetva A', 'Syntetická vetva B']]
        self.assert_valid(doc)
        r['targets'][0]['status'] = 'POTVRDENÉ'
        r['targets'][0]['evidence_refs'] = []
        self.assert_invalid(doc)
        r['targets'][0]['status'] = 'TREBA OVERIŤ'
        del r['targets'][0]['selector_condition_sk']
        self.assert_invalid(doc)

    def test_remaining_record_kinds(self):
        ref = 'synthetic.object.001'
        evidence = ['synthetic.evidence.001']
        fact = {'status': 'TREBA OVERIŤ', 'evidence_refs': evidence}
        samples = {
            'constraints': dict(constraint_id='synthetic.constraint.001', object_ref=ref,
                                oracle_name='EXAMPLE_PK', constraint_type='P', column_refs=[], **fact),
            'indexes': dict(index_id='synthetic.index.001', object_ref=ref,
                            oracle_name='EXAMPLE_INDEX', column_or_expression_entries=[
                                {'position': 1, 'expression_raw': 'UPPER(EXAMPLE_CODE)'}], **fact),
            'value-domains': dict(value_domain_id='synthetic.value.001', scope_ref=ref,
                                  source_constant_ref=ref, observed_live=False, **fact),
            'temporal': dict(temporal_rule_id='synthetic.temporal.001', scope_refs=[ref],
                             classification='DATA GAP', **fact),
            'mutations': dict(mutation_id='synthetic.mutation.001', target_refs=[ref],
                              writer_ref=None, **fact),
            'flows': dict(flow_id='synthetic.flow.001', trigger_or_procedure_ref=None,
                          calls=[{'callee_ref': ref, 'sequence': 1}], direct_mutations=[],
                          side_effects=[], exceptions=[], evidence_refs=evidence),
            'dependencies': dict(dependency_id='synthetic.dependency.001', source_ref=ref,
                                 target_ref=ref, direction='INBOUND', depth=1,
                                 role='DEPENDENCY ONLY', discovery_method='Synthetic',
                                 source_visible=False, runtime_boundary=True, **fact),
            'data-quality': dict(dq_id='synthetic.dq.001', scope_refs=[ref],
                                 observation_sk='Syntetická poznámka', blocking=False, **fact),
            'do-not-assume': dict(rule_id='synthetic.rule.001', scope_refs=[ref],
                                  statement_sk='Syntetické pravidlo', evidence_refs=evidence),
            'playbooks': dict(playbook_id='synthetic.playbook.001', symptom_sk='Syntetický symptóm',
                              first_sql_ref=None),
            'sql-registry': dict(sql_id='synthetic.sql.001', title_sk='Syntetický dotaz',
                                 sql_file='sql/diagnostic/synthetic.sql', evidence_refs=evidence,
                                 compatibility={'sql_client': 'SQL Navigator 5.5.4.847',
                                                'oracle_server_version': None, 'read_only': True}),
            'backlog': dict(backlog_id='synthetic.backlog.001', scope_refs=[ref], blocking=True,
                            question_sk='Syntetická otázka?', status='DATA GAP',
                            related_evidence_refs=evidence),
            'revisions': dict(revision_id='synthetic.revision.001', contract_version='1.0',
                              date='2026-09-09', breaking_change=False, changed_record_refs=[ref],
                              change_sk='Syntetická revízia', evidence_refs=evidence),
        }
        self.assertEqual(set(self.checks), set(samples) | {d['kind'] for d in self.fixtures.values()})
        for kind, record in samples.items():
            with self.subTest(kind=kind):
                doc = self.registry(kind, record)
                self.assert_valid(doc)
                for key in [k for k in record if k.endswith('_id')]:
                    invalid = copy.deepcopy(doc)
                    del invalid['records'][0][key]
                    self.assert_invalid(invalid)
        illegal = self.registry('backlog', samples['backlog'])
        illegal['records'][0]['status'] = 'POTVRDENÉ'
        self.assert_invalid(illegal)
        sql = self.registry('sql-registry', samples['sql-registry'])
        sql['records'][0]['query_body'] = 'SELECT 1 FROM EXAMPLE_TABLE'
        self.assert_invalid(sql)
        del sql['records'][0]['query_body']
        sql['records'][0]['compatibility']['oracle_server_version'] = '19c'
        self.assert_invalid(sql)
        dep = self.registry('dependencies', samples['dependencies'])
        dep['records'][0].update(role='DIRECT WRITER', evidence_refs=[])
        self.assert_invalid(dep)


    def test_unresolved_reference_categories(self):
        cases = [
            ('contract', 'object_refs', ['synthetic.missing.object']),
            ('contract', 'boundary_refs', ['synthetic.missing.boundary']),
            ('object', 'identity_refs', ['synthetic.missing.constraint']),
            ('object', 'field_registry_ref', 'synthetic.missing.fields'),
            ('fields', 'lookup_ref', 'synthetic.missing.lookup'),
            ('fields', 'replacement_ref', 'synthetic.missing.replacement'),
            ('fields', 'authoritative_source_ref', 'synthetic.missing.source'),
            ('relationships', 'from_field_refs', ['synthetic.missing.field']),
            ('relationships', 'physical_constraint_ref', 'synthetic.missing.constraint'),
            ('object', 'evidence_refs', ['synthetic.missing.evidence']),
            ('evidence-manifest', 'query_ref', 'synthetic.missing.sql'),
            ('evidence-manifest', 'supports_record_refs', ['synthetic.missing.relationship']),
        ]
        for kind, key, value in cases:
            with self.subTest(kind=kind, key=key):
                docs = copy.deepcopy(self.fixtures)
                doc = next(d for d in docs.values() if d['kind'] == kind)
                record = doc['records'][0] if 'records' in doc else doc
                record[key] = value
                self.assert_valid(doc)
                self.assertTrue(any('unresolved' in error for error in validate_bundle(docs)))
        for key in ['first_sql_ref', 'flow_refs', 'dependency_or_boundary_refs']:
            with self.subTest(key=key):
                record = dict(playbook_id='synthetic.playbook.999', symptom_sk='Syntetický test',
                              first_sql_ref=None)
                record[key] = ['synthetic.missing.target'] if key.endswith('_refs') else 'synthetic.missing.target'
                docs = copy.deepcopy(self.fixtures)
                docs['playbook'] = self.registry('playbooks', record)
                self.assert_valid(docs['playbook'])
                self.assertTrue(any('unresolved' in error for error in validate_bundle(docs)))

    def test_confirmed_fact_requires_valid_manifest(self):
        for refs in [[], ['synthetic.missing.evidence'], ['synthetic.object.001'],
                     ['synthetic.evidence.001']]:
            with self.subTest(refs=refs):
                docs = copy.deepcopy(self.fixtures)
                record = next(d for d in docs.values() if d['kind'] == 'object')
                record.update(status='POTVRDENÉ', evidence_refs=refs)
                self.assertTrue(validate_bundle(docs))
        docs = copy.deepcopy(self.fixtures)
        next(d for d in docs.values() if d['kind'] == 'object')['status'] = 'POTVRDENÉ'
        next(d for d in docs.values() if d['kind'] == 'evidence-manifest')['evidence_class'] = 'A'
        self.assertEqual([], validate_bundle(docs))

    def test_evidence_must_target_manifest_even_if_unconfirmed(self):
        docs = copy.deepcopy(self.fixtures)
        next(d for d in docs.values() if d['kind'] == 'object')['evidence_refs'] = ['synthetic.object.001']
        self.assertTrue(any('not a manifest' in error for error in validate_bundle(docs)))

    def test_source_physical_values_and_null_are_not_changed(self):
        docs = copy.deepcopy(self.fixtures)
        field = next(d for d in docs.values() if d['kind'] == 'fields')['records'][0]
        field.update(oracle_name='MiXeD Field', datatype_raw='VARCHAR2(16)',
                     default_raw='NULL', oracle_comment='  Pôvodný komentár  ')
        obj = next(d for d in docs.values() if d['kind'] == 'object')
        obj['oracle_name'] = 'MiXeD Object'
        evidence = next(d for d in docs.values() if d['kind'] == 'evidence-manifest')
        observations = evidence['result_summary']['observations']
        observations.append({'name': 'literal_null', 'value': 'NULL'})
        before = copy.deepcopy(docs)
        self.assertEqual([], validate_bundle(docs))
        self.assertEqual(before, docs)
        self.assertIsNone(observations[1]['value'])
        self.assertEqual('NULL', observations[2]['value'])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'physical.yaml'
            raw = 'name: "MiXeD Object"\ndatatype_raw: "VARCHAR2(16)"\ndefault_raw: "NULL"\nnull_value: null\ncomment: "  Pôvodný komentár  "\n'
            path.write_text(raw, encoding='utf-8')
            loaded = load_yaml(path)
            self.assertEqual('VARCHAR2(16)', loaded['datatype_raw'])
            self.assertEqual('NULL', loaded['default_raw'])
            self.assertIsNone(loaded['null_value'])
            self.assertEqual(raw, path.read_text(encoding='utf-8'))

    def test_malformed_synthetic_fixture(self):
        docs = copy.deepcopy(self.fixtures)
        next(d for d in docs.values() if d['kind'] == 'fields')['records'] = 'not a list'
        self.assertTrue(validate_bundle(docs))
        doc = self.fixture('object')
        doc['confidence'] = 0.9
        self.assert_invalid(doc)

    def test_ascii_ids_and_aliases_reject_trailing_newlines(self):
        doc = self.fixture('object')
        doc['object_id'] = 'synthetic.object.001\n'
        self.assert_invalid(doc)
        doc = self.fixture('fields')
        doc['records'][0]['canonical_alias'] = 'example_code\n'
        self.assert_invalid(doc)

    def test_timestamp_formats(self):
        for timestamp in ['2026-09-10T00:00:00Z', '2026-09-10T02:00:00+02:00']:
            doc = self.fixture('evidence-manifest')
            doc['captured_at'] = timestamp
            self.assert_valid(doc)
        for timestamp in ['2026-02-30T00:00:00Z', '2026-09-10', 'yesterday', '2026-09-10T00:00:00+01:99']:
            doc = self.fixture('evidence-manifest')
            doc['captured_at'] = timestamp
            self.assert_invalid(doc)


if __name__ == '__main__':
    unittest.main()

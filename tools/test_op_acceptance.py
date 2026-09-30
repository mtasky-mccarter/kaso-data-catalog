"""Offline engineering gates for the approved OP snapshot, not live Oracle tests."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import materialize_obchodni_partneri as m
from validate_catalog import load_yaml, validate_bundle

class OPAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p, cls.h, cls.counts=m.verify_inputs(m.ROOT,m.ROOT/m.INPUT)
        cls.docs,cls.files=m.project(cls.p,m.ROOT)
        m.preserve_closure(m.ROOT,cls.docs,cls.files)

    def test_approved_counts_and_physical_inventory(self):
        self.assertEqual(self.p['expected_counts'],self.counts)
        fields=self.p['field_records']
        self.assertEqual(87,len({r['oracle_name'] for r in fields}))
        self.assertEqual(57,sum(not r['nullable'] for r in fields))
        self.assertEqual(40,sum(r['default_raw'] is not None for r in fields))
        self.assertEqual({'NUMBER':43,'VARCHAR2':40,'DATE':3,'XMLTYPE':1},
                         {t:sum(r['data_type_raw']==t for r in fields) for t in {r['data_type_raw'] for r in fields}})
        self.assertEqual(fields,load_yaml(m.ROOT/m.DOMAIN/'fields.yaml')['records'])

    def test_deterministic_projection_and_committed_bytes(self):
        docs, files = m.project(copy.deepcopy(self.p),m.ROOT)
        m.preserve_closure(m.ROOT,docs,files)
        self.assertEqual(self.files,files)
        for rel,content in self.files.items():
            with self.subTest(path=rel):
                self.assertEqual(content.encode() if isinstance(content,str) else content,(m.ROOT/rel).read_bytes())

    def test_schema_duplicate_reference_and_evidence_checks(self):
        self.assertEqual([],validate_bundle(self.docs,m.ROOT))

    def test_hash_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/m.HANDOFF).parent.mkdir(parents=True)
            (root/m.HANDOFF).write_bytes((m.ROOT/m.HANDOFF).read_bytes())
            (root/m.INPUT).parent.mkdir(parents=True)
            (root/m.INPUT).write_bytes((m.ROOT/m.INPUT).read_bytes()+b'\n# tampered\n')
            with self.assertRaisesRegex(AssertionError,'checksum mismatch'):
                m.verify_inputs(root,root/m.INPUT)

    def test_corrected_evidence_classes_and_provenance(self):
        ev={e['evidence_id']:e for e in self.p['evidence_records']}
        self.assertNotIn('op.evidence.bundle.20260928',ev)
        self.assertNotIn('op.evidence.bundle.20260928',json.dumps(self.p))
        for suffix in ('index_expressions','scheduler_jobs','classic_jobs'):
            e=ev['op.evidence.negative.'+suffix]
            self.assertEqual('A',e['evidence_class'])
            self.assertTrue(e['limitations_sk'])
        self.assertTrue(any(r['path'].endswith('/MANIFEST.csv') for r in self.h['approved_inputs']))
        self.assertEqual(74,len([e for e in ev.values() if e.get('source_file','').endswith('.xlsx')]))

    def test_approved_profile_is_snapshot_not_live_retest(self):
        identity=self.p['profile_snapshots'][0]
        self.assertEqual('2026-09-17',identity['snapshot_date'])
        for key in ('ROW_COUNT','DISTINCT_ID','DISTINCT_RID','DATUM_VZNIKU_NULL'):
            self.assertEqual(5812,identity['metrics'][key])
        profile_docs=load_yaml(m.ROOT/m.DOMAIN/'profiles.yaml')['records']
        self.assertEqual(self.p['profile_snapshots'],[json.loads(r['observation_sk']) for r in profile_docs])

    def test_boundaries_statuses_and_source_roles_are_preserved(self):
        docs=load_yaml(m.ROOT/m.DOMAIN/'boundaries.yaml')['records']
        self.assertEqual(self.p['boundaries'],[json.loads(r['consequence_sk']) for r in docs])
        self.assertEqual({'MC.MIESTA_DODANIA','MC.KONTAKTY','MC.PARTNER_BANKY'},
                         {r['object'] for r in self.p['boundaries']})
        mutations=load_yaml(m.ROOT/m.DOMAIN/'mutations.yaml')['records']
        self.assertEqual(self.p['source_roles'],[json.loads(r['diagnostic_meaning_sk']) for r in mutations])
        self.assertTrue(all(r['role']=='DEPENDENCY ONLY' for r in self.p['direct_dependencies']))

    def test_sql_exact_copy_and_historical_publication_deferral(self):
        for r in self.p['canonical_sql']:
            self.assertEqual(r['text'],(m.ROOT/r['file']).read_text())
        self.assertFalse(any(p.startswith('generated/') for p in self.files))
        rev=load_yaml(m.ROOT/m.DOMAIN/'revisions.yaml')['records'][0]
        self.assertNotIn('documentation_version',rev)
        self.assertEqual('NONE',rev['publication_impact'])
        self.assertEqual('user',rev['publication_deferral']['approved_by'])
        revisions=load_yaml(m.ROOT/m.DOMAIN/'revisions.yaml')['records']
        if (m.ROOT/'generated/obchodni-partneri').exists():
            self.assertEqual('1.0',revisions[-1]['documentation_version'])
            self.assertEqual('INITIAL',revisions[-1]['publication_impact'])

if __name__=='__main__':
    unittest.main()

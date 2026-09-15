"""Document-backed Phase A gate; does not certify Oracle execution or AGENT-READY."""
import json
import unittest
from odb_scaffold import ROOT, read_scaffold

class ODBPhaseAAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=read_scaffold()
        cls.source=json.loads((ROOT/'evidence/source-extracts/odb/approved-contract.json').read_text())
    def test_fields_match_approved_inventory(self):
        for obj,block,count in [('obj_odb_l',337,79),('obj_odb_o',339,44)]:
            records=self.docs['fields-'+obj+'.yaml']['records']
            self.assertEqual(count,len(records))
            expected=[(r[0].split('. ',1)[1],r[1],r[2]=='Y') for r in self.source[block]['rows'][1:]]
            self.assertEqual(expected,[(r['oracle_name'],r['datatype_raw'],r['nullable']) for r in records])
            self.assertTrue(all(r['evidence_refs'] for r in records))
    def test_trigger_inventory_and_summaries_are_lossless(self):
        expected=self.source[199]['rows'][1:]
        flows=self.docs['flows.yaml']['records']
        self.assertEqual(50,len(flows))
        self.assertEqual([(r[3],r[4]) for r in expected],[(r['event_sk'],r['business_effect_sk']) for r in flows])
    def test_grouped_writers_are_not_inferred_entities(self):
        records=self.docs['mutations.yaml']['records']
        self.assertEqual(18,len(records))
        self.assertEqual([r[1] for r in self.source[195]['rows'][1:]],[r['writer_role'] for r in records])
        self.assertTrue(all(r['writer_ref'] is None for r in records))
    def test_maturity_and_precise_blockers(self):
        self.assertEqual('DIAGNOSTIC-GRADE',self.docs['contract.yaml']['maturity'])
        blocking=[r for r in self.docs['backlog.yaml']['records'] if r['blocking']]
        self.assertTrue(blocking)
        self.assertTrue(all('HANDOFF BLOCKED' in r['question_sk'] for r in blocking))
        self.assertEqual(9,len([r for r in self.docs['backlog.yaml']['records'] if not r['blocking']]))
    def test_quantity_temporal_and_guardrails(self):
        records=self.docs['temporal.yaml']['records']
        formulas=[r['transition_or_event_sk'] for r in records if r['classification']=='DERIVED CURRENT']
        self.assertEqual([r[0]+' = '+r[1] for r in self.source[179]['rows'][1:4]],formulas)
        self.assertTrue({'RAW CURRENT','DERIVED CURRENT','STORED SNAPSHOT','SELECTIVE HISTORY'} <= {r['classification'] for r in records})
        rules={r['statement_sk'] for r in self.docs['do-not-assume.yaml']['records']}
        self.assertTrue(all(r[0]+' — '+r[1] in rules for r in self.source[288]['rows'][1:]))
        joins=self.docs['relationships.yaml']['records']
        self.assertEqual(12,len(joins))
        header=joins[0]
        self.assertEqual(['mc.field.obj_odb_l.rid'],header['from_field_refs'])
        self.assertEqual(['mc.field.obj_odb_o.rid_o'],header['to_field_refs'])
        self.assertEqual('1:N',header['cardinality'])
        issue=next(r for r in joins if r['to_object_ref']=='mc.object.vyd_o')
        self.assertEqual('CONDITIONAL',issue['relationship_type'])
        self.assertIn('204',issue['condition_sk'])
    def test_source_references_do_not_become_runtime_roles(self):
        records=self.docs['dependencies.yaml']['records']
        expected=sum(int(r[2])>0 for r in self.source[343]['rows'][1:])+sum(int(r[3])>0 for r in self.source[343]['rows'][1:])
        self.assertEqual(expected,len(records))
        self.assertTrue(all(r['role']=='DEPENDENCY ONLY' and not r['source_visible'] for r in records))
        inventory=self.source[199]['rows'][1:]
        self.assertEqual(17,sum(r[0]=='OBJ_ODB_L' for r in inventory))
        self.assertEqual(33,sum(r[0]=='OBJ_ODB_O' for r in inventory))
    def test_vyd_boundary_identity_reconciliation(self):
        self.assertEqual(['vyd.oracle.f1dfff357c6da5d31924380f','vyd.oracle.c05d6994b969d9ce00ed3039'],self.docs['contract.yaml']['boundary_refs'])

if __name__=='__main__':unittest.main()

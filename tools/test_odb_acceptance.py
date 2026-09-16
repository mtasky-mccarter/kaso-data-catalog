"""Final ODB evidence/closure acceptance; no fresh Oracle execution."""
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
        records=[r for r in records if r['mutation_id'].startswith('odb.mutation.matrix_')]
        self.assertEqual(18,len(records))
        self.assertEqual([r[1] for r in self.source[195]['rows'][1:]],[r['writer_role'] for r in records])
        self.assertTrue(all(r['writer_ref'] is None for r in records))
    def test_final_backlog_preserves_history_and_nonblocking_gaps(self):
        self.assertIn(self.docs['contract.yaml']['maturity'],['DIAGNOSTIC-GRADE','AGENT-READY'])
        records=self.docs['backlog.yaml']['records']
        self.assertEqual(9,len(records));self.assertFalse(any(r['blocking'] for r in records))
        history=json.loads((ROOT/'evidence/snapshots/odb/phase-a-blocker-history.json').read_text())
        self.assertEqual(7,len(history));self.assertTrue(all(r['blocking'] for r in history))
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
        records=[r for r in self.docs['dependencies.yaml']['records'] if r['dependency_id'].startswith('odb.dependency.doc343.')]
        expected=sum(int(r[2])>0 for r in self.source[343]['rows'][1:])+sum(int(r[3])>0 for r in self.source[343]['rows'][1:])
        self.assertEqual(expected,len(records))
        self.assertTrue(all(r['role']=='DEPENDENCY ONLY' and not r['source_visible'] for r in records))
        inventory=self.source[199]['rows'][1:]
        self.assertEqual(17,sum(r[0]=='OBJ_ODB_L' for r in inventory))
        self.assertEqual(33,sum(r[0]=='OBJ_ODB_O' for r in inventory))
    def records(self,prefix):
        return [r for name,doc in self.docs.items() if name==prefix+'.yaml' or name.startswith(prefix+'-part') for r in doc['records']]
    def test_raw_physical_counts_and_checks(self):
        from collections import Counter
        records=self.docs['constraints.yaml']['records']
        self.assertEqual(130,len(records))
        for obj,expected in [('obj_odb_l',{'CHECK':56,'FOREIGN KEY':26,'UNIQUE':2,'PRIMARY KEY':1}),('obj_odb_o',{'CHECK':36,'FOREIGN KEY':8,'PRIMARY KEY':1})]:
            self.assertEqual(expected,dict(Counter(r['constraint_type'] for r in records if r['object_ref']=='mc.object.'+obj)))
        for name in ['XCE_OBJ_ODB_O_POCET_MR_POCET_V','XCE_OBJ_ODB_O_POCTY','XCE_OBJ_ODB_O_P_REZ_0']:
            r=next(r for r in records if r['oracle_name']==name)
            self.assertTrue(r['search_condition_raw'])
        check=next(r for r in records if r['oracle_name']=='XCE_OBJ_ODB_O_POCTY')
        self.assertIn('DECODE',check['search_condition_raw'].upper())
        for obj,defaults,comments in [('obj_odb_l',33,61),('obj_odb_o',29,28)]:
            fields=self.docs['fields-'+obj+'.yaml']['records']
            self.assertEqual(defaults,sum(r['default_raw'] is not None for r in fields))
            self.assertEqual(comments,sum(r['oracle_comment'] is not None for r in fields))
            self.assertTrue(all('data_default_export_value' in r for r in fields))
        indexes=self.docs['indexes.yaml']['records'];self.assertEqual(34,len(indexes))
        self.assertIn('X_OBJODBO_XML35',{r['oracle_name'] for r in indexes})
    def test_closure_nodes_edges_and_exact_seed_identity(self):
        from materialize_odb_final import bfs
        nodes=self.records('dependency-closure-nodes');edges=self.records('dependency-closure-edges');direct=self.records('dependency-direct-edges')
        self.assertEqual(58,len({(r['node_owner'],r['node_name'],r['node_type']) for r in nodes if r['min_depth']==0}))
        for direction,n,e,maxdepth,d in [('INBOUND',285,673,3,581),('OUTBOUND',477,2515,4,889)]:
            ns=[r for r in nodes if r['direction']==direction];es=[r for r in edges if r['direction']==direction]
            self.assertEqual((n,e,maxdepth,d),(len(ns),len(es),max(r['min_depth'] for r in ns),sum(r['direction']==direction for r in direct)))
            seeds={(r['node_owner'],r['node_name'],r['node_type']) for r in ns if r['min_depth']==0}
            raw=[dict(OWNER=r['source_owner'],NAME=r['source_name'],TYPE=r['source_type'],REFERENCED_OWNER=r['referenced_owner'],REFERENCED_NAME=r['referenced_name'],REFERENCED_TYPE=r['referenced_type'],DEPENDENCY_TYPE=r['dependency_type']) for r in es]
            distances,reached=bfs(raw,seeds,direction)
            self.assertEqual({(r['node_owner'],r['node_name'],r['node_type']):r['min_depth'] for r in ns},distances)
            self.assertEqual(len(es),len(reached))
        self.assertEqual(5,max(r['min_depth'] for r in edges if r['direction']=='OUTBOUND')) # closing/cyclic edge, not a fifth-depth node
    def test_api_case_normalization_is_lossless(self):
        from collections import Counter
        from materialize_odb_final import API_RE
        records=self.records('api-references');self.assertEqual(4515,len(records))
        self.assertEqual(145,len({(r['caller_owner'],r['caller_name'],r['caller_type']) for r in records}))
        self.assertEqual({'D_OBJ_ODB_L':2629,'D_OBJ_ODB_L_B':185,'D_OBJ_ODB_O':1701},dict(Counter(r['target_package'] for r in records)))
        self.assertEqual({'D_OBJ_ODB_L':300,'D_OBJ_ODB_L_B':59,'D_OBJ_ODB_O':236},dict(Counter(p for p,m in {(r['target_package'],r['member_name_normalized']) for r in records})))
        for r in records:
            self.assertEqual('MC',r['caller_owner']);self.assertEqual('SOURCE MEMBER REFERENCE',r['classification'])
            self.assertEqual(r['member_name_raw'].upper(),r['member_name_normalized'])
            self.assertEqual(r['reference_raw'],r['source_text_raw'][r['occurrence_column']-1:r['occurrence_column']-1+len(r['reference_raw'])])
    def test_core_source_package_types_and_direct_writers(self):
        from collections import Counter
        source=[r for p in (ROOT/'evidence/snapshots/odb/core-source').glob('*.json') for r in json.loads(p.read_text())]
        counts=Counter((r['NAME'],r['TYPE']) for r in source)
        self.assertEqual(50,len([k for k in counts if k[1]=='TRIGGER']))
        for name,spec,body in [('D_OBJ_ODB_L',1215,21533),('D_OBJ_ODB_L_B',225,3118),('D_OBJ_ODB_O',761,15801)]:
            self.assertEqual(spec,counts[(name,'PACKAGE')]);self.assertEqual(body,counts[(name,'PACKAGE BODY')])
        writers=[r for r in self.docs['dependencies.yaml']['records'] if r['dependency_id'].startswith('odb.dependency.core_writer.')]
        self.assertEqual(6,len(writers));self.assertTrue(all(r['role']=='DIRECT WRITER' and r['source_visible'] for r in writers))
        self.assertEqual(2,len([r for r in writers if '.d_obj_odb_l_b.' in r['dependency_id']]))
    def test_access_and_job_audit_limits(self):
        from collections import Counter
        access=[r for r in self.docs['dependencies.yaml']['records'] if r['role']=='ACCESS CAPABILITY']
        self.assertEqual({'GRANT':71,'SYNONYM':9},dict(Counter(r['oracle_object_type'] for r in access)))
        jobs=[r for r in self.docs['data-quality.yaml']['records'] if r['dq_id'].startswith('odb.dq.job.')]
        self.assertEqual(2,len(jobs));self.assertTrue(all('result_row_count = 0' in r['observation_sk'] and 'wrapper' in r['interpretation_limit_sk'] for r in jobs))
    def test_vyd_boundary_identity_reconciliation(self):
        self.assertEqual(['vyd.oracle.f1dfff357c6da5d31924380f','vyd.oracle.c05d6994b969d9ce00ed3039'],self.docs['contract.yaml']['boundary_refs'])

if __name__=='__main__':unittest.main()

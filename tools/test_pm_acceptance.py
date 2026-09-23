"""Product Master losslessness and semantic acceptance, using retained approved evidence.

Offline tests validate catalog representation, not current Oracle populations.
"""
import hashlib
import json
from pathlib import Path
import re
import unittest

import openpyxl
import yaml

ROOT=Path(__file__).resolve().parents[1]
DOMAIN=ROOT/'catalog/master/skladove-karty'
SNAP=ROOT/'evidence/snapshots/skladove-karty'

def doc(name):return yaml.safe_load((DOMAIN/(name+'.yaml')).read_text())
def records(name):return doc(name)['records']
def workbook(name):
    w=openpyxl.load_workbook(SNAP/(name+'.xlsx'),read_only=True,data_only=False)
    try:
        rr=list(w.active.iter_rows(values_only=True));return [dict(zip(rr[0],r)) for r in rr[1:]]
    finally:w.close()

class ProductMasterAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fields=records('fields-sklad_karta')
        cls.byname={r['oracle_name']:r for r in cls.fields}
        cls.rules={r['rule_id']:r for r in records('do-not-assume')}

    def test_lossless_root_inventory_against_supplied_bytes(self):
        source=workbook('mp01-a')
        self.assertEqual(169,len(source));self.assertEqual(169,len(self.fields))
        self.assertEqual([r['COLUMN_NAME'] for r in source],[r['oracle_name'] for r in self.fields])
        for s in source:
            c=self.byname[s['COLUMN_NAME']]
            for raw,canonical in [('COLUMN_ID','ordinal_position'),('DATA_TYPE','data_type_raw'),('DATA_LENGTH','data_length'),('DATA_PRECISION','data_precision'),('DATA_SCALE','data_scale'),('DATA_DEFAULT','data_default_export_value'),('COMMENTS','oracle_comment')]:self.assertEqual(s[raw],c[canonical],(s['COLUMN_NAME'],raw))
            self.assertEqual(s['NULLABLE']=='Y',c['nullable'])
            self.assertIsNotNone(c['canonical_alias']) # approved dictionary; exact mapping tested separately
        self.assertEqual({'NUMBER':110,'VARCHAR2':55,'DATE':3,'XMLTYPE':1},{t:sum(r['data_type_raw']==t for r in self.fields) for t in ['NUMBER','VARCHAR2','DATE','XMLTYPE']})

    def test_root_constraints_losslessly_preserved(self):
        src=workbook('mp01-b');actual={r['oracle_name']:r for r in records('constraints') if r['object_ref']=='pm.object.sklad_karta'}
        self.assertEqual(set(s['CONSTRAINT_NAME'] for s in src),set(actual))
        self.assertEqual(32,sum(r['constraint_type']=='R' for r in actual.values()))
        for s in src:
            r=actual[s['CONSTRAINT_NAME']]
            for a,b in [('CONSTRAINT_TYPE','constraint_type'),('STATUS','enabled_state'),('VALIDATED','validated_state'),('DELETE_RULE','delete_rule'),('DEFERRABLE','deferrable_raw'),('DEFERRED','deferred_raw')]:self.assertEqual(s[a],r[b])
            if s['COLUMN_NAME']:self.assertIn('pm.field.sklad_karta.'+s['COLUMN_NAME'].lower(),r['column_refs'])
            if s['SEARCH_CONDITION'] is not None:self.assertEqual(s['SEARCH_CONDITION'],r['search_condition_raw'])
        self.assertEqual(['pm.field.sklad_karta.id'],actual['XPK_SKLAD_KARTA']['column_refs'])
        self.assertTrue(any(r['constraint_type']=='U' and set(r['column_refs'])=={'pm.field.sklad_karta.int_kod','pm.field.sklad_karta.sklad'} for r in actual.values()))

    def test_index_inventory_and_hidden_columns(self):
        src=workbook('mp01-d');actual={r['oracle_name']:r for r in records('indexes') if r['object_ref']=='pm.object.sklad_karta'}
        self.assertEqual(35,len(src));self.assertEqual(31,len(actual))
        for s in src:
            r=actual[s['INDEX_NAME']];self.assertEqual(s['UNIQUENESS'],r['uniqueness'])
            col=next(x for x in r['column_or_expression_entries'] if x['position']==s['COLUMN_POSITION'])
            self.assertEqual(s['DESCEND'],col['direction'])
            self.assertTrue(col.get('field_ref','').endswith('.'+s['COLUMN_NAME'].lower()) or col.get('oracle_column_name_raw')==s['COLUMN_NAME'])

    def test_direct_triggers_and_dependency_surface(self):
        src=workbook('mp01-e');self.assertEqual(21,len(src));self.assertEqual({'ENABLED'},{r['STATUS'] for r in src})
        flows={r['flow_id']:r for r in records('flows')}
        for r in src:self.assertIn('pm.flow.trigger.'+r['TRIGGER_NAME'].lower(),flows)
        deps=records('dependencies')
        self.assertEqual(416,sum(r['dependency_id'].startswith('pm.dependency.mp01-g.') for r in deps))
        direct=[r for r in deps if r['dependency_id'].startswith('pm.dependency.mp01-g.')]
        self.assertEqual(414,len({r['source_ref'] for r in direct if r['target_ref']=='pm.object.sklad_karta'}))
        self.assertEqual(33,sum(r['role']=='DIRECT WRITER' for r in deps))
        for r in direct:self.assertEqual('DEPENDENCY ONLY',r['role'])
        for r in deps:
            if r['dependency_id'].startswith('pm.access.'):self.assertEqual('ACCESS CAPABILITY',r['role'])
        self.assertEqual(324,len(records('relationships-inbound')))

    def test_relationship_grains_and_boundaries(self):
        rels={r['relationship_id']:r for r in records('relationships')}
        for key in ['typed_notes','note_type','supplier','vat','partner_codes','store_logistics','packaging','packaging_codes','coefficients','coefficient_dictionary','supplemental','nahrada']:
            r=rels['pm.rel.'+key]
            for field in ['cardinality','condition_sk','safe_usage_sk','fanout_risk']:self.assertTrue(r[field])
        c=doc('contract');self.assertEqual('MC',c['authoritative_environment'])
        for boundary in ['Kusy','Blokácie','Pasívne kusy','Manufacturing','Orders','Issues','Receipts','Pricing']:self.assertIn(boundary,c['scope_excludes'])

    def test_dated_population_and_group_counts(self):
        r=workbook('mp02-a')[0];self.assertEqual(7429,r['ROW_COUNT'])
        m=yaml.safe_load((ROOT/'evidence/manifests/skladove-karty/mp02-a.yaml').read_text())
        self.assertEqual('2026-09-14',m['snapshot_date'])
        v={o['name']:o['value'] for o in m['result_summary']['observations']}
        self.assertEqual(7429,v['root_rows']);self.assertEqual(100,v['id_sk_id_match_percent']);self.assertEqual(100,v['rid_rid_obj_match_percent'])
        groups=workbook('pm-10f');self.assertEqual(164,len(groups))
        for col,count in [('MEMBER_CNT',3162),('SELF_CNT',164),('OTHER_CNT',2998),('USED1_CNT',837)]:self.assertEqual(count,sum(r[col] for r in groups))
        for r in records('data-quality'):self.assertRegex(r['snapshot_date'],r'^2026-09-\d\d$')

    def test_semantic_handoff_retained_without_loss(self):
        hand=(ROOT/'docs/handoffs/skladove-karty/READY_FOR_CODEX_HANDOFF_skladove_karty.md').read_text()
        sections={int(n):text.strip() for n,text in re.findall(r'^## (\d+)\. ([\s\S]*?)(?=^## \d+\.|\Z)',hand,re.M)}
        for n in [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,29]:self.assertEqual(sections[n],self.rules[f'pm.rule.handoff_section_{n:02}']['statement_sk'])
        dna=re.findall(r'^(\d+)\. (.+)$',sections[19],re.M);self.assertEqual(60,len(dna))
        for n,text in dna:self.assertEqual(text,self.rules[f'pm.rule.do_not_assume_{int(n):02}']['statement_sk'])

    def test_operational_authority_and_temporal_limits(self):
        self.assertIn('does not mean in sale',self.byname['USED']['business_definition_sk'])
        self.assertIn('independent from USED',self.byname['STAV']['business_definition_sk'])
        for name in ['FLAGS_A','ALERGENY']:self.assertIn('typed notes',self.byname[name]['business_definition_sk'])
        self.assertIn('not creation',self.byname['N_STAMP']['business_definition_sk'])
        self.assertIn('unconfirmed',self.byname['NAHRADA']['business_definition_sk'])
        self.assertIn('unresolved',self.byname['TYP_T']['business_definition_sk'])
        self.assertIn('coefficients is valid',self.byname['FLAGS']['business_definition_sk'])
        self.assertFalse(next(r for r in records('temporal') if r['temporal_rule_id']=='pm.temporal.raw_current')['reconstructable'])

    def test_end_of_sale_delta_includes_exception_and_normal_guard(self):
        flows={r['flow_id']:r for r in records('flows')}
        flow=flows['pm.flow.end_of_sale'];lock=flows['pm.flow.forecast_lock']
        self.assertEqual([],lock['direct_mutations'])
        self.assertEqual([],flow.get('direct_mutations',[]))
        self.assertTrue(flow['side_effects'])
        self.assertTrue(flows['pm.flow.end_of_sale_reset']['direct_mutations'])
        for token in ['PLAN_POCET2=0','POZN','Ukončený predaj','OPTyp_Prognoza','OPTyp_PrognPartn']:self.assertIn(token,flow['business_effect_sk'])
        self.assertIn('GetReplikacia',flow['session_or_bypass_sk'])
        self.assertIn("NEW.POZN LIKE '%Ukončený predaj%'",lock['condition_sk'])
        for token in ['BITAND(NEW.STAV,2)=2','ordinary','Not a global lock bypass','insert-time protection']:self.assertIn(token,lock['business_effect_sk'])
        rows=workbook('pm-12a');mc=[r for r in rows if r['OWNER']=='MC']
        source=''.join(r['TEXT'] or '' for r in mc if r['NAME']=='T_OBCH_PL_LOCK_MC')
        self.assertIn("like '%Ukončený predaj%'",source);self.assertIn('bitand(:new.stav, 2) = 2',source)
        ddl={r['LAST_DDL_TIME'].isoformat() if hasattr(r['LAST_DDL_TIME'],'isoformat') else r['LAST_DDL_TIME'] for r in mc if r['NAME']=='T_OBCH_PL_LOCK_MC'}
        self.assertEqual({'2026-09-16T09:39:59'},ddl)
        rev=next(r for r in records('revisions') if r['revision_id']=='pm.revision.1_0_mc_20260916')
        self.assertFalse(rev['breaking_change']);self.assertEqual('2026-09-16',rev['date'])
        self.assertIn('Old defect:',rev['change_sk']);self.assertIn('Resolved behavior:',rev['change_sk'])

    def test_report_and_coefficient_incidents_preserved(self):
        dq={r['dq_id']:r for r in records('data-quality')}
        for i in range(1,7):self.assertIn(f'pm.dq.coef_{i:03}',dq)
        report=dq['pm.dq.report_001'];self.assertEqual('POTVRDENÉ',report['status'])
        for token in ['CRITICAL','Both SK and CZ','not master']:self.assertIn(token,report['observation_sk'])
        r=workbook('pm-11p')[0]
        self.assertAlmostEqual(154.416745,r['TONY_ALL'],places=6)
        self.assertAlmostEqual(150.787039,r['TONY_FLAG12_OK'],places=6)
        self.assertAlmostEqual(3.629706,r['TONY_FLAG12_EXCL'],places=6)

    def test_backlog_and_publication_approval(self):
        b=records('backlog');self.assertEqual(7,len(b));self.assertFalse(any(r['blocking'] for r in b))
        hand=yaml.safe_load((ROOT/'docs/handoffs/skladove-karty/handoff.yaml').read_text())
        self.assertEqual('1.0',hand['target']['documentation_version']);self.assertTrue(hand['publication']['enabled'])
        from check_codex_handoff import validate
        self.assertEqual([],validate(hand)[0])
        self.assertTrue(any(r['revision_id']=='pm.revision.1_0_publication_20260923' for r in records('revisions')))

    def test_evidence_integrity_and_registry_links(self):
        manifests=list((ROOT/'evidence/manifests/skladove-karty').glob('*.yaml'));self.assertEqual(169,len(manifests)) # original 166 + two alias sources + publication approval
        for p in manifests:
            m=yaml.safe_load(p.read_text());self.assertRegex(m['sha256'],r'^[a-f0-9]{64}$')
            if m['raw_retained']:self.assertEqual(m['sha256'],hashlib.sha256((ROOT/m['repository_path']).read_bytes()).hexdigest())
        all_docs=[yaml.safe_load(p.read_text()) for p in DOMAIN.glob('*.yaml')]
        top={d.get('id',d.get('object_id',d.get('contract_id'))) for d in all_docs}
        self.assertTrue(set(doc('contract')['component_refs'])<=top)

if __name__=='__main__':unittest.main()

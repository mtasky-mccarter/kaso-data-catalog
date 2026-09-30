"""Delta intake, canonical versions, history and routing regressions."""
import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import yaml
from check_codex_handoff import validate
from lean_handoff import execution_plan
from publication_versions import resolve_versions
from generate_publication import generate_one, PUBLICATIONS
from check_publication_governance import audit, transition_errors
from plan_change_validation import plan
ROOT=Path(__file__).resolve().parents[1]

class LeanExecutionTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);self.temp=t
        self.git('init','-q');self.git('config','user.email','fixture@example.invalid');self.git('config','user.name','Fixture')
        self.put('catalog/test/contract.yaml',{'contract_id':'test.contract','maturity':'AGENT-READY','authoritative_environment':'MC'})
        self.old={'revision_id':'test.revision.1','contract_version':'1.0'}
        self.put('catalog/test/revisions.yaml',{'records':[self.old]})
        self.put('catalog/test/fields.yaml',{'records':[{'field_id':'test.field'}]});self.base=self.commit()
        self.put('evidence/delta.yaml',{'delta_id':'test.delta','evidence_id':'test.evidence','records':[{'field_id':'test.new'}]})
        self.data={'schema_version':'2.0','kind':'codex-handoff','handoff_id':'test.handoff','status':'READY_FOR_CODEX_HANDOFF','mode':'UPDATE_DOMAIN',
          'repository':{'name':'fixture','base_commit':self.base},'scope':{'domain':'test','slug':'test','canonical_path':'catalog/test/','authoritative_environment':'MC'},
          'canonical_base':{'contract_ref':'test.contract','revision_ref':'test.revision.1'},
          'delta':{'revision_id':'test.revision.2','classification':'NON_BREAKING_SEMANTIC','semantic_change':True,'changed_record_refs':['test.field','test.new'],'record_paths':['catalog/test/fields.yaml'],'approved_evidence_refs':['test.evidence'],'approved_delta_refs':['test.delta']},
          'approved_inputs':[{'path':'evidence/delta.yaml','sha256':hashlib.sha256((self.root/'evidence/delta.yaml').read_bytes()).hexdigest()}],
          'backlog_delta':{'blocking_count':0,'added':[],'resolved':[],'nonblocking_changed':[]},'publication':{'impact':'REGENERATE','documentation_version':'1.1'},
          'execution':{'materializer_commands':['python tools/materialize.py'],'domain_tests':['python -m unittest test_domain'],'sql_tests':[],'publication_tests':[]},
          'repository_actions':{'create_or_update':['catalog/test/fields.yaml'],'preserve':[],'forbidden':[]},'stop_conditions':['Missing approved evidence.']}
    def git(self,*args):return subprocess.run(['git',*args],cwd=self.root,check=True,capture_output=True,text=True).stdout.strip()
    def commit(self):self.git('add','.');self.git('commit','-qm','fixture');return self.git('rev-parse','HEAD')
    def put(self,path,data):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(yaml.safe_dump(data,sort_keys=False))
    def errors(self):return validate(self.data,self.root)[0]
    def test_exact_base_inheritance_and_compact_plan(self):
        self.assertEqual([],self.errors());self.put('catalog/test/contract.yaml',{'contract_id':'uncommitted.different'})
        self.assertEqual([],self.errors());p=execution_plan(self.data)
        self.assertEqual(self.base,p['base_sha']);self.assertNotIn('semantic_contract',p);self.assertLess(len(json.dumps(p)),1500)
    def test_all_modes_and_structured_create_package(self):
        for mode in ['UPDATE_DOMAIN','EVIDENCE_REFRESH','PUBLICATION_ONLY','CLOSURE','REPOSITORY_GOVERNANCE']:
            self.data['mode']=mode
            self.data['delta'].update(semantic_change=mode not in ('PUBLICATION_ONLY','REPOSITORY_GOVERNANCE'),classification='TOOLING_ONLY' if mode in ('PUBLICATION_ONLY','REPOSITORY_GOVERNANCE') else 'NON_BREAKING_SEMANTIC')
            self.assertEqual([],self.errors(),mode)
        self.data['delta'].update(semantic_change=True,classification='NON_BREAKING_SEMANTIC')
        self.data['mode']='CREATE_DOMAIN';self.data['scope']['canonical_path']='catalog/new/';self.data.pop('canonical_base');self.data['target']={'maturity':'AGENT-READY'}
        self.data['materialization_package']={'path':'evidence/delta.yaml','expected_counts':{'fields':2}}
        self.assertEqual([],self.errors());self.data['execution']['materializer_commands']=[];self.assertTrue(self.errors())
    def test_bad_refs_checksum_base_and_paths_fail_closed(self):
        original=copy.deepcopy(self.data)
        for mutate in [lambda d:d['canonical_base'].update(contract_ref='wrong'),lambda d:d['canonical_base'].update(revision_ref='wrong'),lambda d:d['delta'].update(approved_delta_refs=['absent']),lambda d:d['delta'].update(changed_record_refs=['absent']),lambda d:d['approved_inputs'][0].update(sha256='0'*64),lambda d:d['repository'].update(base_commit='0'*40),lambda d:d['approved_inputs'][0].update(path='../outside')]:
            self.data=copy.deepcopy(original);mutate(self.data);self.assertTrue(self.errors())
    def test_prose_replay_and_unapproved_closure_rejected(self):
        self.data['semantic_contract']={'grain':['repeat']};self.assertTrue(self.errors());self.data.pop('semantic_contract')
        self.data['mode']='CLOSURE';self.data['publication']={'impact':'NONE'};self.assertTrue(self.errors())
        self.data['publication']['deferral']={'approved_by':'user','canonical_revision_ref':'test.revision.2','evidence_ref':'test.evidence','reason':'Explicit user approval'}
        self.assertEqual([],self.errors());self.data['target']={'maturity':'AGENT-READY'};self.data['backlog_delta']['blocking_count']=1;self.assertTrue(self.errors())
    def test_documentation_version_separate_and_legacy_fallback(self):
        p='catalog/test/revisions.yaml';self.assertEqual(('1.0','1.0',False),resolve_versions(self.root,p))
        self.put(p,{'records':[{'contract_version':'1.0','documentation_version':'1.0'},{'contract_version':'1.0','documentation_version':'1.1'}]})
        self.assertEqual(('1.0','1.1',True),resolve_versions(self.root,p))
        self.put(p,{'records':[{'contract_version':'1.0','documentation_version':'1.1'},{'contract_version':'1.0','documentation_version':'1.0'}]})
        with self.assertRaises(ValueError):resolve_versions(self.root,p)
    def test_unregistered_closed_domain_blocked(self):self.assertTrue(any('no registered' in e for e in audit(self.root,{})))
    def test_current_repository_publications_pass(self):self.assertEqual([],audit(ROOT))
    def test_history_cannot_be_overwritten(self):
        p=self.root/'generated/test/v1.pdf';p.parent.mkdir(parents=True);p.write_bytes(b'old');base=self.commit()
        p.write_bytes(b'new');self.commit();self.assertTrue(any('history' in e for e in transition_errors(self.root,base,{})))
    def test_canonical_change_requires_additive_classified_revision(self):
        self.put('catalog/test/fields.yaml',{'records':[{'field_id':'test.field','meaning':'approved'}]});self.commit()
        self.assertTrue(any('additive revision' in e for e in transition_errors(self.root,self.base,{})))
        self.put('catalog/test/revisions.yaml',{'records':[self.old,{'revision_id':'test.revision.2','contract_version':'1.0'}]});self.commit()
        self.assertTrue(any('classification' in e for e in transition_errors(self.root,self.base,{})))
    def test_visible_revision_requires_version_advance(self):
        rows=[self.old,{'revision_id':'test.revision.2','contract_version':'1.0','documentation_version':'1.0','change_classification':'NON_BREAKING_SEMANTIC','publication_impact':'REGENERATE'}]
        self.put('catalog/test/revisions.yaml',{'records':rows});self.commit();conf={'test':{'revisions':'catalog/test/revisions.yaml'}}
        self.assertTrue(any('advance documentation_version' in e for e in transition_errors(self.root,self.base,conf)))
        rows[-1]['documentation_version']='1.1';self.put('catalog/test/revisions.yaml',{'records':rows});self.commit()
        self.assertEqual([],transition_errors(self.root,self.base,conf))
    def test_orchestrator_never_overwrites_old_family(self):
        config={'subject_sk':'test','revisions':'catalog/test/revisions.yaml'};source=self.root/'stage';source.mkdir()
        doc=source/'x.docx';pdf=source/'x.pdf';manifest=source/'x.manifest.yaml';doc.write_bytes(b'doc');pdf.write_bytes(b'pdf');manifest.write_text('{}')
        with patch.dict(PUBLICATIONS,{'fixture':config}),patch('generate_publication.run_domain_generator',return_value=(doc,pdf,manifest)):
            outputs=generate_one(self.root,'fixture',self.root/'generated');before=[p.read_bytes() for p in outputs];doc.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError,'overwrite'):generate_one(self.root,'fixture',self.root/'generated')
            self.assertEqual(before,[p.read_bytes() for p in outputs])
    def test_generic_gate_detects_missing_stale_wrong_version_and_hash(self):
        from generate_publication import publication_basename
        config={'subject_sk':'test','revisions':'catalog/test/revisions.yaml'}
        base=publication_basename(config,'1.0');directory=self.root/'generated/test';directory.mkdir(parents=True)
        artifacts=[]
        for ext in ('.docx','.pdf'):
            p=directory/(base+ext);p.write_bytes(b'fixture')
            artifacts.append({'path':str(p.relative_to(self.root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        m={'publication_slug':'test','publication_title':base,'contract_version':'1.0','canonical_input_sha256':'digest','canonical_inputs':['catalog/test/fields.yaml'],'artifacts':artifacts}
        manifest='generated/test/'+base+'.manifest.yaml';self.put(manifest,m)
        with patch('check_publication_governance.generator_digest',return_value=('digest',['catalog/test/fields.yaml'])),patch('check_publication_governance.check_document',return_value=[]):
            self.assertEqual([],audit(self.root,{'test':config}))
            for key,value in [('canonical_input_sha256','stale'),('contract_version','9.9'),('publication_title','wrong')]:
                broken=copy.deepcopy(m);broken[key]=value;self.put(manifest,broken);self.assertTrue(audit(self.root,{'test':config}))
            self.put(manifest,m);(directory/(base+'.pdf')).write_bytes(b'tampered');self.assertTrue(any('hash mismatch' in e for e in audit(self.root,{'test':config})))
            (directory/(base+'.pdf')).unlink();self.assertTrue(audit(self.root,{'test':config}))
            self.assertTrue(any('no registration' in e for e in audit(self.root,{})))

    def test_new_documentation_version_preserves_contract_and_history(self):
        config={'subject_sk':'test','revisions':'catalog/test/revisions.yaml'};source=self.root/'stage';source.mkdir()
        doc=source/'x.docx';pdf=source/'x.pdf';manifest=source/'x.manifest.yaml';doc.write_bytes(b'doc');pdf.write_bytes(b'pdf');manifest.write_text('{}')
        with patch.dict(PUBLICATIONS,{'fixture':config}),patch('generate_publication.run_domain_generator',return_value=(doc,pdf,manifest)):
            old=generate_one(self.root,'fixture',self.root/'generated');before=[p.read_bytes() for p in old]
            self.put('catalog/test/revisions.yaml',{'records':[self.old,{'contract_version':'1.0','documentation_version':'1.1'}]})
            doc.write_bytes(b'new');new=generate_one(self.root,'fixture',self.root/'generated')
            m=yaml.safe_load(new[2].read_text());self.assertEqual('1.0',m['contract_version']);self.assertEqual('1.1',m['documentation_version'])
            self.assertTrue(all('v1.1' in p.name for p in new));self.assertEqual(before,[p.read_bytes() for p in old])

    def test_product_master_is_registered_without_historical_deferral(self):
        from check_publication_governance import current_deferral
        self.assertEqual(6, len(PUBLICATIONS))
        self.assertEqual('catalog/master/skladove-karty/revisions.yaml', PUBLICATIONS['skladove-karty']['revisions'])
        self.assertFalse(current_deferral(ROOT, 'catalog/master/skladove-karty', []))

    def test_product_master_uses_normal_documentation_versions(self):
        from generate_pm_publication import model
        current = model(ROOT)
        self.assertEqual(('1.0', '1.0'), (current['version'], current['documentation_version']))
        with patch('generate_pm_publication.resolve_versions', return_value=('1.0', '1.1', True)):
            updated = model(ROOT)
        self.assertEqual(('1.0', '1.1'), (updated['version'], updated['documentation_version']))
        self.assertEqual(current['docs'], updated['docs'])
        self.assertEqual(current['sql'], updated['sql'])

    def test_scope_router_is_conservative(self):
        self.assertEqual(['skladove-karty'],plan(['catalog/master/skladove-karty/fields.yaml'])['affected_domains'])
        for paths in [['tools/generate_publication.py'],['schema/revisions.schema.json'],['catalog/new/unknown.yaml'],['sql/diagnostic/example.sql'],['evidence/manifests/x.yaml']]:self.assertTrue(plan(paths)['repository_wide_publication_check'])
        self.assertFalse(plan(['docs/codex-execution-standard-v4.md'])['repository_wide_publication_check'])
if __name__=='__main__':unittest.main()

#!/usr/bin/env python3
"""Deterministic projection of approved OP records; never reads Oracle/XLSX content.

The retained package is the exact source representation. Canonical registries
normalize its keys to existing schemas. Source-only attributes are preserved as
JSON in schema-supported descriptions, not silently discarded or reclassified.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import sys
import yaml
from validate_catalog import load_yaml, validate_bundle

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = Path('catalog/master/obchodni-partneri')
INPUT = Path('evidence/snapshots/obchodni-partneri/materialization-package.yaml')
HANDOFF = Path('docs/handoffs/obchodni-partneri/handoff.yaml')
OBJECT = 'op.object.obch_partneri'

class Dumper(yaml.SafeDumper):
    def ignore_aliases(self, value):
        return True

def dump(value):
    return yaml.dump(value, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=110)

def raw(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_inputs(root, package_path):
    h = load_yaml(root / HANDOFF)
    assert package_path == root / INPUT, 'Unexpected materialization input'
    for entry in h['approved_inputs']:
        path = (root / entry['path']).resolve()
        assert path.is_relative_to(root.resolve()), 'Input outside repository'
        assert digest(path) == entry['sha256'], 'Input checksum mismatch: ' + entry['path']
    p = load_yaml(package_path)
    assert p['repository']['base_commit'] == h['repository']['base_commit']
    subprocess.run(['git', 'cat-file', '-e', h['repository']['base_commit']+'^{commit}'], cwd=root, check=True)
    rows = list(csv.DictReader((root/INPUT.parent/'MANIFEST.csv').open(encoding='utf-8-sig', newline='')))
    for row in rows:
        path = (root/row['relative_path']).resolve()
        assert path.is_relative_to(root.resolve())
        assert path.stat().st_size == int(row['size_bytes'])
        assert digest(path) == row['sha256']
    counts = {key: len(p[key]) for key in ('field_records','constraint_records','index_records')}
    counts.update(constraint_rows=sum(len(r['columns']) for r in p['constraint_records']),
                  index_rows=sum(len(r['columns']) for r in p['index_records']),
                  trigger_records=len(p['trigger_flows']), outbound_fk_records=len(p['outbound_relationships']),
                  inbound_fk_records=len(p['inbound_relationships']), direct_dependency_rows=len(p['direct_dependencies']),
                  raw_evidence_files=len(rows), canonical_sql_files=len(p['canonical_sql']),
                  blocking_backlog=sum(r['blocking'] for r in p['backlog']))
    # MP06 physical object count is retained in the approved invariant; the
    # structured reference contracts include a separately approved soft join.
    counts['reference_objects_mp06'] = len({r['target_object'] for r in p['reference_contracts']})
    assert counts == p['expected_counts'] == h['materialization_package']['expected_counts'], (counts,p['expected_counts'])
    return p, h, counts

def project(p, root):
    documents = {}
    files = {}
    entities = {}
    field_ids = {r['oracle_name']:r['field_id'] for r in p['field_records']}
    constraints = {r['oracle_name']:r['constraint_id'] for r in p['constraint_records']}
    def field(name):
        return field_ids[name]
    def reg(kind, records, name=None, **extra):
        name = name or kind
        rid = 'op.registry.'+name.replace('-', '_')
        documents[str(DOMAIN/(name+'.yaml'))] = dict(schema_version='1.0',kind=kind,id=rid,records=records,**extra)
        return rid
    def entity(full, typ, evidence, columns=(), visible=False):
        if full == 'MC.OBCH_PARTNERI' and typ == 'TABLE':
            return OBJECT, [field(c) for c in columns]
        owner,name = full.split('.',1)
        key = 'op.entity.'+owner.lower()+'.'+name.lower()+'.'+typ.lower().replace(' ','_')
        if key not in entities:
            entities[key] = dict(oracle_entity_id=key,environment='MC',oracle_owner=owner,oracle_name=name,
                                 oracle_object_type=typ,source_visible=visible,boundary_only=True,
                                 status='TECHNICKY ZNÁME',evidence_refs=list(evidence),fields=[])
        e=entities[key]
        e['source_visible'] = e['source_visible'] or visible
        e['evidence_refs']=list(dict.fromkeys(e['evidence_refs']+list(evidence)))
        for c in columns:
            fid=key+'.'+c.lower()
            if not any(f['oracle_field_id']==fid for f in e['fields']):
                e['fields'].append(dict(oracle_field_id=fid,oracle_name=c,status='TECHNICKY ZNÁME',evidence_refs=list(evidence)))
        return key,[key+'.'+c.lower() for c in columns]
    def detail(r, idkey, scope=None):
        return dict(dq_id=r[idkey],scope_refs=scope or [OBJECT],observation_sk=raw(r),blocking=False,
                    status=r.get('status','TECHNICKY ZNÁME') if r.get('status')!='BOUNDARY' else 'TECHNICKY ZNÁME',
                    evidence_refs=r.get('evidence_refs',[]),snapshot_date=r.get('snapshot_date'))

    reg('fields',p['field_records'],object_ref=OBJECT)
    obj=dict(schema_version='1.0',kind='object',**p['object_record'],field_registry_ref='op.registry.fields')
    documents[str(DOMAIN/'object-obch_partneri.yaml')]=obj
    cs=[]
    for r in p['constraint_records']:
        d=dict(constraint_id=r['constraint_id'],object_ref=OBJECT,oracle_name=r['oracle_name'],constraint_type=r['constraint_type'],
               column_refs=[field(c) for c in r['columns']],enabled_state=r['status'],validated_state=r['validated'],
               status=r['mapping_status'],evidence_refs=r['evidence_refs'],search_condition_raw=r['search_condition_raw'],
               delete_rule=r['delete_rule'],referenced_owner_raw=r['referenced_owner'],deferrable_raw=r['deferrable'],deferred_raw=r['deferred'])
        if r['referenced_table']:
            d['referenced_object_ref'],d['referenced_column_refs']=entity(r['referenced_owner']+'.'+r['referenced_table'],'TABLE',r['evidence_refs'],r['referenced_columns'])
        cs.append(d)
    reg('constraints',cs)
    reg('indexes',[dict(index_id=r['index_id'],object_ref=OBJECT,oracle_name=r['oracle_name'],uniqueness=r['uniqueness'],
        status='TECHNICKY ZNÁME',evidence_refs=r['evidence_refs'],index_type_raw=r['index_type'],oracle_status_raw=r['status'],
        column_or_expression_entries=[dict(position=i+1,field_ref=field(c),direction=r['descend'][i]) for i,c in enumerate(r['columns'])]) for r in p['index_records']])
    rels=[]
    for r in p['outbound_relationships']+p['inbound_relationships']:
        src,sfields=entity(r['from_object'],'TABLE',r['evidence_refs'],r['from_columns'])
        dst,tfields=entity(r['to_object'],'TABLE',r['evidence_refs'],r['to_columns'])
        d=dict(relationship_id=r['relationship_id'],from_object_ref=src,from_field_refs=sfields,to_object_ref=dst,to_field_refs=tfields,
               relationship_type='DIRECT',status=r['status'],evidence_refs=r['evidence_refs'],validation_summary_sk=raw(r))
        if r in p['outbound_relationships']: d['physical_constraint_ref']=constraints[r['constraint_name']]
        rels.append(d)
    for r in p['reference_contracts']:
        dst,tfields=entity(r['target_object'],'TABLE',r['evidence_refs'],r['target_fields'])
        rels.append(dict(relationship_id=r['reference_id'],from_object_ref=OBJECT,from_field_refs=[field(c) for c in r['source_fields']],
                         to_object_ref=dst,to_field_refs=tfields,relationship_type='DIRECT',status=r['status'],evidence_refs=r['evidence_refs'],
                         safe_usage_sk=r['temporal_rule'],validation_summary_sk=raw(r)))
    reg('relationships',rels)
    deps=[]
    for r in p['direct_dependencies']:
        src,_=entity(r['source_owner']+'.'+r['source_name'],r['source_type'],r['evidence_refs'])
        dst,_=entity(r['target_owner']+'.'+r['target_name'],r['target_type'],r['evidence_refs'])
        deps.append(dict(dependency_id=r['dependency_id'],source_ref=src,target_ref=dst,oracle_object_type=r['source_type'],
                         direction=r['direction'],depth=1,role=r['role'],discovery_method='ALL_DEPENDENCIES',source_visible=False,
                         runtime_boundary=True,status=r['status'],evidence_refs=r['evidence_refs'],limitations_sk=[raw(r)]))
    reg('dependencies',deps)
    flows=[]
    for r in p['trigger_flows']:
        src,_=entity('MC.'+r['oracle_name'],'TRIGGER',r['evidence_refs'],visible=True)
        flows.append(dict(flow_id=r['flow_id'],trigger_or_procedure_ref=src,event_sk=r['event_sk'],watched_field_refs=[field(c) for c in r['watched_fields']],
                          session_or_bypass_sk=r['session_or_bypass_sk'],business_effect_sk=r['business_effect_sk'],diagnostic_meaning_sk=raw(r),evidence_refs=r['evidence_refs']))
    reg('flows',flows)
    api=[]
    for r in p['api_contracts']:
        src,_=entity('MC.C_PARTNER','PACKAGE',r['evidence_refs'],visible=True)
        api.append(dict(flow_id=r['api_id'],trigger_or_procedure_ref=src,business_effect_sk=r['meaning_sk'],diagnostic_meaning_sk=raw(r),evidence_refs=r['evidence_refs']))
    reg('flows',api,'api-contracts')
    # Package/object-level DML evidence does not identify individual target fields.
    mutations=[]
    for r in p['source_roles']:
        matches=[(d['source_type'],d['source_owner']) for d in p['direct_dependencies'] if d['source_name']==r['source_object']]
        src=None
        if matches:
            typ,owner=matches[0]
            src,_=entity(owner+'.'+r['source_object'],typ,r['evidence_refs'],visible=True)
        mutations.append(dict(mutation_id=r['source_role_id'],target_refs=[OBJECT],writer_ref=src,writer_role=r['role'],status=r['status'],evidence_refs=r['evidence_refs'],diagnostic_meaning_sk=raw(r)))
    reg('mutations',mutations)
    vals=[]
    for r in p['value_domains']:
        for i,v in enumerate(r['values']):
            vals.append(dict(value_domain_id=r['value_domain_id'] if i==0 else r['value_domain_id']+'.'+str(i),scope_ref=field(r['scope_field']),
                             raw_value=v['raw'],business_label_sk=v['label_sk'],status=r['status'],evidence_refs=r['evidence_refs']))
    reg('value-domains',vals)
    temporal=[]
    for r in p['temporal_rules']:
        scopes=[field(s) if s in field_ids else entity(s,'TABLE',r['evidence_refs'])[0] for s in r['scope']]
        temporal.append(dict(temporal_rule_id=r['temporal_rule_id'],scope_refs=scopes,classification=r['classification'],reconstructable=r['reconstructable'],
                             history_limitations_sk=r['rule_sk'],status=r['status'],evidence_refs=r['evidence_refs']))
    reg('temporal',temporal)
    reg('data-quality',[dict(r,scope_refs=[OBJECT]) for r in p['data_quality']])
    reg('do-not-assume',[dict(rule_id=r['rule_id'],scope_refs=[OBJECT],statement_sk=r['statement_sk'],consequence_sk='Approved status: '+r['status'],evidence_refs=r['evidence_refs']) for r in p['do_not_assume']])
    # Boundary tags remain literal text; do not promote satellite lifecycle.
    reg('do-not-assume',[dict(rule_id=r['boundary_id'],scope_refs=[OBJECT],statement_sk=r['reason_sk'],consequence_sk=raw(r),evidence_refs=r['evidence_refs']) for r in p['boundaries']],'boundaries')
    reg('backlog',[dict(backlog_id=r['backlog_id'],scope_refs=[OBJECT],status=r['status'],blocking=r['blocking'],question_sk=r['question_sk'],
                        proposed_test_sk=r['next_step_sk'],related_evidence_refs=r['evidence_refs']) for r in p['backlog']])
    reg('data-quality',[detail(r,'profile_id') for r in p['profile_snapshots']],'profiles')
    # Bulk lookup exports remain checksummed structured evidence in the package;
    # no new historic-label or satellite attribute contracts are inferred.
    sqls=[]
    for r in p['canonical_sql']:
        files[r['file']]=r['text']
        sqls.append(dict(sql_id=r['sql_id'],title_sk=Path(r['file']).stem,sql_file=r['file'],purpose_sk='\n'.join(x[3:] for x in r['text'].splitlines() if x.startswith('-- ')),
                         compatibility={k:r[k] for k in ('sql_client','oracle_server_version','read_only')},evidence_refs=p['contract']['evidence_refs']))
    reg('sql-registry',sqls)
    reg('oracle-entities',list(entities.values()))
    revision=dict(p['revision'])
    revision['publication_deferral']=dict(approved_by='user',reason=revision['publication_no_impact_reason'],evidence_refs=['op.evidence.delivery_scope'])
    reg('revisions',[revision])
    contract={k:v for k,v in p['contract'].items() if k not in ('slug','contract_version','blocking_backlog_count')}
    documents[str(DOMAIN/'contract.yaml')]=dict(schema_version='1.0',kind='contract',**contract,purpose_sk=p['contract']['title_sk'],
        component_refs=[v['id'] for v in documents.values() if 'id' in v])
    supports={e['evidence_id']:[] for e in p['evidence_records']}
    def walk(x):
        if isinstance(x,dict):
            rid=next((v for k,v in x.items() if k=='id' or k.endswith('_id')),None)
            if rid:
                for e in x.get('evidence_refs',[])+x.get('related_evidence_refs',[]):
                    if e in supports:supports[e].append(rid)
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    for doc in documents.values():walk(doc)
    for e in p['evidence_records']:
        source=e.get('source_file')
        d=dict(schema_version='1.0',kind='evidence-manifest',evidence_id=e['evidence_id'],evidence_class=e['evidence_class'],environment='MC',oracle_owner='MC',
               snapshot_date=e['snapshot_date'],retention_class='SNAPSHOT_CRITICAL',raw_retained=True,
               supports_record_refs=list(dict.fromkeys(supports[e['evidence_id']])),review_status=e.get('review_status','APPROVED'),
               limitations_sk=e.get('limitations_sk',[]),result_summary_sk=raw(e))
        if source:
            # Canonical path grammar is ASCII/no-spaces; keep original source name
            # and make a byte-identical retained copy, never alter approved input.
            dest=str(INPUT.parent/'retained'/(e['evidence_id'].removeprefix('op.evidence.')+'.xlsx'))
            files[dest]=(root/source).read_bytes()
            d.update(source_file=source,repository_path=dest,sha256=e['sha256'])
        else:
            d.update(source_file=str(INPUT),repository_path=str(INPUT),sha256=digest(root/INPUT))
        documents['evidence/manifests/obchodni-partneri/'+e['evidence_id']+'.yaml']=d
    approval='evidence/snapshots/obchodni-partneri/delivery-scope.md'
    documents['evidence/manifests/obchodni-partneri/op.evidence.delivery_scope.yaml']=dict(schema_version='1.0',kind='evidence-manifest',
        evidence_id='op.evidence.delivery_scope',evidence_class='D',environment='MC',oracle_owner='MC',retention_class='SNAPSHOT_CRITICAL',raw_retained=True,
        repository_path=approval,sha256=digest(root/approval),supports_record_refs=[revision['revision_id']],review_status='APPROVED',
        result_summary_sk='Explicit user instruction: CREATE_DOMAIN delivery excludes publication and documentation_version decisions.')
    for path,doc in documents.items():files[path]=dump(doc)
    return documents,files

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('package',type=Path)
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args(argv)
    p,h,counts=verify_inputs(ROOT,args.package.resolve())
    docs,files=project(p,ROOT)
    # Validate against a temporary projection before changing repository outputs.
    with tempfile.TemporaryDirectory(prefix='op-materialize-') as tmp:
        stage=Path(tmp)
        staged=dict(files)
        for rel in (str(INPUT),'evidence/snapshots/obchodni-partneri/delivery-scope.md'):
            staged[rel]=(ROOT/rel).read_bytes()
        for rel,content in staged.items():
            path=stage/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(content.encode('utf-8') if isinstance(content,str) else content)
        errors=validate_bundle(docs,stage)
        if errors:
            print('\n'.join(errors),file=sys.stderr)
            return 1
        for rel,content in files.items():
            path=ROOT/rel
            data=content.encode('utf-8') if isinstance(content,str) else content
            if args.check:
                assert path.is_file() and path.read_bytes()==data, 'Output drift: '+rel
            else:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(data)
    print(json.dumps(dict(status='PASS',counts=counts,canonical_documents=len(docs),output_files=len(files)),ensure_ascii=False))
    return 0

if __name__=='__main__':
    raise SystemExit(main())

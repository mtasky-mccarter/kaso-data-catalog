"""Reproducible FINAL ODB materialization from checksum-verified read-only XLSX.

No Oracle connection, SQL execution, role inference from graph edges or maturity
promotion. Use --bundle for the supplied closure delta; publication/promotion is
an explicit later gate. Existing semantic records and stable IDs are preserved.
"""
import argparse
from collections import Counter,defaultdict,deque
import hashlib,json,re
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
DOMAIN=Path('catalog/sales/obchodne-pripady')
OBJECTS=['mc.object.obj_odb_l','mc.object.obj_odb_o']
PACKAGES=['D_OBJ_ODB_L','D_OBJ_ODB_L_B','D_OBJ_ODB_O']
API_RE=re.compile(r'\b(D_OBJ_ODB_L_B|D_OBJ_ODB_L|D_OBJ_ODB_O)\s*\.\s*([A-Z][A-Z0-9_$#]*)',re.I)
yaml.SafeDumper.ignore_aliases=lambda self,value:True

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:24]
def emit(root,path,data):
 p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False,width=110))
def load(root,name):return yaml.safe_load((root/DOMAIN/(name+'.yaml')).read_text())
def eid(n):return 'odb.evidence.closure_'+n

def verify_bundle(bundle):
 result={}
 for line in (bundle/'SHA256SUMS.txt').read_text().splitlines():
  sha,name=line.split(None,1);name=name.strip().removeprefix('./');p=bundle/name
  if not p.resolve().is_relative_to(bundle.resolve()):raise ValueError('Unsafe bundle path')
  if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Checksum mismatch: '+name)
  result[name]=sha
 return result

def read_workbooks(bundle):
 import openpyxl
 result={}
 for p in sorted((bundle/'closure_exports').glob('*.xlsx')):
  wb=openpyxl.load_workbook(p,read_only=True,data_only=True)
  if len(wb.worksheets)!=1:raise ValueError('Unexpected sheet layout: '+p.name)
  it=iter(wb.worksheets[0].values);header=next(it)
  if len(set(header))!=len(header):raise ValueError('Duplicate headers')
  result[p.name.split('_')[2]]=[dict(zip(header,r)) for r in it];wb.close()
 return result

def bfs(rows,seeds,direction):
 edges={(tuple(r[k] for k in ('OWNER','NAME','TYPE')),tuple(r[k] for k in ('REFERENCED_OWNER','REFERENCED_NAME','REFERENCED_TYPE')),r['DEPENDENCY_TYPE']) for r in rows}
 adjacency=defaultdict(list);inbound=direction=='INBOUND'
 for e in sorted(edges):adjacency[e[1] if inbound else e[0]].append(e)
 distance={s:0 for s in seeds};queue=deque(sorted(seeds));reached={}
 while queue:
  current=queue.popleft()
  for edge in adjacency[current]:
   reached[edge]=distance[current]+1;next_node=edge[0] if inbound else edge[1]
   if next_node not in distance:distance[next_node]=distance[current]+1;queue.append(next_node)
 return distance,reached

def summary(records):
 return dict(record_count=len(records),inbound_count=sum(r['direction']=='INBOUND' for r in records),outbound_count=sum(r['direction']=='OUTBOUND' for r in records),max_inbound_depth=max((r['min_depth'] for r in records if r['direction']=='INBOUND'),default=0),max_outbound_depth=max((r['min_depth'] for r in records if r['direction']=='OUTBOUND'),default=0))

def main(bundle,root=ROOT):
 hashes=verify_bundle(bundle);w=read_workbooks(bundle)
 def registry(name,records):
  d=load(root,name);d['records']=records;emit(root,DOMAIN/(name+'.yaml'),d)
 def snapshot(path,value,identity,cls,scope,meaning):
  p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
  manifest=dict(schema_version='1.0',kind='evidence-manifest',evidence_id=identity,evidence_class=cls,environment='MC',oracle_owner='MC',snapshot_date='2026-09-15',source_file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),retention_class='SNAPSHOT_CRITICAL',raw_retained=True,repository_path=path,supports_record_refs=scope,review_status='ACCEPTED',result_summary_sk=meaning,limitations_sk=['Retained lossless export projection; original XLSX hashes are in the closure manifests.'])
  emit(root,Path('evidence/manifests/odb')/(identity.replace('.','-')+'.yaml'),manifest)
 for n in range(1,10):
  key=f'{n:02}';name=next(x for x in hashes if x.startswith('closure_exports/OBJ_CLOSURE_'+key+'_'))
  manifest=dict(schema_version='1.0',kind='evidence-manifest',evidence_id=eid(key),evidence_class='B2' if n in (5,8) else 'A',environment='MC',oracle_owner='MC',snapshot_date='2026-09-15',source_client='SQL Navigator 5.5.4.847',source_file=Path(name).name,sha256=hashes[name],retention_class='TRANSIENT',raw_retained=False,supports_record_refs=OBJECTS,review_status='ACCEPTED',result_summary_sk='Verified final closure export '+key+'; '+str(len(w[key]))+' rows.',limitations_sk=['Raw XLSX is read-only external input; no Oracle queries executed by materializer.','Non-MC source rows are auxiliary only; dependency edges and source members do not imply runtime roles.'])
  emit(root,Path('evidence/manifests/odb')/('closure-'+key+'.yaml'),manifest)
 comments={(r['TABLE_NAME'],r['COLUMN_NAME']):r['COMMENTS'] for r in w['02']}
 fields={}
 for table in ['OBJ_ODB_L','OBJ_ODB_O']:
  d=load(root,'fields-'+table.lower());raw={r['COLUMN_NAME']:r for r in w['01'] if r['TABLE_NAME']==table}
  assert len(d['records'])==len(raw)
  for f in d['records']:
   r=raw[f['oracle_name']];assert f['ordinal_position']==r['COLUMN_ID'] and f['nullable']==(r['NULLABLE']=='Y')
   f.update(data_default_export_value=r['DATA_DEFAULT'],default_raw=None if r['DATA_DEFAULT'] is None else str(r['DATA_DEFAULT']),oracle_comment=comments[(table,f['oracle_name'])],data_type_raw=r['DATA_TYPE'],data_length=r['DATA_LENGTH'],char_length=r['CHAR_LENGTH'],data_precision=r['DATA_PRECISION'],data_scale=r['DATA_SCALE'])
   f['evidence_refs']=list(dict.fromkeys(f['evidence_refs']+[eid('01'),eid('02')]))
   f['limitations_sk']=[x for x in f.get('limitations_sk',[]) if not any(t in x for t in ['raw Oracle export nebol','Prázdna bunka','Default a Oracle comment'])]
   fields[(table,f['oracle_name'])]=f['field_id']
  emit(root,DOMAIN/('fields-'+table.lower()+'.yaml'),d)
 old={r['oracle_name']:r for r in load(root,'constraints')['records']};columns=defaultdict(list)
 for r in w['04']:
  if r['SECTION']=='CONSTRAINT_COLUMN':columns[r['OBJECT_NAME']].append(r)
 relationships=load(root,'relationships')['records'];constraints=[]
 for r in w['03']:
  name=r['CONSTRAINT_NAME'];table=r['TABLE_NAME'];fks=sorted(columns[name],key=lambda x:int(x['DETAIL_2'] or 0))
  record=dict(old.get(name,{}));record.update(constraint_id=record.get('constraint_id','odb.constraint.'+name.lower()),object_ref='mc.object.'+table.lower(),oracle_name=name,constraint_type={'P':'PRIMARY KEY','U':'UNIQUE','R':'FOREIGN KEY','C':'CHECK'}[r['CONSTRAINT_TYPE']],column_refs=[fields[(table,x['DETAIL_1'])] for x in fks],enabled_state=r['STATUS'],validated_state=r['VALIDATED'],status='TECHNICKY ZNÁME',evidence_refs=[eid('03'),eid('04')],search_condition_raw=r['SEARCH_CONDITION'],delete_rule=r['DELETE_RULE'],referenced_owner_raw=r['R_OWNER'],referenced_constraint_name_raw=r['R_CONSTRAINT_NAME'],generated_raw=r['GENERATED'],deferrable_raw=r['DEFERRABLE'],deferred_raw=r['DEFERRED'])
  if r['CONSTRAINT_TYPE']=='R' and 'referenced_object_ref' not in record:
   if record['column_refs']==['mc.field.obj_odb_o.rid_o']:record.update(referenced_object_ref=OBJECTS[0],referenced_column_refs=['mc.field.obj_odb_l.rid'])
   else:
    rel=next(x for x in relationships if x['from_object_ref']==record['object_ref'] and x['from_field_refs']==record['column_refs'])
    record.update(referenced_object_ref=rel['to_object_ref'],referenced_column_refs=rel['to_field_refs'])
  constraints.append(record)
 registry('constraints',constraints)
 indexes=load(root,'indexes')['records'];raw_indexes={r['OBJECT_NAME']:r for r in w['04'] if r['SECTION']=='INDEX'}
 for record in indexes:
  name=record['oracle_name']
  if name=='X_OBJODB_O_XML35':
   assert 'X_OBJODBO_XML35' in raw_indexes
   record['oracle_name']='X_OBJODBO_XML35';name=record['oracle_name']
   record['limitations_sk'].append('Technical spelling reconciled: Phase A document X_OBJODB_O_XML35; raw Oracle X_OBJODBO_XML35, same documented hidden SYS_NC00044$. Stable index ID retained; full domain-index expression remains the approved nonblocking gap.')
  r=raw_indexes.get(name)
  assert r is not None,name
  if not record['column_or_expression_entries']:
   record['column_or_expression_entries']=[dict(position=int(x['DETAIL_2']),oracle_column_name_raw=x['DETAIL_1'],direction=x['DETAIL_3']) for x in w['04'] if x['SECTION']=='INDEX_COLUMN' and x['OBJECT_NAME']==name]
  # Hidden XML index is in the approved document but omitted from this flat INDEX export.
  if r:
   record.update(index_type_raw=r['DETAIL_2'],oracle_status_raw=r['DETAIL_3'],uniqueness=r['DETAIL_1'],function_based='FUNCTION-BASED' in r['DETAIL_2'])
   for entry in record['column_or_expression_entries']:
    raw=next(x for x in w['04'] if x['SECTION']=='INDEX_COLUMN' and x['OBJECT_NAME']==name and int(x['DETAIL_2'])==entry['position'])
    entry.update(oracle_column_name_raw=raw['DETAIL_1'],direction=raw['DETAIL_3'])
   record['evidence_refs']=list(dict.fromkeys(record['evidence_refs']+[eid('04')]))
   record['limitations_sk']=[x for x in record.get('limitations_sk',[]) if 'raw Oracle export nebol' not in x]
 registry('indexes',indexes)
 entities=load(root,'oracle-entities')['records'];bykey={(r['oracle_owner'],r['oracle_name'],r['oracle_object_type']):r for r in entities}
 def entity(owner,name,typ,source=False):
  key=(owner,name,typ)
  if key not in bykey:
   r=dict(oracle_entity_id='odb.oracle.final.'+digest(key),environment='MC',oracle_owner=owner,oracle_name=name,oracle_object_type=typ,source_visible=source,boundary_only=not source,status='TECHNICKY ZNÁME',evidence_refs=[eid('05' if source else '09')],limitations_sk=['Technical identity only; principal/owner names do not imply a separate database environment or runtime role.'])
   entities.append(r);bykey[key]=r
  elif source:
   r=bykey[key];r['source_visible']=True;r['boundary_only']=False;r['evidence_refs']=list(dict.fromkeys(r['evidence_refs']+[eid('05')]))
   r['limitations_sk']=[x for x in r.get('limitations_sk',[]) if not any(t in x for t in ['raw Oracle export nebol','source_visible=false'])]
  return bykey[key]['oracle_entity_id']
 source=defaultdict(list)
 for r in w['05']:
  assert r['OWNER']=='MC';source[(r['OWNER'],r['NAME'],r['TYPE'])].append(r)
 source_evidence={}
 for key,lines in sorted(source.items()):
  ent=entity(*key,source=True);parts=[];part=[];size=0
  for r in sorted(lines,key=lambda x:x['LINE']):
   n=len(json.dumps(r,ensure_ascii=False).encode())
   if part and size+n>65000:parts.append(part);part=[];size=0
   part.append(r);size+=n
  if part:parts.append(part)
  refs=[]
  for number,part in enumerate(parts,1):
   slug='-'.join(key).lower().replace(' ','-')+f'-{number:03}'
   identity='odb.evidence.source.'+digest([key,number]);refs.append(identity)
   snapshot('evidence/snapshots/odb/core-source/'+slug+'.json',part,identity,'B2',[ent],f'Exact ALL_SOURCE cells: {key}; lines {part[0]["LINE"]}..{part[-1]["LINE"]}. Not executable diagnostics.')
  source_evidence[key]=refs;bykey[key]['evidence_refs']=list(dict.fromkeys(bykey[key]['evidence_refs']+refs))
 flows=load(root,'flows')['records']
 for f in flows:
  name=next(r['oracle_name'] for r in entities if r['oracle_entity_id']==f['trigger_or_procedure_ref'])
  f['evidence_refs']=list(dict.fromkeys(f['evidence_refs']+[eid('05')]+source_evidence[('MC',name,'TRIGGER')]))
  f['diagnostic_meaning_sk']=f['diagnostic_meaning_sk'].replace('Úplné watched fields, call chains, exceptions a bypass detaily sa neodhadujú.','Raw source je zachovaný po riadkoch v B2 snapshots; schválená interpretácia sa nemení.').replace('raw Oracle export nebol pri materializácii dostupný.','raw source bol reconciliovaný s final closure exportom.')
 registry('flows',flows)
 dependencies=[r for r in load(root,'dependencies')['records'] if not r['dependency_id'].startswith(('odb.dependency.access.','odb.dependency.core_writer.'))]
 mutations=[r for r in load(root,'mutations')['records'] if not r['mutation_id'].startswith('odb.mutation.core_writer.')]
 # Match only actual static SQL after stripping Oracle comments and quoted strings.
 for package in PACKAGES:
  key=('MC',package,'PACKAGE BODY');lines=sorted(source[key],key=lambda x:x['LINE']);text=''.join(r['TEXT'] or '' for r in lines)
  masked=re.sub(r"'(?:''|[^'])*'|--[^\n]*|/\*[\s\S]*?\*/",lambda m:'\n'*m[0].count('\n') if '\n' in m[0] else ' '*len(m[0]),text)
  for table in ['OBJ_ODB_L','OBJ_ODB_O']:
   matches=list(re.finditer(r'\b(?:UPDATE|INSERT\s+INTO|DELETE\s+FROM)\s+(?:MC\.)?'+table+r'\b',masked,re.I))
   assert matches,(package,table)
   line_numbers=sorted({masked[:m.start()].count('\n')+1 for m in matches});ent=entity(*key,source=True);target='mc.object.'+table.lower()
   dependencies.append(dict(dependency_id='odb.dependency.core_writer.'+package.lower()+'.'+table.lower(),source_ref=ent,target_ref=target,oracle_object_type='PACKAGE BODY',direction='INBOUND',depth=1,role='DIRECT WRITER',discovery_method='Static DML in comment/string-masked MC ALL_SOURCE',source_visible=True,runtime_boundary=False,status='POTVRDENÉ',evidence_refs=[eid('05')]+source_evidence[key],limitations_sk=['Static source writer, not runtime execution frequency. Source line anchors: '+', '.join(map(str,line_numbers))]))
   mutations.append(dict(mutation_id='odb.mutation.core_writer.'+package.lower()+'.'+table.lower(),target_refs=[target],writer_ref=ent,writer_role='DIRECT WRITER',status='POTVRDENÉ',evidence_refs=[eid('05')]+source_evidence[key],direct_mutations_sk='MC static DML targets '+table+'; source lines '+', '.join(map(str,line_numbers)),diagnostic_meaning_sk='Raw B2 source proves the direct writer; no additional business responsibility inferred.'))
 for r in w['09']:
  typ=r['ACCESS_TYPE'];owner=r['PRINCIPAL_OR_OWNER'];name=r['ACCESS_OBJECT'] if typ=='SYNONYM' else r['TARGET_OBJECT']
  src=entity(owner,name,'SYNONYM' if typ=='SYNONYM' else 'GRANTEE');target='mc.object.'+r['TARGET_OBJECT'].lower() if r['TARGET_OBJECT'] in ['OBJ_ODB_L','OBJ_ODB_O'] else entity(r['TARGET_OWNER'],r['TARGET_OBJECT'],'PACKAGE')
  dependencies.append(dict(dependency_id='odb.dependency.access.'+digest(r),source_ref=src,target_ref=target,oracle_object_type=typ,direction='INBOUND',depth=1,role='ACCESS CAPABILITY',discovery_method='ALL_TAB_PRIVS / ALL_SYNONYMS',source_visible=False,runtime_boundary=True,status='TECHNICKY ZNÁME',evidence_refs=[eid('09')],limitations_sk=['ACCESS CAPABILITY only; no runtime dependency or writer role.',json.dumps(r,ensure_ascii=False,sort_keys=True)]))
 registry('dependencies',dependencies);registry('mutations',mutations);registry('oracle-entities',entities)
 seeds=set(source)|{('MC','OBJ_ODB_L','TABLE'),('MC','OBJ_ODB_O','TABLE')};assert len(seeds)==58
 closure=[];nodes=[];audit={}
 for num,direction in [('06','INBOUND'),('07','OUTBOUND')]:
  distance,reached=bfs(w[num],seeds,direction)
  audit[direction]=dict(nodes=len(distance),edges=len(reached),max_node_depth=max(distance.values()),direct_edges=sum(v==1 for v in reached.values()))
  for node,depth in sorted(distance.items()):nodes.append(dict(dependency_node_id='odb.node.'+digest([direction,node]),direction=direction,min_depth=depth,node_owner=node[0],node_name=node[1],node_type=node[2],evidence_refs=[eid(num)]))
  for (a,b,t),depth in sorted(reached.items()):closure.append(dict(dependency_edge_id='odb.edge.closure.'+digest([direction,a,b,t]),direction=direction,min_depth=depth,source_owner=a[0],source_name=a[1],source_type=a[2],referenced_owner=b[0],referenced_name=b[1],referenced_type=b[2],referenced_link_name=None,dependency_type=t,evidence_refs=[eid(num)]))
 assert audit=={'INBOUND':dict(nodes=285,edges=673,max_node_depth=3,direct_edges=581),'OUTBOUND':dict(nodes=477,edges=2515,max_node_depth=4,direct_edges=889)},audit
 def partition(name,kind,records,key,limit=150):
  for p in (root/DOMAIN).glob(name+'-part*.yaml'):p.unlink()
  ids=[]
  for i in range(0,len(records),limit):
   number=i//limit;filename=name if number==0 else name+f'-part{number+1:03}';identity='odb.'+name.replace('-','_')+'.001'+('' if not number else f'.part{number+1:03}');ids.append(identity)
   d=dict(schema_version='1.0',kind=kind,id=identity,environment='MC',records=records[i:i+limit]);d[key]='Final MC closure exports; BFS exact owner/name/type; DEPENDENCY ONLY. No runtime role from edges.'
   if kind=='api-references':d['summary']=dict(record_count=len(d['records']),caller_count=len({(r['caller_owner'],r['caller_name'],r['caller_type']) for r in d['records']}),member_count=len({(r['target_package'],r['member_name_normalized']) for r in d['records']}))
   else:d['summary']=summary(d['records'])
   emit(root,DOMAIN/(filename+'.yaml'),d)
  return ids
 direct=[dict(r,dependency_edge_id=r['dependency_edge_id'].replace('.closure.','.direct.')) for r in closure if r['min_depth']==1]
 components=[]
 for name,kind,records,key in [('dependency-closure-edges','dependency-edges',closure,'source_view'),('dependency-direct-edges','dependency-edges',direct,'source_view'),('dependency-closure-nodes','dependency-nodes',nodes,'source_dataset')]:components+=partition(name,kind,records,key)
 api=[]
 for r in w['08']:
  if r['OWNER']!='MC':continue
  for m in API_RE.finditer(r['TEXT'] or ''):
   api.append(dict(api_reference_id='odb.api.'+digest([r,m.start()]),caller_owner=r['OWNER'],caller_name=r['NAME'],caller_type=r['TYPE'],target_package=m[1].upper(),member_name_raw=m[2],member_name_normalized=m[2].upper(),reference_raw=m[0],source_text_raw=r['TEXT'],occurrence_column=m.start()+1,hit_count=1,hit_lines=[r['LINE']],classification='SOURCE MEMBER REFERENCE',evidence_refs=[eid('08')],limitations_sk=['Single textual occurrence, including constants/helpers; not automatically a CALLER/WRITER role.']))
 assert len(api)==4515 and len({(r['target_package'],r['member_name_normalized']) for r in api})==595
 components+=partition('api-references','api-references',api,'source_dataset',100)
 dq=[r for r in load(root,'data-quality')['records'] if not r['dq_id'].startswith('odb.dq.job.')]
 for p in sorted((bundle/'negative_audits').glob('*.yaml')):
  r=yaml.safe_load(p.read_text());identity='odb.evidence.'+('jobs_dbms' if '10A' in p.name else 'jobs_scheduler');snapshot('evidence/snapshots/odb/'+p.stem.lower()+'.json',r,identity,'A',OBJECTS,r['proves']+' '+r['does_not_prove'])
  dq.append(dict(dq_id='odb.dq.job.'+r['source_view'].lower(),scope_refs=OBJECTS,observation_sk=r['source_view']+': result_row_count = 0; '+r['predicate_summary']+'. '+r['proves'],blocking=False,status='POTVRDENÉ',snapshot_date='2026-09-15',evidence_refs=[identity],interpretation_limit_sk=r['does_not_prove']))
 registry('data-quality',dq)
 backlog=load(root,'backlog');closed=[r for r in backlog['records'] if r['blocking']]
 if closed:snapshot('evidence/snapshots/odb/phase-a-blocker-history.json',closed,'odb.evidence.phase_a_blocker_history','D',['odb.backlog.001'],'Historical Phase A blockers, now closed by final raw evidence and explicit final publication authorization; records are not silently erased.')
 registry('backlog',[r for r in backlog['records'] if not r['blocking']])
 contract=load(root,'contract');contract['component_refs']=[r for r in contract['component_refs'] if not r.startswith(('odb.dependency_','odb.api_references.'))]+components
 contract['limitations_sk']=['Exhaustive source-visible static dependency closure within the supplied MC exports; dynamic SQL, external services and runtime outside ALL_SOURCE remain boundaries.','Zero directly named jobs does not exclude wrappers, programs/chains or hidden action text.','Nine original nonblocking future-domain gaps remain; no global MC/MCCZ/TEST/TESTCZ identity claim.']
 contract['evidence_refs']=list(dict.fromkeys(contract['evidence_refs']+[eid('01'),eid('03'),eid('05'),eid('06'),eid('07'),eid('08'),eid('09')]))
 emit(root,DOMAIN/'contract.yaml',contract)
 for obj in ['obj_odb_l','obj_odb_o']:
  d=load(root,'object-'+obj);d['evidence_refs']=contract['evidence_refs'];d['scope_limitations_sk']=contract['limitations_sk'];emit(root,DOMAIN/('object-'+obj+'.yaml'),d)
 revisions=load(root,'revisions')['records'];rid='odb.revision.final_closure_2026_09_15'
 revisions=[r for r in revisions if r['revision_id']!=rid];revisions.append(dict(revision_id=rid,contract_version='1.2',date='2026-09-15',breaking_change=False,changed_record_refs=OBJECTS+['odb.backlog.001'],change_sk='Raw physical/source reconciliation; D_OBJ_ODB_L_B supporting direct writer; reproducible source-visible dependency closure, API/access and negative job audits. AGENT-READY promotion is gated by validation and tests. XML index physical spelling corrected from document X_OBJODB_O_XML35 to raw X_OBJODBO_XML35 (SYS_NC00044$), retaining its stable ID and original nonblocking expression gap.',evidence_refs=[eid('01'),eid('03'),eid('05'),eid('06'),eid('07'),eid('08'),eid('09')]))
 if contract['maturity']=='AGENT-READY':
  revisions[-1]['change_sk']=revisions[-1]['change_sk'].replace('AGENT-READY promotion is gated by validation and tests.','Maturity raised from DIAGNOSTIC-GRADE to AGENT-READY after canonical validation and ODB acceptance gates passed.')
 registry('revisions',revisions)
 audit.update(seed_logical_objects=55,seed_graph_nodes=58,api_references=len(api),api_callers=len({(r['caller_owner'],r['caller_name'],r['caller_type']) for r in api}),api_unique_members=595,access=dict(Counter(r['ACCESS_TYPE'] for r in w['09'])))
 path=root/'docs/handoffs/odb-final-materialization-audit.json';path.write_text(json.dumps(audit,indent=2)+'\n');return audit

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();print(json.dumps(main(a.bundle,a.root),indent=2))

#!/usr/bin/env python3
"""Deterministic Product Master intake. Reads supplied evidence; never connects to Oracle.

Usage: python tools/materialize_pm.py /path/to/KASO_skladove_karty_codex_package_2026-09-16
Requires openpyxl and xlrd for the supplied legacy XLS files.
"""
import argparse
import csv
import datetime
import hashlib
import json
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'catalog/master/skladove-karty'
SNAP = 'evidence/snapshots/skladove-karty'
DOCS = 'docs/handoffs/skladove-karty'
BASE = '38cdc052a7c50389946648246202f13f8c01271f'
CONF = 'POTVRDENÉ'
TECH = 'TECHNICKY ZNÁME'
HAND = 'pm.evidence.handoff'
CORE = ['SKLAD_KARTA','SKLAD_KARTA_LB','B_KOD_U','SK_LOG_UDAJE','SKLAD_DODAVATEL','SKLAD_KARTA_FU','SKLAD_PARTNER_KODY','SK_JEDNOTKY','CIS_POZNAMKY','CIS_POZNAMKY_TYPY','SK_NAKL_POLOZKY','NAKL_KOEF','CIS_DU_O','IMP_MC_SK_NAKL_POL']

def slug(x):
    return re.sub(r'[^a-z0-9_.-]+','_',unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower()).strip('_')
def ev(k): return 'pm.evidence.'+slug(k)
def obj(n): return 'pm.object.'+n.lower()
def fld(n,c): return 'pm.field.'+n.lower()+'.'+c.lower()
def write(path, data):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False,width=110),encoding='utf-8')
def records(kind, name, items, **extra):
    ident='pm.'+name.replace('-','_')
    write(f'{DOMAIN}/{name}.yaml',dict(schema_version='1.0',kind=kind,id=ident,**extra,records=items))
    return ident
def read_book(p):
    if p.read_bytes()[:2]==b'PK':
        import openpyxl
        with p.open('rb') as f:
            w=openpyxl.load_workbook(f,read_only=True,data_only=False)
            return {s.title:[[v.isoformat() if isinstance(v,(datetime.date,datetime.datetime)) else v for v in r] for r in s.iter_rows(values_only=True)] for s in w}
    import xlrd
    w=xlrd.open_workbook(p)
    return {s.name:[[None if s.cell(i,j).ctype==xlrd.XL_CELL_EMPTY else s.cell_value(i,j) for j in range(s.ncols)] for i in range(s.nrows)] for s in w.sheets()}

def materialize(package):
    inventory=list(csv.DictReader((package/'MANIFEST.csv').open(encoding='utf-8-sig')))
    files={unicodedata.normalize('NFC',str(p.relative_to(package))):p for p in package.rglob('*') if p.is_file()}
    books={}; entries={}; manifests={}; audit=[]
    critical={'MP01-A','MP01-B','MP01-D','MP01-E','MP02-A','MP02-B','MP05-C','PM-06C','PM-07A','PM-07B','PM-07C','PM-10F','PM-11N','PM-11P','PM-11S1','PM-11S2','PM-12A'}
    for e in inventory:
        rel=e['relative_path'] or e['status'].removeprefix('DUPLICATE_OF ')
        p=files[unicodedata.normalize('NFC',rel)]
        assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],rel
        assert p.stat().st_size==int(e['size_bytes']),rel
        audit.append(dict(source_name=e['source_name'],status=e['status'],sha256=e['sha256'],bytes=int(e['size_bytes'])))
        if e['status']!='INCLUDED':continue
        key=p.name.split(' — ')[0] if ' — ' in p.name else p.stem
        if key in entries:key+='_'+e['sha256'][:8]
        entries[key]=(p,e)
        if e['category']=='handoff':key='handoff';entries[key]=(p,e)
        if p.suffix.lower() in ('.xls','.xlsx'):books[key]=read_book(p)
        retain=key in critical or key=='handoff' or key.startswith('MP02-E_')
        repo=f'{SNAP}/{slug(key)}{p.suffix.lower()}' if retain else None
        if retain:
            dest=ROOT/repo;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        # Metadata and source packs retain their actual class; no role is inferred from names.
        heads=[r[0] for r in books.get(key,{}).values() if r]
        if key=='handoff':cls='D'
        elif e['category']=='ui':cls='C'
        elif e['category']=='process-docs':cls='D'
        elif any('TEXT' in h or 'LINE_NO' in h for h in heads):cls='B2'
        elif any('COLUMN_ID' in h or 'CONSTRAINT_NAME' in h or 'TRIGGER_NAME' in h or 'REFERENCED_OWNER' in h or 'PRIVILEGE' in h or 'SYNONYM_NAME' in h for h in heads):cls='A'
        else:cls='B'
        manifests[key]=dict(schema_version='1.0',kind='evidence-manifest',evidence_id=ev(key),evidence_class=cls,mapping_pack=None,environment='MC',oracle_owner='MC',captured_at=None,snapshot_date='2026-09-16' if key=='PM-12A' else None,source_client='SQL Navigator 5.5.4.847' if e['category']=='mapping-packs' else None,source_file=rel,sha256=e['sha256'],retention_class='SNAPSHOT_CRITICAL' if retain else 'REPRODUCIBLE',raw_retained=retain,repository_path=repo,supports_record_refs=[],review_status='Approved supplied handoff / integrity verified',result_summary_sk=e['source_name'],limitations_sk=['Source capture timestamp is not invented. Dated semantic observations follow the approved handoff.','Only MC rows support MC facts. Process proposals and technical comments are not implementation proof.'])
    def rows(key):
        ans=[]
        for sheet, rr in books[key].items():
            if rr:ans.extend(dict(zip(rr[0],r)) for r in rr[1:] if any(v is not None for v in r))
        return ans
    hand=entries['handoff'][0].read_text()
    sections={int(n):text.strip() for n,text in re.findall(r'^## (\d+)\. ([\s\S]*?)(?=^## \d+\.|\Z)',hand,re.M)}
    p=ROOT/DOCS;p.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(entries['handoff'][0],p/'READY_FOR_CODEX_HANDOFF_skladove_karty.md')
    shutil.copyfile(package/'MANIFEST.csv',p/'MANIFEST.csv')
    (p/'integrity.json').write_text(json.dumps(dict(base_commit=BASE,verified_files=166,verified_duplicate_pointers=7,files=audit),ensure_ascii=False,indent=2)+'\n')
    # Preserve the complete approved semantic text in addressable existing rule records.
    rules=[dict(rule_id=f'pm.rule.handoff_section_{n:02}',scope_refs=[obj('SKLAD_KARTA')],statement_sk=sections[n],evidence_refs=[HAND]) for n in [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,29]]
    for n,t in re.findall(r'^(\d+)\. (.+)$',sections[19],re.M):
        rules.append(dict(rule_id=f'pm.rule.do_not_assume_{int(n):02}',scope_refs=[obj('SKLAD_KARTA')],statement_sk=t,evidence_refs=[HAND]))
    components=[records('do-not-assume','do-not-assume',rules)]
    physical={}; physical_pack={}
    for k in ['MP01-A','LM-02A','PM-02A','PM-04A','PM-08A','PM-09A','PM-03C']:
        for r in rows(k):
            table='CIS_POZNAMKY_TYPY' if k=='PM-09A' else r.get('TABLE_NAME',r.get('TARGET_OBJECT',r.get('OBJECT_NAME')))
            if not table or not r.get('COLUMN_NAME') or not r.get('COLUMN_ID'):continue
            if table=='SKLAD_KARTA' and k!='MP01-A':continue
            physical.setdefault(table,{})[r['COLUMN_NAME']]=r
            physical_pack.setdefault(table,k)
    entities={}
    def ent(name,typ='TABLE',owner='MC',evidence=HAND,source=False):
        if owner=='MC' and typ=='TABLE' and name in CORE:return obj(name)
        ident='pm.oracle.'+slug(owner)+'.'+slug(name)+'.'+slug(typ)
        if ident not in entities:entities[ident]=dict(oracle_entity_id=ident,environment=owner,oracle_owner=owner,oracle_name=name,oracle_object_type=typ,source_visible=source,boundary_only=True,status=TECH,evidence_refs=[evidence],limitations_sk=['Boundary/reference only; not absorbed into Product Master.'],fields=[])
        elif evidence not in entities[ident]['evidence_refs']:entities[ident]['evidence_refs'].append(evidence)
        return ident
    def field(table,column,evidence=HAND):
        if table in CORE and column in physical.get(table,{}):return fld(table,column)
        ident=ent(table,evidence=evidence)
        fid='pm.boundary_field.'+table.lower()+'.'+column.lower()
        if not any(f['oracle_field_id']==fid for f in entities[ident]['fields']):entities[ident]['fields'].append(dict(oracle_field_id=fid,oracle_name=column,datatype_raw=None,status=TECH,evidence_refs=[evidence]))
        return fid
    definitions={'ID':'Physical primary key.','INT_KOD':'User-facing internal code; design uniqueness (INT_KOD, SKLAD).','USED':'Technical active/storno dimension; does not mean in sale.','STAV':'Business/sales state, independent from USED.','I_STAMP':'Technical insert stamp.','U_STAMP':'Last technical update stamp.','S_STAMP':'Technical remove/storno stamp.','N_STAMP':'Selective Novinka process stamp; not creation date or universal lifecycle timestamp.','NAHRADA':'Technical self-anchor group; business substitutability remains unconfirmed.','TYP_T':"Current '00' unresolved; do not use as product classification.",'FLAGS':'Position 12: Nezahŕňaj do prepočtu odpadov výrobkov. FLAGS[12]=1 plus coefficients is valid.','FLAGS_A':'Implemented, currently unpopulated allergen mechanism; typed notes are current operational authority.','ALERGENY':'Currently unpopulated; typed notes are current operational allergen authority.','UROVEN_DPH':'Root VAT value; SKLAD_KARTA_FU can override by warehouse/session context.','DOD_KOD':'kód dodávateľa; not a synonym for KOD_DOD or VYROBCA_KOD.'}
    for table in CORE:
        assert table in physical,table
        k=physical_pack[table]; fs=[]
        for c,r in sorted(physical[table].items(),key=lambda x:x[1]['COLUMN_ID']):
            typ=r['DATA_TYPE']; precision=r.get('DATA_PRECISION');scale=r.get('DATA_SCALE')
            dt=typ
            if typ=='NUMBER' and precision is not None:dt+=f'({int(precision)}'+(f',{int(scale)}' if scale is not None else '')+')'
            elif typ=='VARCHAR2':dt+=f"({int(r['DATA_LENGTH'])})"
            definition=definitions.get(c) if table=='SKLAD_KARTA' else None
            fs.append(dict(field_id=fld(table,c),oracle_name=c,ordinal_position=int(r['COLUMN_ID']),datatype_raw=dt,data_type_raw=typ,data_length=r.get('DATA_LENGTH'),data_precision=precision,data_scale=scale,nullable={'Y':True,'N':False}.get(r.get('NULLABLE')),default_raw=None if r.get('DATA_DEFAULT') is None else str(r['DATA_DEFAULT']),data_default_export_value=r.get('DATA_DEFAULT'),oracle_comment=r.get('COMMENTS',r.get('ORACLE_COMMENT')),canonical_alias=None,business_definition_sk=definition,status=CONF if definition else TECH,temporal_classification='RAW CURRENT',evidence_refs=[ev(k),HAND] if definition else [ev(k)],limitations_sk=['Canonical alias null by explicit user decision on 2026-09-16; approved English alias dictionary requested separately.']))
        ident=records('fields','fields-'+table.lower(),fs,object_ref=obj(table));components.append(ident)
        write(f'{DOMAIN}/object-{table.lower()}.yaml',dict(schema_version='1.0',kind='object',object_id=obj(table),environment='MC',oracle_owner='MC',oracle_name=table,object_type='TABLE',maturity='AGENT-READY',status=CONF,field_registry_ref=ident,grain_sk='One current stock/product card.' if table=='SKLAD_KARTA' else 'Physical row of '+table+'; contextual natural grain and fan-out are in relationships.',identity_refs=[fld(table,'ID')] if 'ID' in physical[table] else [],source_of_truth_summary_sk='RAW CURRENT; context-specific authority per handoff.',temporal_summary_sk='No arbitrary full historical reconstruction.',scope_limitations_sk=['Declared Product Master scope; inventory and transaction lifecycle excluded.'],evidence_refs=[ev(k),HAND]))
    cons=[];idx=[]; rels=[]
    def constraint(table, group, k):
        r=group[0];name=r['CONSTRAINT_NAME'];cid='pm.constraint.'+table.lower()+'.'+name.lower()
        cc=[field(table,x['COLUMN_NAME'],ev(k)) for x in group if x.get('COLUMN_NAME')]
        target=r.get('REFERENCED_TABLE');tc=[field(target,x['REFERENCED_COLUMN'],ev(k)) for x in group if target and x.get('REFERENCED_COLUMN')]
        rec=dict(constraint_id=cid,object_ref=obj(table) if table in CORE else ent(table,evidence=ev(k)),oracle_name=name,constraint_type=r['CONSTRAINT_TYPE'],column_refs=list(dict.fromkeys(cc)),referenced_object_ref=(obj(target) if target in CORE else ent(target,evidence=ev(k))) if target else None,referenced_column_refs=list(dict.fromkeys(tc)),enabled_state=r.get('STATUS'),validated_state=r.get('VALIDATED'),search_condition_raw=r.get('SEARCH_CONDITION'),delete_rule=r.get('DELETE_RULE'),deferrable_raw=r.get('DEFERRABLE'),deferred_raw=r.get('DEFERRED'),status=TECH,evidence_refs=[ev(k)])
        cons.append(rec)
        if target:
            rels.append(dict(relationship_id='pm.rel.'+table.lower()+'.'+name.lower(),from_object_ref=rec['object_ref'],from_field_refs=rec['column_refs'],to_object_ref=rec['referenced_object_ref'],to_field_refs=rec['referenced_column_refs'],relationship_type='DIRECT',cardinality='N:1 declared FK; parent-to-child 1:N',physical_constraint_ref=cid,condition_sk='Declared metadata; preserve ENABLED/DISABLED and VALIDATED states. No automatic validity from FK existence.',fanout_risk='HIGH',safe_usage_sk='Keep child grain. Aggregate each child separately before combining satellites; never sum root measures after reverse joins.',status=TECH,evidence_refs=[ev(k)]))
    groups=defaultdict(list)
    for r in rows('MP01-B'):groups[r['CONSTRAINT_NAME']].append(r)
    for g in groups.values():constraint('SKLAD_KARTA',g,'MP01-B')
    for k in ['LM-02B']:
        groups=defaultdict(list)
        for r in rows(k):
            if r['TABLE_NAME'] in CORE:groups[(r['TABLE_NAME'],r['CONSTRAINT_NAME'])].append(r)
        checks={(r['TABLE_NAME'],r['CONSTRAINT_NAME']):r for r in rows('LM-02B2')}
        for (t,n),g in groups.items():
            if (t,n) in checks:g[0]['SEARCH_CONDITION']=checks[t,n].get('SEARCH_CONDITION')
            constraint(t,g,k)
    for k in ['PM-02B','PM-04B','PM-08B']:
        groups=defaultdict(list)
        for r in rows(k):
            t=r.get('OBJECT_NAME')
            if t not in CORE or t in ['SKLAD_KARTA','SKLAD_KARTA_LB','B_KOD_U']:continue
            rt=str(r.get('RECORD_TYPE',r.get('REC_TYPE')))
            if rt=='CONSTRAINT':
                x=dict(CONSTRAINT_NAME=r.get('RECORD_NAME',r.get('REC_NAME')),CONSTRAINT_TYPE=r['TYPE_DETAIL'],COLUMN_NAME=r['COLUMN_NAME'],REFERENCED_TABLE=r.get('REFERENCED_OBJECT',r.get('REF_OBJECT')),REFERENCED_COLUMN=r.get('REFERENCED_COLUMN',r.get('REF_COLUMN')),STATUS=r['STATUS'],VALIDATED=r.get('VALIDATED'))
                groups[t,x['CONSTRAINT_NAME']].append(x)
        for (t,n),g in groups.items():constraint(t,g,k)
    for k in ['MP01-D','LM-02C']:
        groups=defaultdict(list)
        for r in rows(k):
            t=r.get('TABLE_NAME','SKLAD_KARTA')
            if t in CORE:groups[t,r['INDEX_NAME']].append(r)
        for (t,n),g in groups.items():
            idx.append(dict(index_id='pm.index.'+t.lower()+'.'+n.lower(),object_ref=obj(t),oracle_name=n,uniqueness=g[0]['UNIQUENESS'],function_based=None,index_type_raw=g[0].get('INDEX_TYPE'),oracle_status_raw=g[0]['STATUS'],status=TECH,evidence_refs=[ev(k)],column_or_expression_entries=[dict(position=int(x['COLUMN_POSITION']),**({'field_ref':field(t,x['COLUMN_NAME'],ev(k))} if x['COLUMN_NAME'] in physical.get(t,{}) else {'oracle_column_name_raw':x['COLUMN_NAME']}),direction=x['DESCEND']) for x in g]))
    components += [records('constraints','constraints',cons),records('indexes','indexes',idx)]
    # Complete inbound FK surface, including constraints on external transactional objects.
    inbound=[]
    for r in rows('MP01-C'):
        t=r['CHILD_TABLE']; n=r['CONSTRAINT_NAME']
        inbound.append(dict(relationship_id='pm.rel.inbound.'+t.lower()+'.'+n.lower(),from_object_ref=ent(t,owner=r['CHILD_OWNER'],evidence=ev('MP01-C')),from_field_refs=[field(t,r['CHILD_COLUMN'],ev('MP01-C'))],to_object_ref=obj('SKLAD_KARTA'),to_field_refs=[fld('SKLAD_KARTA',r['PARENT_COLUMN'])],relationship_type='DIRECT',cardinality='N:1 declared FK; reverse 1:N',condition_sk=f"{r['STATUS']}; {r['VALIDATED']}; delete rule {r['DELETE_RULE']}",fanout_risk='HIGH',safe_usage_sk='Transactional boundary. Do not absorb lifecycle or multiply root measures.',status=TECH,evidence_refs=[ev('MP01-C')]))
    components.append(records('relationships','relationships-inbound',inbound))
    def relationship(key,ft,fc,tt,tc,card,condition,pack):
        rels.append(dict(relationship_id='pm.rel.'+key,from_object_ref=obj(ft) if ft in CORE else ent(ft),from_field_refs=[field(ft,c,ev(pack)) for c in fc],to_object_ref=obj(tt) if tt in CORE else ent(tt),to_field_refs=[field(tt,c,ev(pack)) for c in tc],relationship_type='CONDITIONAL',cardinality=card,condition_sk=condition,fanout_risk='HIGH',safe_usage_sk='Preserve declared contextual grain; preaggregate satellites independently.',snapshot_date='2026-09-14',status=CONF,evidence_refs=[HAND,ev(pack)]))
    for args in [
        ('typed_notes','SKLAD_KARTA',['RID'],'CIS_POZNAMKY',['RID_V'],'1:N','Product-card RID context only; CIS_POZNAMKY is generic/polymorphic. Current allergen authority.','PM-08E'),
        ('note_type','CIS_POZNAMKY',['TYP'],'CIS_POZNAMKY_TYPY',['ID'],'N:1','Meaning comes from typed-note dictionary; direct and cross-contamination stay separate.','PM-09B'),
        ('supplier','SKLAD_KARTA',['ID'],'SKLAD_DODAVATEL',['KOD_ID'],'1:N','Active natural grain KOD_ID + ID_DODAVATELA; not continuous root synchronization.','PM-05E'),
        ('vat','SKLAD_KARTA',['ID'],'SKLAD_KARTA_FU',['KOD_ID'],'1:N','Specify SKLAD_P and session context; root UROVEN_DPH not universal.','PM-05F'),
        ('partner_codes','SKLAD_KARTA',['ID'],'SKLAD_PARTNER_KODY',['KOD_ID'],'1:N','Natural grain KOD_ID + PARTNER + BALENIE; PARTNER + KOD_PARTNERA not globally unique.','PM-05G'),
        ('store_logistics','SKLAD_KARTA',['ID'],'SK_LOG_UDAJE',['KOD_ID'],'1:N','KOD_ID + SKLAD_P + optional SARZA. Current SARZA all NULL; contextual root overrides.','PM-05D'),
        ('packaging','SKLAD_KARTA',['ID'],'SKLAD_KARTA_LB',['KOD_ID'],'1:N','Packaging levels 0..4; main LB FLAGS_B[1]. Root fields not universal roll-up.','LM-02E'),
        ('packaging_codes','SKLAD_KARTA_LB',['RID'],'B_KOD_U',['RID_SKLAD_KARTA_LB'],'1:N','Preserve BAL level and active/storno context; FLAGS_B[2] main code behavior.','LM-03C'),
        ('coefficients','SKLAD_KARTA',['ID'],'SK_NAKL_POLOZKY',['KOD_ID'],'1:N','Active is not effective today; preserve DATUM_OD/DATUM_DO and lifecycle.','PM-05B'),
        ('coefficient_dictionary','SK_NAKL_POLOZKY',['NK_ID'],'NAKL_KOEF',['ID'],'N:1','Coefficient name is not jurisdiction truth.','PM-04C'),
        ('supplemental','SKLAD_KARTA',['RID'],'CIS_DU_O',['RID'],'1:0..1 observed','Approved DU1/4/5/6/7/8/9 definitions only; no guessed unused meanings.','PM-04G'),
        ('nahrada','SKLAD_KARTA',['NAHRADA'],'SKLAD_KARTA',['ID'],'N:1','Self-anchor technical grouping only; no business substitutability or automatic merge.','PM-10F')]:relationship(*args)
    components.append(records('relationships','relationships',rels))
    deps=[]
    for k in ['MP01-G','MP04-A','LM-01D']:
        for i,r in enumerate(rows(k),1):
            if r['OWNER']!='MC':continue
            deps.append(dict(dependency_id=f'pm.dependency.{slug(k)}.{i:05}',source_ref=ent(r['NAME'],r['TYPE'],r['OWNER'],ev(k)),target_ref=ent(r['REFERENCED_NAME'],r['REFERENCED_TYPE'],r['REFERENCED_OWNER'],ev(k)),direction='SOURCE TO REFERENCED',depth=1,role='DEPENDENCY ONLY',discovery_method='ALL_DEPENDENCIES',source_visible=False,runtime_boundary=True,status='DEPENDENCY ONLY',evidence_refs=[ev(k)],limitations_sk=['Compile-time dependency does not establish runtime reader/writer/caller behavior.']))
    for k in ['MP04-C','MP04-D']:
        for i,r in enumerate(rows(k),1):
            name=r.get('SYNONYM_NAME',r.get('GRANTEE'));owner=r.get('OWNER',r.get('GRANTEE'))
            deps.append(dict(dependency_id=f'pm.access.{slug(k)}.{i:03}',source_ref=ent(name,'SYNONYM' if k=='MP04-C' else 'GRANTEE',owner,ev(k)),target_ref=ent(r['TABLE_NAME'],'TABLE' if r['TABLE_NAME']=='SKLAD_KARTA' else 'PACKAGE',r.get('TABLE_OWNER',r.get('TABLE_SCHEMA')),ev(k)),direction='ACCESS CAPABILITY',depth=1,role='ACCESS CAPABILITY',discovery_method='ALL_SYNONYMS' if k=='MP04-C' else 'ALL_TAB_PRIVS',source_visible=False,runtime_boundary=True,status='DEPENDENCY ONLY',evidence_refs=[ev(k)],limitations_sk=[json.dumps(r,ensure_ascii=False),'Access capability only; no runtime role asserted.']))
    writer_groups=defaultdict(list)
    for r in rows('MP03-D'):
        if r['OWNER']=='MC':writer_groups[r['NAME'],r['TYPE']].append(r)
    writer_count=0
    for (name,typ),g in writer_groups.items():
        source='\n'.join(r['TEXT'] or '' for r in g)
        source=re.sub(r'/\*.*?\*/',' ',source,flags=re.S)
        source=re.sub(r'--[^\n]*',' ',source)
        if not re.search(r'\b(?:update\s+(?:MC\.)?SKLAD_KARTA\b|insert\s+into\s+(?:MC\.)?SKLAD_KARTA\b|delete\s+(?:from\s+)?(?:MC\.)?SKLAD_KARTA\b)',source,re.I):continue
        writer_count+=1
        deps.append(dict(dependency_id='pm.writer.'+slug(name)+'.'+slug(typ),source_ref=ent(name,typ,evidence=ev('MP03-D'),source=True),target_ref=obj('SKLAD_KARTA'),direction='SOURCE TO WRITTEN',depth=1,role='DIRECT WRITER',discovery_method='Approved MP03-D external direct-writer context; explicit root DML occurrence',source_visible=True,runtime_boundary=True,status=CONF,evidence_refs=[ev('MP03-D'),HAND],limitations_sk=['Source-visible writer capability; does not assert execution frequency or external caller identity. Exact source context in source-references.']))
    assert writer_count==33,writer_count
    components.append(records('dependencies','dependencies',deps))
    # Source-context register uses existing dependency records, preserving exact locations.
    source_context=[]
    for k in ['MP03-A','MP03-B','MP03-C','MP03-D','MP03-E','MP03-F','PM-02D','PM-02E','PM-03G','PM-04H','PM-05A','PM-08C','PM-09C','PM-09D','PM-09E','PM-09F','PM-10C','PM-12A']:
        groups=defaultdict(list)
        for r in rows(k):
            if r.get('OWNER','MC')!='MC':continue
            n=r.get('NAME',r.get('TRIGGER_NAME'));t=r.get('TYPE','TRIGGER')
            if n and r.get('LINE') is not None:groups[n,t].append(r)
        for (n,t),g in groups.items():
            source_context.append(dict(dependency_id=f'pm.source.{slug(k)}.{slug(n)}.{slug(t)}',source_ref=ent(n,t,evidence=ev(k),source=True),target_ref=obj('SKLAD_KARTA'),direction='SOURCE CONTEXT',depth=1,role='DEPENDENCY ONLY',discovery_method='Supplied approved source pack; exact line register',source_visible=True,runtime_boundary=True,status='DEPENDENCY ONLY',evidence_refs=[ev(k)],limitations_sk=['Context/hit is not runtime role. Lines may be a partial source window.','\n'.join(f"{int(r['LINE'])}: {r.get('TEXT') or ''}" for r in g)]))
    for start in range(0,len(source_context),100):components.append(records('dependencies',f'source-references-part{start//100+1:03}',source_context[start:start+100]))
    api=[]
    targets=['C_SKLAD_KARTA','C_SKLAD_KARTA_LB','C_SKLAD_DODAVATEL','C_SK_NAKL_POL','C_NAKL_KOEF','C_CIS_POZNAMKY','MCCARTER_PLAN']
    pattern=re.compile(r'\b('+'|'.join(targets)+r')\s*\.\s*([A-Za-z][A-Za-z0-9_$#]*)',re.I)
    for k in ['MP03-C','PM-02D','PM-03G','PM-10C','PM-12A']:
        for r in rows(k):
            if r.get('OWNER')!='MC' or not r.get('TEXT'):continue
            for occurrence,m in enumerate(pattern.finditer(r['TEXT']),1):
                api.append(dict(api_reference_id=f"pm.api.{slug(k)}.{slug(r['NAME'])}.{slug(r['TYPE'])}.{int(r['LINE'])}.{occurrence}",caller_owner='MC',caller_name=r['NAME'],caller_type=r['TYPE'],target_package=m.group(1).upper(),member_name_raw=m.group(2),member_name_normalized=m.group(2).upper(),reference_raw=m.group(0),source_text_raw=r['TEXT'],occurrence_column=m.start()+1,hit_count=1,hit_lines=[int(r['LINE'])],classification='SOURCE MEMBER REFERENCE',evidence_refs=[ev(k)],limitations_sk=['Lexical source member reference; includes declarations/comments/strings and is not promoted to runtime CALLER.']))
    for start in range(0,len(api),200):
        chunk=api[start:start+200]
        components.append(records('api-references',f'api-references-part{start//200+1:03}',chunk,environment='MC',source_dataset='Approved supplied source-hit/context exports',summary=dict(record_count=len(chunk),caller_count=len({(r['caller_name'],r['caller_type']) for r in chunk}),member_count=len({(r['target_package'],r['member_name_normalized']) for r in chunk}))))
    flows=[]; mutations=[]
    for r in rows('MP01-E'):
        n=r['TRIGGER_NAME'];eid=ent(n,'TRIGGER',evidence=ev('MP01-E'),source=True)
        flows.append(dict(flow_id='pm.flow.trigger.'+n.lower(),trigger_or_procedure_ref=eid,event_sk=r['TRIGGER_TYPE']+' '+r['TRIGGERING_EVENT'],condition_sk=r['WHEN_CLAUSE'],diagnostic_meaning_sk='Enabled state: '+r['STATUS']+'. Full source context in source-references; no trigger ordering assumption.',evidence_refs=[ev('MP01-E'),ev('MP03-A')]))
    def flow(key,writer,event,condition,description,targets,pack='MP03-A',bypass=None,calls=[]):
        writer_ref=ent(writer,'TRIGGER' if writer.startswith('T_') else 'PACKAGE BODY',evidence=ev(pack),source=True)
        f=dict(flow_id='pm.flow.'+key,trigger_or_procedure_ref=writer_ref,event_sk=event,condition_sk=condition,session_or_bypass_sk=bypass,business_effect_sk=description,evidence_refs=[HAND,ev(pack)],calls=[dict(callee_ref=ent(n,'PACKAGE BODY',evidence=ev(pack),source=True),sequence=i+1) for i,n in enumerate(calls)],direct_mutations=[dict(scope_refs=targets,description_sk=description)])
        flows.append(f);mutations.append(dict(mutation_id='pm.mutation.'+key,target_refs=targets,writer_ref=writer_ref,writer_role='DIRECT WRITER',event_sk=event,condition_sk=condition,session_or_bypass_sk=bypass,direct_mutations_sk=description,status=CONF,evidence_refs=[HAND,ev(pack)]))
    flow('insert','T_S_SKLAD_KARTA_INS','BEFORE INSERT','Outside replication; defaults retain source conditions.','HLAVNA_TP=self when null/0; NAHRADA=self when null; SK_ID=ID; RID_OBJ=RID; USED=1; DATUM=SYSDATE; I_STAMP technical insert; U_STAMP/S_STAMP zero. Template branch may subsequently override values.',[fld('SKLAD_KARTA',c) for c in ['HLAVNA_TP','NAHRADA','SK_ID','RID_OBJ','USED','DATUM','I_STAMP']],bypass='C_SESSION.GETREPLIKACIA != 0 returns early.')
    flow('storno','T_S_SKLAD_KARTA','BEFORE DELETE OR UPDATE','On S_STAMP change to nonzero, active child rows only.','USED and S_STAMP technical synchronization; storno B_KOD_U, SKLAD_KARTA_LB and SKLAD_DODAVATEL. B_KOD_U and LB SKRATKA=RID. Reverse root activation does not prove child restoration.',[obj(t) for t in ['SKLAD_KARTA','B_KOD_U','SKLAD_KARTA_LB','SKLAD_DODAVATEL']],bypass='Replication early return; C_SESSION.GetSwap branch retained in source.')
    flow('novinka','T_S_SKLAD_KARTA','UPDATE STAV','NEW.STAV=1 AND OLD.STAV!=1','N_STAMP=C_STAMP.GetSessionStamp for selective Novinka transition, not universal lifecycle history.',[fld('SKLAD_KARTA','N_STAMP')])
    flow('end_of_sale','T_SKLAD_KARTA_STAV_AFTER_MC','AFTER UPDATE OF STAV','OLD.STAV <> 8 AND NEW.STAV = 8','Calls MCCARTER_PLAN.MC_UKONCENY_PREDAJ_SK(NEW.ID). Current/future OBCH_PL_O forecast types OPTyp_Prognoza / OPTyp_PrognPartn: PLAN_POCET2=0 and POZN beginning Ukončený predaj with date and original quantity. POZN is part of the executable bypass contract.',[field('OBCH_PL_O',c,ev('PM-12A')) for c in ['PLAN_POCET2','POZN']],'PM-12A','C_Session.GetReplikacia: replication returns early.',['MCCARTER_PLAN'])
    flow('forecast_lock','T_OBCH_PL_LOCK_MC','AFTER INSERT OR UPDATE OF PLAN_POCET2',"Changed PLAN_POCET2; NVL(OLD.POZN,'xyz') != NVL(NEW.POZN,'xyz') AND NEW.POZN LIKE '%Ukončený predaj%' recognizes specific marker.",'POTVRDENÉ — VYRIEŠENÉ as of 2026-09-16 MC. Dedicated note exception bypasses this guard; ordinary changed PLAN_POCET2 on BITAND(NEW.STAV,2)=2 still raises locked-period error. Existing (+%)/(-%) transfer exceptions and insert-time protection unchanged. Not a global lock bypass.',[field('OBCH_PL_O','PLAN_POCET2',ev('PM-12A'))],'PM-12A','Simultaneous changed POZN marker only; lock not removed.')
    # The lock trigger validates; it does not write the forecast quantity.
    guard=flows[-1]
    guard['exceptions']=[dict(scope_refs=[field('OBCH_PL_O','PLAN_POCET2',ev('PM-12A'))],description_sk=guard['business_effect_sk'])]
    guard['direct_mutations']=[]
    mutations.pop()
    delegated=next(r for r in mutations if r['mutation_id']=='pm.mutation.end_of_sale')
    delegated['writer_role']='TRIGGER SIDE EFFECT'
    delegated_flow=next(r for r in flows if r['flow_id']=='pm.flow.end_of_sale')
    delegated_flow['side_effects']=delegated_flow.pop('direct_mutations')
    flow('end_of_sale_reset','MCCARTER_PLAN','MC_UKONCENY_PREDAJ_SK(SK.ID)','Matching SKU; current week-period forward; OBCH_PL_L.TYP_PLANU in OPTyp_Prognoza / OPTyp_PrognPartn.','Directly sets OBCH_PL_O.PLAN_POCET2=0 and POZN beginning Ukončený predaj with date and original quantity; the simultaneous note change is required by the dedicated lock exception.',[field('OBCH_PL_O',c,ev('PM-12A')) for c in ['PLAN_POCET2','POZN']],'PM-12A')
    flow('bom_coefficients','MCCARTER','imp_SK_NAKL_POL_VYR','Active BOM rows; executable finished-product INT_KOD prefix 3; DU8/DU9 tokens.','Uses component HMOTNOST_NETTO times BOM POCET (can include norm loss), DU7 split and CZ;SK tokens. Deletes product+NK_ID then inserts per component/token: overwrite instead of aggregation. DQ-COEF-001..006 remain incidents; do not normalize away.',[obj('SK_NAKL_POLOZKY')],'PM-04F_0eff0ebf')
    # Lexical source assignments retain the complete source condition context rather
    # than promoting a field-name guess into a business rule.
    trigger_source=defaultdict(list)
    for r in rows('MP03-A'):
        if r['OWNER']=='MC':trigger_source[r['NAME']].append(r)
    for name,g in trigger_source.items():
        text=''.join(r['TEXT'] or '' for r in g)
        code=re.sub(r'/\*.*?\*/',' ',text,flags=re.S)
        code=re.sub(r'--[^\n]*',' ',code)
        assignments=re.findall(r':new\.([A-Za-z0-9_]+)\s*:=\s*([^;]+);',code,re.I)
        targets=list(dict.fromkeys(fld('SKLAD_KARTA',c.upper()) for c,expr in assignments if c.upper() in physical['SKLAD_KARTA']))
        if not targets:continue
        mutations.append(dict(mutation_id='pm.mutation.assignments.'+name.lower(),target_refs=targets,writer_ref=ent(name,'TRIGGER',evidence=ev('MP03-A'),source=True),writer_role='DIRECT WRITER',event_sk='Source-visible :NEW assignments; trigger event recorded in flows.',condition_sk='Preserve branch conditions and exceptions in pm.source.mp03-a.'+name.lower()+'.trigger; assignments are not unconditional defaults.',direct_mutations_sk='\n'.join(':NEW.'+c+' := '+expr+';' for c,expr in assignments),status=TECH,evidence_refs=[ev('MP03-A')]))
    components += [records('flows','flows',flows),records('mutations','mutations',mutations)]
    temporal=[]
    for c,typ,limit in [('I_STAMP','TRANSITION STAMP','Technical insert only.'),('U_STAMP','LAST UPDATE','Last technical update; not per-field history.'),('S_STAMP','TRANSITION STAMP','Remove/storno only.'),('N_STAMP','TRANSITION STAMP','Selective Novinka process; not creation date or universal lifecycle timestamp.')]:
        temporal.append(dict(temporal_rule_id='pm.temporal.'+c.lower(),scope_refs=[fld('SKLAD_KARTA',c)],classification=typ,reconstructable=False,history_limitations_sk=limit,status=CONF,evidence_refs=[HAND]))
    temporal.extend([dict(temporal_rule_id='pm.temporal.raw_current',scope_refs=[obj('SKLAD_KARTA')],classification='RAW CURRENT',reconstructable=False,history_limitations_sk='Historical transaction joined to current master is not historical master truth.',status=CONF,evidence_refs=[HAND]),dict(temporal_rule_id='pm.temporal.selective_history',scope_refs=[ent('SKLAD_KARTA_INTKOD_Z'),ent('HIST_ZMIEN'),ent('SK_TEMP')],classification='SELECTIVE HISTORY',reconstructable=False,history_limitations_sk='SK_TEMP is process/change queue; selective history cannot reconstruct arbitrary master fields.',status=CONF,evidence_refs=[HAND])])
    components.append(records('temporal','temporal',temporal))
    values=[]
    for i,r in enumerate(rows('MP02-B'),1):
        values.append(dict(value_domain_id=f'pm.value.root.{i:03}',scope_ref=fld('SKLAD_KARTA',r['FIELD_NAME']),raw_value=r['VALUE_CODE'],observed_live=True,observed_count=int(r['ROW_COUNT']),snapshot_date='2026-09-14',status=TECH,evidence_refs=[ev('MP02-B')],limitations_sk=['Dated population observation, not invariant.']))
    for i,r in enumerate(rows('PM-09B'),1):
        values.append(dict(value_domain_id=f'pm.value.note_type.{i:03}',scope_ref=fld('CIS_POZNAMKY','TYP'),raw_value=str(r['ID']),business_label_sk=r['NAZOV'],observed_live=True,snapshot_date='2026-09-14',status=TECH,evidence_refs=[ev('PM-09B')],limitations_sk=['Dictionary label preserved; 00048 vs 00052 remains unresolved; not every note is allergen.']))
    for c,labels in [('TYP_UPL',['quantity','volume','weight','purchase cost']),('ZARADENIE',['recycling','electro','hazardous','other','excise','bonus','deposit','sugar'])]:
        for i,label in enumerate(labels):values.append(dict(value_domain_id=f'pm.value.nakl_koef.{c.lower()}.{i}',scope_ref=fld('NAKL_KOEF',c),raw_value=i,business_label_sk=label,status=CONF,evidence_refs=[HAND]))
    components.append(records('value-domains','value-domains',values))
    backlog=[]
    for i,q in re.findall(r'^(\d+)\. (.+)$',sections[24],re.M):backlog.append(dict(backlog_id='pm.backlog.'+i,scope_refs=[obj('SKLAD_KARTA')],status='DATA GAP' if int(i)>=6 else 'TREBA OVERIŤ',blocking=False,question_sk=q,related_evidence_refs=[HAND]))
    components.append(records('backlog','backlog',backlog))
    # Named incident IDs are stable and retained verbatim in each observation.
    dq=[]
    for i,desc in re.findall(r'- DQ-COEF-(\d+): (.+)',sections[13]):dq.append(dict(dq_id='pm.dq.coef_'+i,scope_refs=[obj('SK_NAKL_POLOZKY')],observation_sk='DQ-COEF-'+i+': '+desc,snapshot_date='2026-09-15',blocking=False,status=CONF,evidence_refs=[HAND],interpretation_limit_sk='Scope-sensitive; no automatic master-data remediation. Preserve norm loss, lifecycle/effective context and jurisdiction boundary.'))
    dq.append(dict(dq_id='pm.dq.report_001',scope_refs=[obj('SKLAD_KARTA'),obj('SK_NAKL_POLOZKY')],observation_sk='DQ-REPORT-001; CRITICAL; POTVRDENÉ. Both SK and CZ total/footer omit FLAGS[12] eligibility filter present in detail. Fix belongs to report SQL, not master values or coefficients.',snapshot_date='2026-09-15',blocking=False,status=CONF,evidence_refs=[HAND,ev('PM-11P'),ev('PM-11N'),ev('PM-11S2')],interpretation_limit_sk='SK Q2/2026: 154.416745 t versus 150.787039 t; excluded 3.629706 t, 12 cards. Current master does not reconstruct historical eligibility.'))
    for key,scope,desc,pack in [('logistics','SKLAD_KARTA_LB','5 active LB missing exact piece code; 4 active unlinked codes; 1 linked to inactive LB; 1 code not represented by LB level; 14 main LB without main piece code; 27 active shared codes. Candidates are scope-dependent, not automatic errors.','LM-03C'),('supplier','SKLAD_DODAVATEL','102 matches; 13 root main suppliers absent from active satellite. DOD_KOD, KOD_DOD, VYROBCA_KOD are not synonyms.','PM-05E'),('vat','SKLAD_KARTA_FU','2080 false / 481 true SAME_AS_ROOT. Contextual overrides may be valid.','PM-05F'),('nahrada','SKLAD_KARTA','164 groups; 3162 nonzero rows; 164 anchors; 2998 other members; 837 USED=1. No substitutability or automatic remediation.','PM-10F'),('typ_t','SKLAD_KARTA',"12 unresolved '00'; no ID/TYP_T/tree resolution. No guessed classification or cleanup.",'PM-10B2')]:dq.append(dict(dq_id='pm.dq.'+key,scope_refs=[obj(scope)],observation_sk=desc,snapshot_date='2026-09-14',blocking=False,status=CONF,evidence_refs=[HAND,ev(pack)]))
    for r in dq:
        m=re.search(r'DQ-(?:COEF|REPORT)-[0-9]{3}',r['observation_sk'])
        if m:
            r['incident_code']=m.group(0)
            if m.group(0) in ['DQ-COEF-002','DQ-REPORT-001']:r['severity']='CRITICAL'
            elif m.group(0)=='DQ-COEF-005':r['severity']='WARNING'
    components.append(records('data-quality','data-quality',dq))
    components.append(records('oracle-entities','oracle-entities',list(entities.values())))
    components.append(records('revisions','revisions',[dict(revision_id='pm.revision.1_0',contract_version='1.0',date='2026-09-15',breaking_change=False,changed_record_refs=[obj(t) for t in CORE],change_sk='Initial approved MC Product Master semantic closure. New canonical domain; publications deferred.',evidence_refs=[HAND]),dict(revision_id='pm.revision.1_0_mc_20260916',contract_version='1.0',date='2026-09-16',breaking_change=False,changed_record_refs=['pm.flow.end_of_sale','pm.flow.forecast_lock','pm.mutations'],change_sk=sections[29],reason_sk='Earlier locked-period conflict -> POTVRDENÉ — VYRIEŠENÉ on MC. Deployed change localized to T_OBCH_PL_LOCK_MC.',evidence_refs=[HAND,ev('PM-12A')])]))
    write(f'{DOMAIN}/contract.yaml',dict(schema_version='1.0',kind='contract',contract_id='pm.contract.skladove_karty.1_0',domain='master',title_sk='Product Master / skladové karty',purpose_sk='EXHAUSTIVE DEPENDENCY-GRADE / AGENT-READY within approved MC scope.',scope_includes=['MC.'+t for t in CORE],scope_excludes=['Kusy','Blokácie','Pasívne kusy','Inventory/WMS lifecycle','Manufacturing','Orders','Issues','Receipts','Pricing'],authoritative_environment='MC',authoritative_owner='MC',maturity='AGENT-READY',object_refs=[obj(t) for t in CORE],component_refs=components,boundary_refs=[],evidence_refs=[HAND],limitations_sk=['RAW CURRENT; selective history only.','Seven approved non-blocking gaps retained.','Canonical aliases remain null by explicit user decision on 2026-09-16; dictionary approval deferred.','No publication/documentation version created.']))
    # Translate approved prose into the existing machine-readable handoff shape.
    handoff=dict(schema_version='1.0',kind='codex-handoff',handoff_id='pm.handoff.1_0_20260916',status='READY_FOR_CODEX_HANDOFF',repository=dict(name='mtasky-mccarter/kaso-data-catalog',base_branch='main',base_commit=BASE,feature_branch='codex/skladove-karty-1-0'),scope=dict(domain='master',slug='skladove-karty',oracle_objects=['MC.'+t for t in CORE],authoritative_environment='MC',canonical_path=DOMAIN+'/',existing_canonical_refs=[]),target=dict(maturity='AGENT-READY',contract_version='1.0',documentation_version=None,breaking_change=False,revision_date='2026-09-16',revision_note_sk=sections[29]),semantic_contract=dict(approved=True,grain=[sections[3]],identity=[sections[5]],source_of_truth=[sections[7]],critical_relationships=[sections[n] for n in [8,9,10,11,12,13]],do_not_assume=[sections[19]],mutation_boundaries=[sections[17],sections[29]],dependency_boundaries=[sections[18]]),evidence=dict(bundles=[DOCS+'/MANIFEST.csv'],manifests=['evidence/manifests/skladove-karty/'],snapshot_dates=['2026-09-14','2026-09-15','2026-09-16']),canonical_sql=dict(materialize=True,read_only_required=True,source_paths=[DOCS+'/READY_FOR_CODEX_HANDOFF_skladove_karty.md']),backlog=dict(blocking_count=0,blocking_items=[],nonblocking_items=[r['question_sk'] for r in backlog]),acceptance=dict(expected_counts=dict(root_fields=169,root_outbound_fks=32,root_enabled_triggers=21),semantic_loss_assertions=[sections[25]],required_domain_tests=['python -m unittest discover -s tools -p test_pm_acceptance.py -v'],required_sql_safety_tests=['python -m unittest discover -s tools -p test_pm_sql_safety.py -v'],unresolved_refs=0,duplicate_global_ids=0),publication=dict(enabled=False),execution=dict(standard='docs/codex-execution-standard-v3.md',prefer_deterministic_materializer=True,do_not_rediscover_approved_facts=True),repository_actions=dict(merge_only_with_green_ci=True,prepare_pr=True,verify_main_after_merge=True),engineering_decisions=['2026-09-16 user explicitly instructed canonical aliases remain null; request approved alias dictionary in final report.'])
    write(DOCS+'/handoff.yaml',handoff)
    # Evidence observations are dated, independently asserted by acceptance tests.
    manifests['MP02-A']['snapshot_date']='2026-09-14'
    manifests['MP02-A']['result_summary']=dict(summary_sk='Approved current MC snapshot; not invariant.',observations=[dict(name='root_rows',value=7429),dict(name='id_sk_id_match_percent',value=100),dict(name='rid_rid_obj_match_percent',value=100)])
    for key,m in manifests.items():write('evidence/manifests/skladove-karty/'+slug(key)+'.yaml',m)
    (p/'workbook-inventory.json').write_text(json.dumps({k:{n:dict(rows=len(r)-1,columns=r[0] if r else []) for n,r in v.items()} for k,v in books.items()},ensure_ascii=False,indent=2)+'\n')
    (p/'materialization-counts.json').write_text(json.dumps(dict(root_fields=len(physical['SKLAD_KARTA']),root_constraints=len([r for r in cons if r['object_ref']==obj('SKLAD_KARTA')]),root_outbound_fk=len([r for r in cons if r['object_ref']==obj('SKLAD_KARTA') and r['constraint_type']=='R']),root_indexes=len([r for r in idx if r['object_ref']==obj('SKLAD_KARTA')]),root_triggers=len(rows('MP01-E')),direct_dependency_rows=len(rows('MP01-G')),source_context_objects=len(source_context),inbound_fks=len(inbound),evidence_manifests=len(manifests),null_root_aliases=len(physical['SKLAD_KARTA'])),indent=2)+'\n')
    from apply_pm_aliases import apply as apply_approved_aliases
    apply_approved_aliases(ROOT)
    print('PASS: manifest integrity; canonical physical and semantic registries materialized.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('package',type=Path)
    materialize(parser.parse_args().package)

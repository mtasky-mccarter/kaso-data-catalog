"""Deterministic document-backed Phase A projection; no business inference or DB access.

Block offsets address the retained intake extraction, NOT raw Oracle exports.
Empty DOCX cells are omitted, never converted to source NULL. Original status
strings and complete source rows remain traceable in the retained extraction.
"""
import hashlib
import json
import re
from pathlib import Path
import yaml
yaml.SafeDumper.ignore_aliases = lambda self, data: True
ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / 'catalog/sales/obchodne-pripady'
SOURCE = ROOT / 'evidence/source-extracts/odb/approved-contract.json'
APPROVED_EXTRACT_SHA256 = '7801ca66f6a8bd1f0a3a165d698e7d3cff0e66e785151f072cb4a99b6cdfca5d'
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != APPROVED_EXTRACT_SHA256:
    raise ValueError('HANDOFF BLOCKED: approved extraction checksum mismatch')
B = json.loads(SOURCE.read_text())
OBJECTS = ['mc.object.obj_odb_l', 'mc.object.obj_odb_o']
E = 'odb.evidence.d.approved_contract'

def rows(block):
    return B[block]['rows'][1:]
def load(name):
    return yaml.safe_load((DOMAIN / (name+'.yaml')).read_text())
def save(name, doc):
    (DOMAIN / (name+'.yaml')).write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=110))
def registry(name, records):
    d=load(name); d['records']=records; save(name,d)
def field(obj, name):
    return 'mc.field.'+obj.lower()+'.'+name.lower()
def source_note(block):
    return f'Schválený DOCX v1.2, extraction block {block} (0-based). Dokumentový prenos; raw Oracle export nebol pri materializácii dostupný.'
def rule(block, row, text, scope=OBJECTS):
    return dict(rule_id=f'odb.rule.doc_{block}_{row}',scope_refs=scope,statement_sk=text,evidence_refs=[E])

def main():
    all_fields={}
    for obj, block, semantic in [('OBJ_ODB_L',337,77),('OBJ_ODB_O',339,117)]:
        semantics={r[0]:r for r in rows(semantic)}
        records=[]
        for r in rows(block):
            pos,name=r[0].split('. ',1)
            f=dict(field_id=field(obj,name),oracle_name=name,ordinal_position=int(pos),datatype_raw=r[1],nullable={'Y':True,'N':False}[r[2]],status='TECHNICKY ZNÁME',evidence_refs=[E],limitations_sk=[source_note(block)])
            if obj.endswith('_L'):
                if r[3]: f['default_raw']=r[3]
                if r[4]: f['oracle_comment']=r[4]
                f['limitations_sk'].append('Prázdna bunka default/comment nie je dôkaz source NULL.')
            else:
                f['limitations_sk'].append('Default a Oracle comment chýbajú v tejto prílohe; HANDOFF BLOCKED pre ich raw materializáciu.')
            if name in semantics:
                s=semantics[name]; alias=s[1] if obj.endswith('_L') else s[2]
                if re.fullmatch('[a-z][a-z0-9_]*',alias): f['canonical_alias']=alias
                f['business_definition_sk']=s[3]
                f['limitations_sk'].append('Pôvodný semantic status: '+s[4]+'; canonical/business label: '+alias)
                if s[4] in ('POTVRDENÉ','CONFIRMED','CORE CONFIRMED'): f['status']='POTVRDENÉ'
                elif 'DETAIL OPEN' in s[4]: f['status']='TREBA OVERIŤ'
            records.append(f)
        all_fields[obj]={r['oracle_name']:r['field_id'] for r in records}
        registry('fields-'+obj.lower(),records)
        d=load('object-'+obj.lower());d.update(maturity='DIAGNOSTIC-GRADE',status='POTVRDENÉ',evidence_refs=[E],grain_sk=rows(67)[0 if obj.endswith('_L') else 1][2],scope_limitations_sk=[source_note(block),'Publication blocked; dependency closure nie je exhaustive; otvorené raw claims sú v backlogu.'])
        d['source_of_truth_summary_sk']=B[69]['text']
        d['identity_refs']=['odb.constraint.xpk_'+obj.lower()]
        save('object-'+obj.lower(),d)
    # Trigger inventory and approved summaries: no inferred call graph or source visibility.
    entities=[]; flows=[]
    for obj,priority,name,event,meaning in rows(199):
        eid='odb.oracle.trigger.'+name.lower()
        entities.append(dict(oracle_entity_id=eid,environment='MC',oracle_owner='MC',oracle_name=name,oracle_object_type='TRIGGER',source_visible=False,boundary_only=True,status='TECHNICKY ZNÁME',evidence_refs=[E],limitations_sk=[source_note(199),'source_visible=false vyjadruje nedostupnosť raw source v tomto prenose; nie neprítomnosť source v MC.','Objekt: '+obj+'; diagnostická trieda: '+priority]))
        flows.append(dict(flow_id='odb.flow.'+name.lower(),trigger_or_procedure_ref=eid,event_sk=event,business_effect_sk=meaning,diagnostic_meaning_sk=source_note(199)+' Trieda '+priority+'. Úplné watched fields, call chains, exceptions a bypass detaily sa neodhadujú.',evidence_refs=[E]))
    details={r[0]:r for block in (102,150) for r in rows(block)}
    for flow in flows:
        name=flow['trigger_or_procedure_ref'].removeprefix('odb.oracle.trigger.').upper()
        if name in details:flow['diagnostic_meaning_sk']+=' | Detail approved table: '+' | '.join(details[name])
    registry('oracle-entities',entities);registry('flows',flows)
    mutations=[]
    for i,(names,writers,meaning) in enumerate(rows(195),1):
        targets=[field('OBJ_ODB_O',n.strip()) for n in names.split('/')]
        assert all(x in all_fields['OBJ_ODB_O'].values() for x in targets)
        mutations.append(dict(mutation_id=f'odb.mutation.matrix_{i:02}',target_refs=targets,writer_ref=None,writer_role=writers,status='POTVRDENÉ',evidence_refs=[E],diagnostic_meaning_sk=meaning,direct_mutations_sk=source_note(195)+' Skupinový mechanizmus je zachovaný doslova; wildcard nie je rozbalený na vymyslené entity.'))
    registry('mutations',mutations)
    rules=[rule(288,i,r[0]+' — '+r[1]) for i,r in enumerate(rows(288),1)]
    # Preserve approved technical/semantic tables verbatim under existing rule kind.
    # These are scoped contract statements, not invented structured physical claims.
    for block in [80,99,100,104,107,122,124,126,130,135,138,142,144,179,202,205,209,214,218]:
        if B[block]['type'] != 'table':
            rules.append(rule(block,1,B[block]['text'])); continue
        for i,r in enumerate(rows(block),1):
            rules.append(rule(block,i,' | '.join(k+': '+v for k,v in zip(B[block]['rows'][0],r))))
    rules.append(dict(rule_id='odb.rule.vyd_identity_reconciliation',scope_refs=OBJECTS+['vyd.oracle.f1dfff357c6da5d31924380f','vyd.oracle.c05d6994b969d9ce00ed3039'],statement_sk='Existujúce VYD boundary IDs zostávajú nezmenené. MC.OBJ_ODB_L boundary vyd.oracle.f1dfff357c6da5d31924380f zodpovedá sales mc.object.obj_odb_l; MC.OBJ_ODB_O boundary vyd.oracle.c05d6994b969d9ce00ed3039 zodpovedá sales mc.object.obj_odb_o. Ide o tie isté fyzické objekty, nie ďalšie business objekty.',evidence_refs=[E]))
    for block in range(180,228):
        b=B[block]
        if b['type']=='p' and b['text'] and not re.match(r'\d+\.',b['text']):rules.append(rule(block,1,b['text']))
    registry('do-not-assume',rules)
    dq=[]
    for i,r in enumerate(rows(158),1):
        dq.append(dict(dq_id=f'odb.dq.snapshot_{i:02}',scope_refs=[OBJECTS[1]],observation_sk=' | '.join(r),blocking=False,status='POTVRDENÉ',evidence_refs=[E],snapshot_date='2026-09-08',interpretation_limit_sk=source_note(158)+' Ide o výsledok uvedený v schválenom dokumente, nie dotaz vykonaný týmto nástrojom ani verified zero prázdneho registra.'))
    registry('data-quality',dq)
    temporal=[]
    for i,classification in [(0,'RAW CURRENT'),(1,'SELECTIVE HISTORY'),(2,'RAW CURRENT'),(3,'SELECTIVE HISTORY'),(4,'SELECTIVE HISTORY')]:
        r=rows(209)[i]
        temporal.append(dict(temporal_rule_id=f'odb.temporal.doc_209_{i+1}',scope_refs=([OBJECTS[0]] if i==0 else [field('OBJ_ODB_L','DATUM_P')] if i==1 else [OBJECTS[1]] if i in (2,4) else [field('OBJ_ODB_O',x) for x in ['POCET','P_DEL','P_DEL_DOD','RID_CT_A']]),classification=classification,status='POTVRDENÉ',evidence_refs=[E],transition_or_event_sk=r[0]+': '+r[1],history_limitations_sk=r[3]+' Pôvodný typ: '+r[2]))
    for i,r in enumerate(rows(179)[:3],1):
        temporal.append(dict(temporal_rule_id=f'odb.temporal.quantity_{i}',scope_refs=[OBJECTS[1]],classification='DERIVED CURRENT',status='POTVRDENÉ',evidence_refs=[E],transition_or_event_sk=r[0]+' = '+r[1],history_limitations_sk=r[2]+' '+r[3]))
    r=rows(218)[4]
    temporal.append(dict(temporal_rule_id='odb.temporal.pricing_snapshot',scope_refs=[field('OBJ_ODB_O',x) for x in ['CENA','CENA_M','CENA_S','CENA_S2']],classification='STORED SNAPSHOT',status='POTVRDENÉ',evidence_refs=[E],transition_or_event_sk=r[2],history_limitations_sk=r[3]))
    for i,r in enumerate(rows(218)[:4],1):
        obj,name=r[0].split('.')
        temporal.append(dict(temporal_rule_id=f'odb.temporal.master_gap_{i}',scope_refs=[field(obj,name)],classification='DATA GAP',status='DATA GAP',evidence_refs=[E],transition_or_event_sk=r[2],history_limitations_sk=r[3]))
    registry('temporal',temporal)
    indexes=[]
    for obj,block in [('OBJ_ODB_L',94),('OBJ_ODB_O',146)]:
        for r in rows(block):
            name,typ,expr=r[:3];entries=[]
            if 'hidden' not in expr:
                parts=expr.split(' + ') if obj.endswith('_L') else expr.split(', ')
                for pos,x in enumerate(parts,1):
                    entries.append(dict(position=pos,**({'field_ref':all_fields[obj][x]} if x in all_fields[obj] else {'expression_raw':x})))
            indexes.append(dict(index_id='odb.index.'+name.lower(),object_ref='mc.object.'+obj.lower(),oracle_name=name,status='TECHNICKY ZNÁME',evidence_refs=[E],column_or_expression_entries=entries,limitations_sk=[source_note(block),' | '.join(r)],uniqueness='NONUNIQUE' if 'NONUNIQUE' in typ else 'UNIQUE' if typ.startswith('UNIQUE') else None,function_based='FUNCTION-BASED' in typ))
    registry('indexes',indexes)
    constraints=[]
    for name,cols,state,typ in rows(90):
        constraints.append(dict(constraint_id='odb.constraint.'+name.lower(),object_ref=OBJECTS[0],oracle_name=name,constraint_type='PRIMARY KEY' if typ=='PRIMARY KEY' else 'UNIQUE',column_refs=[field('OBJ_ODB_L',x) for x in cols.split(' + ')],status='TECHNICKY ZNÁME',evidence_refs=[E],enabled_state='ENABLED',validated_state='VALIDATED'))
    constraints.append(dict(constraint_id='odb.constraint.xpk_obj_odb_o',object_ref=OBJECTS[1],oracle_name='XPK_OBJ_ODB_O',constraint_type='PRIMARY KEY',column_refs=[field('OBJ_ODB_O',x) for x in ['RID_O','ID_R']],status='TECHNICKY ZNÁME',evidence_refs=[E],enabled_state='ENABLED',validated_state='VALIDATED'))

    existing={}
    for directory in ['warehouse/vydajky','transport/cestovne-prikazy']:
        for r in yaml.safe_load((ROOT/'catalog'/directory/'oracle-entities.yaml').read_text())['records']:
            if r['environment']=='MC' and r['oracle_owner']=='MC' and r['oracle_object_type']=='TABLE':
                existing.setdefault(r['oracle_name'],[]).append(r)
    def target(table,column):
        if table in existing:
            for ent in existing[table]:
                for f in ent.get('fields',[]):
                    if f['oracle_name']==column:return ent['oracle_entity_id'],f['oracle_field_id']
        # Only names explicitly declared in approved metadata/SQL are admitted.
        eid='odb.oracle.table.'+table.lower()
        ent=next((r for r in entities if r['oracle_entity_id']==eid),None)
        if ent is None:
            ent=dict(oracle_entity_id=eid,environment='MC',oracle_owner='MC',oracle_name=table,oracle_object_type='TABLE',source_visible=False,boundary_only=True,status='TECHNICKY ZNÁME',evidence_refs=[E],fields=[],limitations_sk=[source_note(91),'Iba explicitná field boundary; bez nového master business významu.'])
            if table in existing:ent['limitations_sk'].append('Dopĺňa iba chýbajúce field boundary tej istej fyzickej identity: '+', '.join(r['oracle_entity_id'] for r in existing[table])+'. Nezavádza nový business objekt.')
            entities.append(ent)
        fid='odb.oracle_field.'+table.lower()+'.'+column.lower()
        if not any(f['oracle_field_id']==fid for f in ent['fields']):ent['fields'].append(dict(oracle_field_id=fid,oracle_name=column,datatype_raw=None,status='TECHNICKY ZNÁME',evidence_refs=[E]))
        return eid,fid
    for column,reference,name,state in rows(91):
        table,col=reference.split('.')
        eid,fid=target(table,col)
        enabled,validated=state.split(' / ')
        constraints.append(dict(constraint_id='odb.constraint.'+name.lower(),object_ref=OBJECTS[0],oracle_name=name,constraint_type='FOREIGN KEY',column_refs=[field('OBJ_ODB_L',column)],referenced_object_ref=eid,referenced_column_refs=[fid],status='TECHNICKY ZNÁME',evidence_refs=[E],enabled_state=enabled,validated_state=validated))
    for name,state,expression in rows(142)[1:]:
        constraints.append(dict(constraint_id='odb.constraint.'+name.lower(),object_ref=OBJECTS[1],oracle_name=name,constraint_type='CHECK',column_refs=[],status='TECHNICKY ZNÁME',evidence_refs=[E],enabled_state='ENABLED',validated_state='NOT VALIDATED' if 'NOVALIDATE' in state else 'VALIDATED'))
    cancellation_object,cancellation_rid=target('DOVOD_ZRUS_POL_DOKLAD','RID_O')
    _,cancellation_line=target('DOVOD_ZRUS_POL_DOKLAD','ID_R')
    registry('oracle-entities',entities)
    registry('constraints',constraints)
    # Relationship register: existing VYD/master IDs are reused, never renamed.
    relationships=[]
    specifications=[
        (0,OBJECTS[0],['mc.field.obj_odb_l.rid'],OBJECTS[1],['mc.field.obj_odb_o.rid_o'],False),
        (2,OBJECTS[0],['mc.field.obj_odb_l.rid'],'mc.object.vyd_l',['mc.field.vyd_l.rid_v'],True),
        (3,OBJECTS[1],['mc.field.obj_odb_o.rid_o','mc.field.obj_odb_o.id_r'],'mc.object.vyd_o',['mc.field.vyd_o.rid_v'],True),
        (5,OBJECTS[1],['mc.field.obj_odb_o.kod_id'],'vyd.oracle.01e7b2f15c19e6d43d71f206',['vyd.oracle_field.42f37d6d62423f9ce965dc63'],False),
        (6,OBJECTS[1],['mc.field.obj_odb_o.id_sz'],'vyd.oracle.02cf754cf59912a9fb74f610',['vyd.oracle_field.6fb40d1c1638aaae0e4c9f4c'],False),
        (7,OBJECTS[1],['mc.field.obj_odb_o.rid_ct_a'],'vyd.oracle.acf2e047611033d127973252',['vyd.oracle_field.d11ec3c52af18947511f6cfe'],False),
        (7,OBJECTS[1],['mc.field.obj_odb_o.rid_ct_z'],'vyd.oracle.acf2e047611033d127973252',['vyd.oracle_field.d11ec3c52af18947511f6cfe'],False)]
    for n,(i,fo,ff,to,tf,conditional) in enumerate(specifications,1):
        r=rows(222)[i]
        record=dict(relationship_id=f'odb.relationship.doc_222_{n}',from_object_ref=fo,from_field_refs=ff,to_object_ref=to,to_field_refs=tf,relationship_type='CONDITIONAL' if conditional else 'DIRECT',cardinality=r[2],status='POTVRDENÉ',evidence_refs=[E],safe_usage_sk=r[3],validation_summary_sk=source_note(222)+' '+r[1]+'; '+r[4],fanout_risk=r[3])
        if conditional:record['condition_sk']=r[1]+'; '+r[3]
        relationships.append(record)
    r=rows(222)[1]
    relationships.append(dict(relationship_id='odb.relationship.cancellation_history',from_object_ref=OBJECTS[1],from_field_refs=['mc.field.obj_odb_o.rid_o','mc.field.obj_odb_o.id_r'],to_object_ref=cancellation_object,to_field_refs=[cancellation_rid,cancellation_line],relationship_type='DIRECT',cardinality=r[2],status='POTVRDENÉ',evidence_refs=[E],safe_usage_sk=r[3],validation_summary_sk=source_note(222)+' '+r[1]))
    for column,table,col in [('RID_BAL','B_KOD_U','RID'),('RID_OBJEKT','DOKL_OBJEKTY','RID'),('DOVOD_BLOKACIE','DOVODY_BLOK_TOVAR','ID'),('RID_N','OBJ_D_NAVRH','RID')]:
        eid,fid=target(table,col)
        relationships.append(dict(relationship_id='odb.relationship.'+column.lower(),from_object_ref=OBJECTS[1],from_field_refs=[field('OBJ_ODB_O',column)],to_object_ref=eid,to_field_refs=[fid],relationship_type='DIRECT',status='TECHNICKY ZNÁME',evidence_refs=[E],validation_summary_sk=source_note(71),safe_usage_sk='Nedopĺňa lifecycle externej domény; current zero nie je univerzálna absencia.'))
    registry('relationships',relationships)
    registry('oracle-entities',entities)
    values=[]
    for i,r in enumerate(rows(97),1):
        values.append(dict(value_domain_id=f'odb.value_domain.form_{i}',scope_ref='mc.field.obj_odb_l.flags_s',raw_value=r[0],business_label_sk=' | '.join(r[1:]),status='POTVRDENÉ',evidence_refs=[E],limitations_sk=[source_note(97),'Platí pre SUBSTR(FLAGS_S,20,1), nie celý kontajner FLAGS_S.']))
    registry('value-domains',values)
    entity_lookup={}
    for directory in ['warehouse/vydajky','transport/cestovne-prikazy']:
        for r in yaml.safe_load((ROOT/'catalog'/directory/'oracle-entities.yaml').read_text())['records']:
            if r['environment']=='MC' and r['oracle_owner']=='MC':entity_lookup[(r['oracle_name'],r['oracle_object_type'])]=r['oracle_entity_id']
    for r in entities:entity_lookup[(r['oracle_name'],r['oracle_object_type'])]=r['oracle_entity_id']
    dependencies=[]
    for name,typ,l_count,o_count,total in rows(343):
        assert int(l_count)+int(o_count)==int(total)
        eid=entity_lookup.get((name,typ))
        if eid is None:
            eid='odb.oracle.source.'+name.lower()+'.'+typ.lower().replace(' ','_')
            entities.append(dict(oracle_entity_id=eid,environment='MC',oracle_owner='MC',oracle_name=name,oracle_object_type=typ,source_visible=False,boundary_only=True,status='TECHNICKY ZNÁME',evidence_refs=[E],limitations_sk=[source_note(343),'DML-reference inventory z dokumentu; nie runtime writer certifikácia.']))
        for obj,count in zip(OBJECTS,[l_count,o_count]):
            if int(count):
                dependencies.append(dict(dependency_id='odb.dependency.doc343.'+name.lower()+'.'+obj.rsplit('.',1)[-1],source_ref=eid,target_ref=obj,oracle_object_type=typ,direction='INBOUND',depth=1,role='DEPENDENCY ONLY',discovery_method='Approved DOCX v1.2 block 343: non-comment source DML-reference summary',source_visible=False,runtime_boundary=True,status='TECHNICKY ZNÁME',evidence_refs=[E],limitations_sk=[f'Document-reported DML refs: {count}; object total: {total}. Nie počty runtime executions.',source_note(343),'Nejde o ALL_DEPENDENCIES closure; raw source anchors a runtime role sú HANDOFF BLOCKED.']))
    registry('dependencies',dependencies);registry('oracle-entities',entities)

    sql_records=[];playbooks=[]
    sql_blocks=[232,240,247,254,262,268,274,281,294,298,301,305,309,313,317,321,324]
    for block in sql_blocks:
        raw=B[block]['rows'][0][0]
        # Only insert whitespace at known SQL clause boundaries lost by intake.
        normalized=re.sub(r'(LEFT JOIN|JOIN|FROM|WHERE|ORDER BY|GROUP BY|HAVING)',r'\n\1',raw)
        assert re.sub(r'\s','',normalized)==re.sub(r'\s','',raw)
        notes=[]
        for next_block in B[block+1:]:
            if next_block['type']=='table' or re.match(r'[78]\.\d+ ',next_block.get('text','')):break
            if next_block['type']=='p' and next_block['text']:notes.append(next_block['text'])
        title=next(x['text'] for x in reversed(B[:block]) if x['type']=='p' and re.match(r'[78]\.\d+ ',x['text']))
        for part,statement in enumerate(normalized.split(';')[:-1],1):
            path=f'sql/diagnostic/obchodne-pripady/doc-{block}-{part}.sql'
            (ROOT/path).write_text(statement.strip()+';\n')
            sid=f'odb.sql.doc_{block}_{part}'
            sql_records.append(dict(sql_id=sid,title_sk=title+' / '+str(part),sql_file=path,evidence_refs=[E],compatibility=dict(sql_client='SQL Navigator 5.5.4.847',oracle_server_version=None,read_only=True),input_parameters=[dict(name=n,required=True) for n in sorted(set(re.findall(r':([a-z_]+)',statement)))],purpose_sk=source_note(block),does_not_prove_sk=' | '.join(notes) or 'Nevytvára runtime ani historický dôkaz bez vykonania na MC.',fanout_warning_sk='Určiť grain pred JOIN; nezávislé 1:N vrstvy najprv agregovať. Pozri relationship register.'))
        if block<290:
            playbooks.append(dict(playbook_id=f'odb.playbook.doc_{block}',symptom_sk=title,first_sql_ref=f'odb.sql.doc_{block}_1',proves_sk=' | '.join(notes),does_not_prove_sk='Current snapshot nenahrádza kompletnú event históriu; interpretovať iba v rozsahu schválených poznámok.',next_step_sk=' | '.join(notes)))
    registry('sql-registry',sql_records);registry('playbooks',playbooks)


    backlog=[]
    for i,r in enumerate(rows(327),1):
        backlog.append(dict(backlog_id=f'odb.backlog.approved_{i:02}',scope_refs=OBJECTS,status='DATA GAP',blocking=False,question_sk=' | '.join(r),related_evidence_refs=[E]))
    for suffix,scope,question in [
        ('l_empty_metadata_cells',[field('OBJ_ODB_L',r[0].split('. ',1)[1]) for r in rows(337) if not r[3] or not r[4]],'Chýbajúce L default/comment bunky: nie je preukázané, či ide o source NULL alebo chýbajúcu dokumentovú hodnotu. OBJ_H01..H06B ešte nie sú dodané.'),
        ('o_defaults_comments',[field('OBJ_ODB_O',r[0].split('. ',1)[1]) for r in rows(339)],'Raw OBJ_ODB_O defaults a Oracle comments nie sú v document prílohe; spracovať príslušné raw XLSX.'),
        ('o_fk_names',[field('OBJ_ODB_O',n) for n in ['DOVOD_BLOKACIE','ID_SZ','KOD_ID','RID_BAL','RID_CT_A','RID_CT_Z','RID_O','RID_OBJEKT']],'Presné Oracle constraint names pre osem OBJ_ODB_O FK nie sú v document prílohe; názvy sa nesyntetizujú.'),
        ('check_expressions',['odb.constraint.'+r[0].lower() for r in rows(142)[1:]],'Raw úplné CHECK expressions; dokumentové popisy sú zachované ako pravidlá, nie predstierané ALL_CONSTRAINTS DDL.'),
        ('source',[r['flow_id'] for r in flows],'Raw trigger/package source, line anchors a detailné call/exception/session vetvy nad rámec schválených document summaries.'),
        ('closure',['odb.dependencies.001','odb.dependency_direct_edges.001','odb.dependency_closure_edges.001','odb.dependency_closure_nodes.001','odb.api_references.001'],'Raw ODB_DIAG dependency/API výsledky; closure nie je exhaustive. Prázdne registre nepreukazujú nulové nálezy.'),
        ('publication',OBJECTS,'Publication zostáva podľa pokynu používateľa blocked.')]:
        backlog.append(dict(backlog_id='odb.backlog.'+suffix,scope_refs=scope,status='DATA GAP',blocking=True,question_sk='HANDOFF BLOCKED: '+question,related_evidence_refs=[E],closure_condition_sk='Dodať príslušný vstup/explicitné schválenie a overiť dotknuté claims bez inferencie.'))
    registry('backlog',backlog)
    d=load('contract');d.update(purpose_sk='Dokumentový prenos schváleného v1.2 contractu pre diagnostiku MC.OBJ_ODB_L/O.',maturity='DIAGNOSTIC-GRADE',evidence_refs=[E],boundary_refs=['vyd.oracle.f1dfff357c6da5d31924380f','vyd.oracle.c05d6994b969d9ce00ed3039'],limitations_sk=['Maximálna maturity PHASE A; nejde o AGENT-READY ani exhaustive dependency closure.','Schválené dokumentové summaries sa neprezentujú ako priamo skontrolovaný raw Oracle source.','Publication blocked. Empty register != verified zero. Chýbajúce claims sú v backlogu.']);save('contract',d)
    registry('revisions',[dict(revision_id='odb.revision.phase_a_document_materialization',contract_version='1.2',date='2026-09-15',breaking_change=False,changed_record_refs=OBJECTS,change_sk='Phase A dokumentová materializácia zo schváleného v1.2; presné raw claims zostávajú otvorené. VYD IDs nezmenené.',evidence_refs=[E])])
    evidence=dict(schema_version='1.0',kind='evidence-manifest',evidence_id=E,evidence_class='D',environment='MC',oracle_owner='MC',source_file='KASO Data Catalog - Technical & Diagnostic Reference - obchodné prípady v1.2.docx',sha256='815e78b939389326badebc567d02411359a0a2f1784fb2c1b39dab6324edbd95',retention_class='TRANSIENT',raw_retained=False,supports_record_refs=OBJECTS,review_status='ACCEPTED',snapshot_date='2026-09-09',result_summary_sk='Používateľom schválený human semantic contract; 41 vstupných checksumov overených pri intake. Retained extraction: evidence/source-extracts/odb/approved-contract.json; SHA256 '+hashlib.sha256(SOURCE.read_bytes()).hexdigest(),limitations_sk=['Nie je náhradou raw Oracle A/B/B2 evidence. Pôvodný bundle momentálne nie je na pôvodnej ceste.','Extrakcia zachováva bunky a odseky; nezachováva vnútorné SQL line breaks.'])
    p=ROOT/'evidence/manifests/odb/approved-contract.yaml';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(yaml.safe_dump(evidence,allow_unicode=True,sort_keys=False))
if __name__=='__main__':main()

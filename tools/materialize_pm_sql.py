#!/usr/bin/env python3
"""Materialize read-only Product Master diagnostics from approved handoff/source contracts."""
from pathlib import Path
import re
import yaml

ROOT=Path(__file__).resolve().parents[1]
DOMAIN=ROOT/'catalog/master/skladove-karty'
OUT=ROOT/'sql/diagnostic/skladove-karty'
OUT.mkdir(parents=True,exist_ok=True)
registry=[]
def add(name,title,sql,grain,fanout,proves,limits,packs):
    path=OUT/(name+'.sql')
    header='\n'.join('-- '+k+': '+v for k,v in [('Scope','MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown'),('Grain',grain),('Fan-out',fanout),('Proves',proves),('Does not prove',limits),('Evidence',', '.join(packs))])
    path.write_text(header+'\n'+sql.strip()+'\n')
    registry.append(dict(sql_id='pm.sql.'+name.replace('-','_'),title_sk=title,sql_file=path.relative_to(ROOT).as_posix(),purpose_sk=title,input_parameters=[dict(name=p.lower(),required=True,description_sk='Explicit caller-supplied context; preserve code/RID text.') for p in sorted(set(re.findall(r'(?<!:):([A-Za-z][A-Za-z0-9_]*)',sql)))],result_grain_sk=grain,fanout_warning_sk=fanout,proves_sk=proves,does_not_prove_sk=limits,compatibility=dict(sql_client='SQL Navigator 5.5.4.847',oracle_server_version=None,read_only=True,notes_sk='Offline safety checked; no Oracle execution performed.'),evidence_refs=['pm.evidence.handoff']+['pm.evidence.'+p.lower().replace('-','-') for p in packs]))

add('identity','Identita skladovej karty',"""
SELECT ID, SK_ID, RID, RID_OBJ, INT_KOD, SKLAD
FROM MC.SKLAD_KARTA
WHERE (:id IS NOT NULL AND ID=:id)
   OR (:sk_id IS NOT NULL AND SK_ID=:sk_id)
   OR (:rid IS NOT NULL AND RID=:rid)
   OR (:int_kod IS NOT NULL AND INT_KOD=:int_kod);
""",'One root card','No joins; multiple identifiers may select different cards.','Current identity matches.','Historical/global uniqueness; INT_KOD is text, not numeric.',['MP01-A','MP02-A'])
add('current-state','Aktuálny stav',"""SELECT ID,INT_KOD,USED,STAV,S_STAMP,I_STAMP,U_STAMP,N_STAMP
FROM MC.SKLAD_KARTA WHERE ID=:id;""",'One card','None','Independent USED and STAV plus technical stamps.','USED=1 is not in sale; N_STAMP not creation; no full history.',['MP02-B','MP03-A'])
add('lookups','Stav a priame referencie',"""SELECT sk.ID,sk.INT_KOD,sk.STAV,s.NAZOV AS STAV_NAZOV
FROM MC.SKLAD_KARTA sk LEFT JOIN MC.STAVY_SK s ON s.ID=sk.STAV
WHERE sk.ID=:id;""",'One card and referenced state','Target PK limits fan-out; do not filter lookup S_STAMP silently.','Current state dictionary resolution.','Lookup lifecycle alone does not invalidate an existing reference.',['MP01-B','MP02-J'])
add('logistics','Balenia a EAN podľa úrovne',"""SELECT sk.ID,sk.INT_KOD,lb.RID AS LB_RID,lb.S_STAMP AS LB_S_STAMP,
 lb.FLAGS_B AS LB_FLAGS_B,lb.EAN,lb.EAN_SBK,lb.EAN_KART,lb.EAN_ROW,lb.EAN_PAL,
 b.RID AS CODE_RID,b.SKRATKA,b.BAL,b.S_STAMP AS CODE_S_STAMP,b.FLAGS_B AS CODE_FLAGS_B
FROM MC.SKLAD_KARTA sk
LEFT JOIN MC.SKLAD_KARTA_LB lb ON lb.KOD_ID=sk.ID
LEFT JOIN MC.B_KOD_U b ON b.RID_SKLAD_KARTA_LB=lb.RID
WHERE sk.ID=:id;""",'Card x packaging x code','1:N:N; do not sum root/packaging measures after joining codes.','Current packaging hierarchy and level-associated codes.','Root logistics fields are not universal roll-up; missing packaging not universally an error.',['LM-02A','LM-02E'])
add('ean-anomalies','Aktívne balenie bez presného kusového EAN',"""SELECT lb.RID,lb.KOD_ID,lb.EAN,lb.FLAGS_B
FROM MC.SKLAD_KARTA_LB lb
WHERE lb.S_STAMP='0'
 AND NOT EXISTS (SELECT 1 FROM MC.B_KOD_U b
 WHERE b.RID_SKLAD_KARTA_LB=lb.RID AND b.S_STAMP='0' AND b.BAL=0 AND b.SKRATKA=lb.EAN);""",'One active packaging row','Anti-join avoids multiplying packaging rows.','Missing exact active piece-level code candidate.','Universal business error or remediation; scope by product use.',['LM-03C'])
add('supplier','Dodávateľský kód a hlavný dodávateľ',"""SELECT sk.ID,sk.INT_KOD,sk.DOD_SK,sk.DOD_KOD,
 d.ID AS SUPPLIER_ROW,d.ID_DODAVATELA,d.KOD_DOD,d.VYROBCA_KOD,d.S_STAMP
FROM MC.SKLAD_KARTA sk LEFT JOIN MC.SKLAD_DODAVATEL d ON d.KOD_ID=sk.ID
WHERE sk.ID=:id;""",'Card x supplier row','1:N; preserve ID_DODAVATELA and lifecycle.','Root versus supplier satellite values.','DOD_KOD/KOD_DOD/VYROBCA_KOD equivalence or continuous synchronization.',['PM-05E'])
add('vat-context','DPH podľa skladového kontextu',"""SELECT sk.ID,sk.INT_KOD,sk.UROVEN_DPH AS ROOT_UROVEN_DPH,
 fu.ID AS FU_ID,fu.SKLAD_P,fu.UROVEN_DPH AS LOCAL_UROVEN_DPH,fu.S_STAMP
FROM MC.SKLAD_KARTA sk LEFT JOIN MC.SKLAD_KARTA_FU fu
 ON fu.KOD_ID=sk.ID AND fu.SKLAD_P=:sklad_p AND fu.S_STAMP='0'
WHERE sk.ID=:id;""",'Card x matching active warehouse override','Expose duplicates; no ROWNUM=1.','Root and contextual VAT values.','Root VAT is not universal; does not execute session-dependent API resolution.',['PM-05F'])
add('partner-grain','Duplicity kontextu partnerských kódov',"""SELECT KOD_ID,PARTNER,BALENIE,COUNT(*) AS ROW_COUNT
FROM MC.SKLAD_PARTNER_KODY WHERE S_STAMP='0'
GROUP BY KOD_ID,PARTNER,BALENIE HAVING COUNT(*)>1;""",'KOD_ID + PARTNER + BALENIE','Aggregate only at exact natural grain.','Current duplicate active grain.','PARTNER + KOD_PARTNERA is not globally unique.',['PM-05G'])
add('typed-notes','Aktuálne typované poznámky ku karte',"""SELECT sk.ID,sk.INT_KOD,n.ID AS NOTE_ID,n.TYP,t.NAZOV AS NOTE_TYPE,
 n.POZNAMKA,n.S_STAMP,n.ZOBRAZIT_OD,n.ZOBRAZIT_DO
FROM MC.SKLAD_KARTA sk JOIN MC.CIS_POZNAMKY n ON n.RID_V=sk.RID
LEFT JOIN MC.CIS_POZNAMKY_TYPY t ON t.ID=n.TYP
WHERE sk.ID=:id AND n.S_STAMP='0';""",'One active product-context typed note','1:N root-to-note; no root sums.','Current operational typed-note values and dictionary meaning.','Not every note is allergen; not full historical or downstream manufacturing truth.',['PM-08E','PM-09B'])
# Dictionary IDs are supplied as binds instead of guessing classification from spelling.
add('allergen-types','Priamy alergén a krížová kontaminácia',"""SELECT sk.ID,sk.INT_KOD,n.ID AS NOTE_ID,n.TYP,t.NAZOV,
 CASE WHEN n.TYP=:direct_type THEN 'DIRECT'
      WHEN n.TYP=:cross_type THEN 'CROSS_CONTAMINATION' END AS SELECTED_CONTEXT
FROM MC.SKLAD_KARTA sk JOIN MC.CIS_POZNAMKY n ON n.RID_V=sk.RID
JOIN MC.CIS_POZNAMKY_TYPY t ON t.ID=n.TYP
WHERE sk.ID=:id AND n.S_STAMP='0' AND n.TYP IN (:direct_type,:cross_type)
 AND :direct_type<>:cross_type;""",'One selected active allergen note','Multiple notes per card/type remain visible.','Separate caller-selected dictionary types.','Caller must select approved dictionary types; 00048/00052 relation unresolved; no free-text inference.',['PM-09B'])
add('coefficients','Aktívne a účinné nákladové koeficienty',"""SELECT p.ID,p.KOD_ID,p.NK_ID,n.NAZOV,n.TYP_UPL,n.ZARADENIE,n.TYP_KRAJINY,
 p.MNOZSTVO,p.PERCENTO,p.FIX_NAKL,p.DATUM_OD,p.DATUM_DO,p.S_STAMP,n.S_STAMP AS NK_S_STAMP,
 CASE WHEN p.S_STAMP='0' AND :as_of BETWEEN NVL(p.DATUM_OD,:as_of) AND NVL(p.DATUM_DO,:as_of)
 THEN 1 ELSE 0 END AS EFFECTIVE_AT_DATE
FROM MC.SK_NAKL_POLOZKY p LEFT JOIN MC.NAKL_KOEF n ON n.ID=p.NK_ID
WHERE p.KOD_ID=:id;""",'One stored assignment','Multiple historical assignments; do not collapse to ROWNUM=1.','Stored lifecycle and effective-date comparison.','Current coefficient registry is not historical truth; mask is not country code; names not jurisdiction.',['PM-04D','PM-05B'])

BOM="""WITH component_mapping AS (
 SELECT sk.ID AS KOD_ID,sc.ID AS COMPONENT_KOD_ID,l.RID AS BOM_RID,o.POCET,
 sc.HMOTNOST_NETTO,du.DU_7,du.DU_8,du.DU_9,
 CASE WHEN du.DU_7 IS NULL THEN 0
      WHEN TRIM(TRANSLATE(TRIM(du.DU_7),'0123456789.',' ')) IS NULL
       AND LENGTH(TRIM(du.DU_7))-LENGTH(REPLACE(TRIM(du.DU_7),'.',''))<=1
      THEN TO_NUMBER(TRIM(du.DU_7),'999999999D999999999','NLS_NUMERIC_CHARACTERS=''.,''') END AS RECYCLED_PCT
 FROM MC.VYR_KUSOVNIKY_L l JOIN MC.VYR_KUSOVNIKY_O o ON o.RID_O=l.RID
 JOIN MC.VYR_KATALOG vl ON vl.ID=l.ID_VYR
 JOIN MC.VYR_KATALOG vo ON vo.ID=o.ID_VYR
 JOIN MC.SKLAD_KARTA sk ON sk.INT_KOD=vl.INT_KOD
 JOIN MC.SKLAD_KARTA sc ON sc.INT_KOD=vo.INT_KOD
 JOIN MC.CIS_DU_O du ON du.RID=sc.RID
 WHERE l.S_STAMP='0' AND o.S_STAMP='0' AND SUBSTR(vl.INT_KOD,1,1)='3'
 AND (du.DU_8 IS NOT NULL OR du.DU_9 IS NOT NULL)
), contributions AS (
 SELECT c.*,1 AS TOKEN_POSITION,'VIRGIN' AS MATERIAL_PART,
 SUBSTR(DU_8,1,INSTR(DU_8||';',';')-1) AS NK_ID,
 (100-RECYCLED_PCT)/100*HMOTNOST_NETTO*POCET AS EXPECTED_PART FROM component_mapping c
 UNION ALL
 SELECT c.*,1,'RECYCLED',SUBSTR(DU_9,1,INSTR(DU_9||';',';')-1),
 RECYCLED_PCT/100*HMOTNOST_NETTO*POCET FROM component_mapping c
 UNION ALL
 SELECT c.*,2,'VIRGIN',
 CASE WHEN INSTR(DU_8,';')>0 THEN SUBSTR(DU_8,INSTR(DU_8,';')+1,
 INSTR(DU_8||';',';',1,2)-INSTR(DU_8,';')-1) END,
 (100-RECYCLED_PCT)/100*HMOTNOST_NETTO*POCET FROM component_mapping c
 UNION ALL
 SELECT c.*,2,'RECYCLED',
 CASE WHEN INSTR(DU_9,';')>0 THEN SUBSTR(DU_9,INSTR(DU_9,';')+1,
 INSTR(DU_9||';',';',1,2)-INSTR(DU_9,';')-1) END,
 RECYCLED_PCT/100*HMOTNOST_NETTO*POCET FROM component_mapping c
), expected AS (
 SELECT KOD_ID,NK_ID,COUNT(*) AS CONTRIBUTION_ROWS,
 COUNT(DISTINCT COMPONENT_KOD_ID) AS COMPONENT_COUNT,
 SUM(CASE WHEN EXPECTED_PART IS NULL THEN 1 ELSE 0 END) AS NULL_INPUT_ROWS,
 SUM(EXPECTED_PART) AS EXPECTED_MNOZSTVO
 FROM contributions WHERE NK_ID IS NOT NULL GROUP BY KOD_ID,NK_ID
), stored AS (
 SELECT KOD_ID,NK_ID,COUNT(*) AS STORED_ROWS,SUM(MNOZSTVO) AS STORED_MNOZSTVO
 FROM MC.SK_NAKL_POLOZKY WHERE S_STAMP='0' AND POZN LIKE 'Import z kusovníka;%'
 GROUP BY KOD_ID,NK_ID
), audit AS (
 SELECT NVL(e.KOD_ID,s.KOD_ID) AS KOD_ID,NVL(e.NK_ID,s.NK_ID) AS NK_ID,
 e.CONTRIBUTION_ROWS,e.COMPONENT_COUNT,e.NULL_INPUT_ROWS,e.EXPECTED_MNOZSTVO,
 s.STORED_ROWS,s.STORED_MNOZSTVO,
 CASE WHEN e.KOD_ID IS NULL THEN 'STALE_AUTO_ROW'
      WHEN e.NULL_INPUT_ROWS>0 THEN 'MISSING_OR_UNSUPPORTED_INPUT'
      WHEN s.KOD_ID IS NULL THEN 'MISSING_STORED'
      WHEN e.COMPONENT_COUNT>1 THEN 'MULTI_COMPONENT_SAME_COEF'
      WHEN ABS(e.EXPECTED_MNOZSTVO-s.STORED_MNOZSTVO)>:tolerance THEN 'MISMATCH'
      ELSE 'MATCH' END AS AUDIT_STATUS
 FROM expected e FULL OUTER JOIN stored s ON s.KOD_ID=e.KOD_ID AND s.NK_ID=e.NK_ID
)
"""
limit='Diagnostic aggregate, not a corrected writer. Prefix 3 is executable heuristic, not taxonomy. O.POCET may include norm loss; no extra loss multiplication. Current INT_KOD and DU uniqueness must be checked. Unsupported DU7 stays NULL. No historical eligibility or pure packed-weight claim.'
for name,where,title in [('bom-audit','1=1','BOM aktuálny súčet proti uloženým hodnotám'),('dq-coef-001',"AUDIT_STATUS='STALE_AUTO_ROW'",'DQ-COEF-001 zastarané BOM-auto riadky'),('dq-coef-002','COMPONENT_COUNT>1','DQ-COEF-002 viac komponentov pre rovnaký koeficient'),('dq-coef-003','NULL_INPUT_ROWS=0 AND STORED_ROWS IS NOT NULL AND ABS(EXPECTED_MNOZSTVO-STORED_MNOZSTVO)>:tolerance','DQ-COEF-003 rozdiel recompute'),('dq-coef-004',"AUDIT_STATUS='MISSING_STORED'",'DQ-COEF-004 chýbajúci uložený koeficient')]:
    add(name,title,BOM+'SELECT * FROM audit WHERE '+where+';','One current product x coefficient group','Components aggregated before stored join; validate code and DU uniqueness before interpreting.',title,limit,['PM-06C','PM-07A','PM-07B'])
add('dq-coef-005','DQ-COEF-005 prefix názvu nie je krajina',"""SELECT ID,NAZOV,TYP_KRAJINY,ZARADENIE,TYP_UPL,S_STAMP
FROM MC.NAKL_KOEF WHERE SUBSTR(NAZOV,1,2) IN ('SK','CZ');""",'One coefficient','None','Legacy SK/CZ name prefixes alongside applicability mask.','No jurisdiction classification from name; reporting context remains downstream.',['PM-04C'])
add('dq-coef-006','DQ-COEF-006 história a lifecycle sugar assignments',"""SELECT p.KOD_ID,p.NK_ID,COUNT(*) AS ALL_HISTORY_ROWS,
 SUM(CASE WHEN p.S_STAMP='0' AND :as_of BETWEEN NVL(p.DATUM_OD,:as_of) AND NVL(p.DATUM_DO,:as_of) THEN 1 ELSE 0 END) AS EFFECTIVE_ROWS
FROM MC.SK_NAKL_POLOZKY p JOIN MC.NAKL_KOEF n ON n.ID=p.NK_ID
WHERE n.ZARADENIE=7 GROUP BY p.KOD_ID,p.NK_ID;""",'Product x sugar coefficient','All history retained intentionally; do not join directly to transaction totals.','Potential row multiplication/lifecycle exposure if downstream filter omitted.','Not every historical row is a business error; exact affected report SQL is boundary.',['PM-07C'])
add('flag12','Výluka z odpadového reportingu',"""SELECT ID,INT_KOD,NAZOV,SUBSTR(FLAGS,12,1) AS FLAG12,USED,STAV
FROM MC.SKLAD_KARTA WHERE SUBSTR(FLAGS,12,1)='1';""",'One excluded current card','None','Current FLAGS[12] reporting exclusion.','Private-label/cofilling cannot be inferred from name; coefficients may validly exist; no full flag history.',['PM-09E'])
add('recycling-reconciliation','DQ-REPORT-001 porovnanie RF total s FLAGS[12]',"""SELECT SUM(o.POCET*p.MNOZSTVO/1000) AS TONY_ALL,
 SUM(CASE WHEN SUBSTR(sk.FLAGS,12,1)='0' THEN o.POCET*p.MNOZSTVO/1000 ELSE 0 END) AS TONY_FLAG12_OK,
 SUM(CASE WHEN SUBSTR(sk.FLAGS,12,1)='1' THEN o.POCET*p.MNOZSTVO/1000 ELSE 0 END) AS TONY_FLAG12_ONE,
 SUM(CASE WHEN SUBSTR(sk.FLAGS,12,1) IS NULL OR SUBSTR(sk.FLAGS,12,1) NOT IN ('0','1') THEN o.POCET*p.MNOZSTVO/1000 ELSE 0 END) AS TONY_OTHER_OR_NULL
FROM MC.V_DLAF_C_L l JOIN MC.V_DLAF_C_O o ON o.RID_O=l.RID
JOIN MC.SKLAD_KARTA sk ON sk.SK_ID=o.KOD_ID
JOIN MC.SK_NAKL_POLOZKY p ON p.KOD_ID=sk.SK_ID
JOIN MC.OBCH_PARTNERI op ON op.ID=l.PARTNER
JOIN MC.NAKL_KOEF nk ON nk.ID=p.NK_ID
WHERE l.STORNO='0'
 AND (SELECT SUBSTR(NVL(ct.NAZOV_N,ct.NAZOV),1,254) FROM MC.CIS_TREE ct WHERE ct.ID=op.ID_TREE)=:market
 AND SUBSTR(nk.NAZOV||' \\'||nk.ID,1,2)=:market
 AND l.DATUM>=:date_from AND l.DATUM<:date_to_exclusive
 AND (:market='CZ' OR SUBSTR(op.FLAGS,16,1)<>'1');""",'One report-scope aggregate','Transaction line x every stored coefficient assignment, as captured RF footer; intentional legacy fan-out.','RF footer comparison retaining legacy name-prefix filter, plus explicit eligibility split.','Does not fix report or master. No added coefficient lifecycle filter. Market is explicit SK/CZ context, not inferred jurisdiction; date binds must match captured whole-month periods. Current values cannot reconstruct historical master.',['PM-11N','PM-11P','PM-11S2'])
add('nahrada','Technické skupiny NAHRADA',"""SELECT a.ID AS ANCHOR_ID,a.INT_KOD AS ANCHOR_CODE,m.ID AS MEMBER_ID,m.INT_KOD,m.USED,m.STAV,
 CASE WHEN m.ID=m.NAHRADA THEN 'SELF_ANCHOR' ELSE 'MEMBER' END AS TECHNICAL_ROLE
FROM MC.SKLAD_KARTA m LEFT JOIN MC.SKLAD_KARTA a ON a.ID=m.NAHRADA
WHERE m.NAHRADA<>0 AND (:anchor_id IS NULL OR m.NAHRADA=:anchor_id);""",'One nonzero NAHRADA member','Anchor repeated across members; no merging.','Technical self-anchor membership only.','Physical/commercial substitutability, exact runtime business use, automatic remediation.',['PM-10F'])
add('typ-t','Nevyriešený TYP_T',"""SELECT ID,INT_KOD,TYP_T,T_TOVARU,USED,STAV FROM MC.SKLAD_KARTA WHERE TYP_T='00';""",'One current unresolved card','None','Current unresolved value population.','No guessed meaning, dictionary join or cleanup rule.',['PM-10B2'])
add('dependency-trace','Priame dependency bez runtime klasifikácie',"""SELECT OWNER,NAME,TYPE,REFERENCED_OWNER,REFERENCED_NAME,REFERENCED_TYPE
FROM ALL_DEPENDENCIES
WHERE REFERENCED_OWNER='MC' AND REFERENCED_NAME IN ('SKLAD_KARTA','C_SKLAD_KARTA');""",'One visible compile-time dependency','Multiple types per object possible.','Visible static dependency surface.','Reader/writer/caller role, external runtime completeness or absence.',['MP01-G','MP04-A'])
add('end-of-sale-source','STAV=8 a zachovaná ochrana zámku',"""SELECT s.OWNER,s.NAME,s.TYPE,s.LINE,s.TEXT
FROM ALL_SOURCE s
WHERE s.OWNER='MC' AND
 ((s.NAME IN ('T_SKLAD_KARTA_STAV_AFTER_MC','T_OBCH_PL_LOCK_MC') AND s.TYPE='TRIGGER')
 OR (s.NAME='MCCARTER_PLAN' AND s.TYPE='PACKAGE BODY' AND s.LINE BETWEEN 1030 AND 1070))
ORDER BY s.NAME,s.TYPE,s.LINE;""",'One source line','No data joins','Source-visible POZN marker exception and ordinary BITAND(STAV,2)=2 guard; replication condition.','Executing or globally bypassing locks. Package line window is dated PM-12A locator and may move after DDL.',['PM-12A'])
add('end-of-sale-rows','Ukončený predaj aktuálne prognózy',"""SELECT o.RID_O,o.KOD_ID,o.OBDOBIE,o.PLAN_POCET2,o.POZN,o.STAV,
 BITAND(o.STAV,2) AS LOCK_BIT,l.TYP_PLANU
FROM MC.OBCH_PL_O o JOIN MC.OBCH_PL_L l ON l.RID=o.RID_O
WHERE o.KOD_ID=:id AND o.POZN LIKE '%Ukončený predaj%';""",'One marked current forecast row','Header join by RID; do not infer causal history from note alone.','Current quantity/marker/lock state for explicit SKU.','Complete event history, global lock bypass or provenance solely from matching note.',['PM-12A'])

write=dict(schema_version='1.0',kind='sql-registry',id='pm.sql_registry',records=registry)
(DOMAIN/'sql-registry.yaml').write_text(yaml.safe_dump(write,allow_unicode=True,sort_keys=False,width=110))
symptoms=[('Nesedí stav skladovej karty','current-state'),('Chýba / nesedí EAN alebo balenie','logistics'),('Nesedí dodávateľský kód','supplier'),('Nesedí DPH','vat-context'),('Nesedia alergény','typed-notes'),('Nesedia nákladové/recyklačné koeficienty','bom-audit'),('Recyklačný fond total nesedí detailu','recycling-reconciliation'),('Historický report nesedí dnešnej karte','current-state'),('NAHRADA vyzerá nesprávne','nahrada'),('STAV=8 a uzamknutá prognóza','end-of-sale-source')]
playbooks=[]
for i,(title,name) in enumerate(symptoms,1):
    q=next(r for r in registry if r['sql_file'].endswith('/'+name+'.sql'))
    playbooks.append(dict(playbook_id=f'pm.playbook.{i:02}',symptom_sk=title,first_sql_ref=q['sql_id'],proves_sk=q['proves_sk'],does_not_prove_sk=q['does_not_prove_sk'],next_step_sk='Interpret with the linked grain/fan-out contract and approved source/evidence. Escalate unresolved business meaning; no automatic master-data fix.',flow_refs=['pm.flow.end_of_sale','pm.flow.forecast_lock'] if name=='end-of-sale-source' else [],dependency_or_boundary_refs=[],temporal_boundary_sk='RAW CURRENT / selective history; no arbitrary historical reconstruction.'))
(DOMAIN/'playbooks.yaml').write_text(yaml.safe_dump(dict(schema_version='1.0',kind='playbooks',id='pm.playbooks',records=playbooks),allow_unicode=True,sort_keys=False,width=110))
contract=yaml.safe_load((DOMAIN/'contract.yaml').read_text())
for ref in ['pm.sql_registry','pm.playbooks']:
    if ref not in contract['component_refs']:contract['component_refs'].append(ref)
(DOMAIN/'contract.yaml').write_text(yaml.safe_dump(contract,allow_unicode=True,sort_keys=False,width=110))
print(f'PASS: {len(registry)} read-only diagnostics and {len(playbooks)} playbooks.')

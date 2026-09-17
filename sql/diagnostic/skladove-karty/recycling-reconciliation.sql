-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One report-scope aggregate
-- Fan-out: Transaction line x every stored coefficient assignment, as captured RF footer; intentional legacy fan-out.
-- Proves: RF footer comparison retaining legacy name-prefix filter, plus explicit eligibility split.
-- Does not prove: Does not fix report or master. No added coefficient lifecycle filter. Market is explicit SK/CZ context, not inferred jurisdiction; date binds must match captured whole-month periods. Current values cannot reconstruct historical master.
-- Evidence: PM-11N, PM-11P, PM-11S2
SELECT SUM(o.POCET*p.MNOZSTVO/1000) AS TONY_ALL,
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
 AND SUBSTR(nk.NAZOV||' \'||nk.ID,1,2)=:market
 AND l.DATUM>=:date_from AND l.DATUM<:date_to_exclusive
 AND (:market='CZ' OR SUBSTR(op.FLAGS,16,1)<>'1');

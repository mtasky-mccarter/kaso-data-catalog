-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One stored assignment
-- Fan-out: Multiple historical assignments; do not collapse to ROWNUM=1.
-- Proves: Stored lifecycle and effective-date comparison.
-- Does not prove: Current coefficient registry is not historical truth; mask is not country code; names not jurisdiction.
-- Evidence: PM-04D, PM-05B
SELECT p.ID,p.KOD_ID,p.NK_ID,n.NAZOV,n.TYP_UPL,n.ZARADENIE,n.TYP_KRAJINY,
 p.MNOZSTVO,p.PERCENTO,p.FIX_NAKL,p.DATUM_OD,p.DATUM_DO,p.S_STAMP,n.S_STAMP AS NK_S_STAMP,
 CASE WHEN p.S_STAMP='0' AND :as_of BETWEEN NVL(p.DATUM_OD,:as_of) AND NVL(p.DATUM_DO,:as_of)
 THEN 1 ELSE 0 END AS EFFECTIVE_AT_DATE
FROM MC.SK_NAKL_POLOZKY p LEFT JOIN MC.NAKL_KOEF n ON n.ID=p.NK_ID
WHERE p.KOD_ID=:id;

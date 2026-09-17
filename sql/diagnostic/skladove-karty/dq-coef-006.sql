-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: Product x sugar coefficient
-- Fan-out: All history retained intentionally; do not join directly to transaction totals.
-- Proves: Potential row multiplication/lifecycle exposure if downstream filter omitted.
-- Does not prove: Not every historical row is a business error; exact affected report SQL is boundary.
-- Evidence: PM-07C
SELECT p.KOD_ID,p.NK_ID,COUNT(*) AS ALL_HISTORY_ROWS,
 SUM(CASE WHEN p.S_STAMP='0' AND :as_of BETWEEN NVL(p.DATUM_OD,:as_of) AND NVL(p.DATUM_DO,:as_of) THEN 1 ELSE 0 END) AS EFFECTIVE_ROWS
FROM MC.SK_NAKL_POLOZKY p JOIN MC.NAKL_KOEF n ON n.ID=p.NK_ID
WHERE n.ZARADENIE=7 GROUP BY p.KOD_ID,p.NK_ID;

-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One marked current forecast row
-- Fan-out: Header join by RID; do not infer causal history from note alone.
-- Proves: Current quantity/marker/lock state for explicit SKU.
-- Does not prove: Complete event history, global lock bypass or provenance solely from matching note.
-- Evidence: PM-12A
SELECT o.RID_O,o.KOD_ID,o.OBDOBIE,o.PLAN_POCET2,o.POZN,o.STAV,
 BITAND(o.STAV,2) AS LOCK_BIT,l.TYP_PLANU
FROM MC.OBCH_PL_O o JOIN MC.OBCH_PL_L l ON l.RID=o.RID_O
WHERE o.KOD_ID=:id AND o.POZN LIKE '%Ukončený predaj%';

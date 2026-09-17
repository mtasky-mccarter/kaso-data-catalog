-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: KOD_ID + PARTNER + BALENIE
-- Fan-out: Aggregate only at exact natural grain.
-- Proves: Current duplicate active grain.
-- Does not prove: PARTNER + KOD_PARTNERA is not globally unique.
-- Evidence: PM-05G
SELECT KOD_ID,PARTNER,BALENIE,COUNT(*) AS ROW_COUNT
FROM MC.SKLAD_PARTNER_KODY WHERE S_STAMP='0'
GROUP BY KOD_ID,PARTNER,BALENIE HAVING COUNT(*)>1;

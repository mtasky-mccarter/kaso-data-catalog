-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One active packaging row
-- Fan-out: Anti-join avoids multiplying packaging rows.
-- Proves: Missing exact active piece-level code candidate.
-- Does not prove: Universal business error or remediation; scope by product use.
-- Evidence: LM-03C
SELECT lb.RID,lb.KOD_ID,lb.EAN,lb.FLAGS_B
FROM MC.SKLAD_KARTA_LB lb
WHERE lb.S_STAMP='0'
 AND NOT EXISTS (SELECT 1 FROM MC.B_KOD_U b
 WHERE b.RID_SKLAD_KARTA_LB=lb.RID AND b.S_STAMP='0' AND b.BAL=0 AND b.SKRATKA=lb.EAN);

-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One nonzero NAHRADA member
-- Fan-out: Anchor repeated across members; no merging.
-- Proves: Technical self-anchor membership only.
-- Does not prove: Physical/commercial substitutability, exact runtime business use, automatic remediation.
-- Evidence: PM-10F
SELECT a.ID AS ANCHOR_ID,a.INT_KOD AS ANCHOR_CODE,m.ID AS MEMBER_ID,m.INT_KOD,m.USED,m.STAV,
 CASE WHEN m.ID=m.NAHRADA THEN 'SELF_ANCHOR' ELSE 'MEMBER' END AS TECHNICAL_ROLE
FROM MC.SKLAD_KARTA m LEFT JOIN MC.SKLAD_KARTA a ON a.ID=m.NAHRADA
WHERE m.NAHRADA<>0 AND (:anchor_id IS NULL OR m.NAHRADA=:anchor_id);

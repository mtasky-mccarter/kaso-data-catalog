-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One card and referenced state
-- Fan-out: Target PK limits fan-out; do not filter lookup S_STAMP silently.
-- Proves: Current state dictionary resolution.
-- Does not prove: Lookup lifecycle alone does not invalidate an existing reference.
-- Evidence: MP01-B, MP02-J
SELECT sk.ID,sk.INT_KOD,sk.STAV,s.NAZOV AS STAV_NAZOV
FROM MC.SKLAD_KARTA sk LEFT JOIN MC.STAVY_SK s ON s.ID=sk.STAV
WHERE sk.ID=:id;

-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One excluded current card
-- Fan-out: None
-- Proves: Current FLAGS[12] reporting exclusion.
-- Does not prove: Private-label/cofilling cannot be inferred from name; coefficients may validly exist; no full flag history.
-- Evidence: PM-09E
SELECT ID,INT_KOD,NAZOV,SUBSTR(FLAGS,12,1) AS FLAG12,USED,STAV
FROM MC.SKLAD_KARTA WHERE SUBSTR(FLAGS,12,1)='1';

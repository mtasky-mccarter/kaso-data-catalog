-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One coefficient
-- Fan-out: None
-- Proves: Legacy SK/CZ name prefixes alongside applicability mask.
-- Does not prove: No jurisdiction classification from name; reporting context remains downstream.
-- Evidence: PM-04C
SELECT ID,NAZOV,TYP_KRAJINY,ZARADENIE,TYP_UPL,S_STAMP
FROM MC.NAKL_KOEF WHERE SUBSTR(NAZOV,1,2) IN ('SK','CZ');

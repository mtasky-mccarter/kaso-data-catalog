-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One card
-- Fan-out: None
-- Proves: Independent USED and STAV plus technical stamps.
-- Does not prove: USED=1 is not in sale; N_STAMP not creation; no full history.
-- Evidence: MP02-B, MP03-A
SELECT ID,INT_KOD,USED,STAV,S_STAMP,I_STAMP,U_STAMP,N_STAMP
FROM MC.SKLAD_KARTA WHERE ID=:id;

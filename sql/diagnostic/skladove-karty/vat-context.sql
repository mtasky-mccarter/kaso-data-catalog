-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: Card x matching active warehouse override
-- Fan-out: Expose duplicates; no ROWNUM=1.
-- Proves: Root and contextual VAT values.
-- Does not prove: Root VAT is not universal; does not execute session-dependent API resolution.
-- Evidence: PM-05F
SELECT sk.ID,sk.INT_KOD,sk.UROVEN_DPH AS ROOT_UROVEN_DPH,
 fu.ID AS FU_ID,fu.SKLAD_P,fu.UROVEN_DPH AS LOCAL_UROVEN_DPH,fu.S_STAMP
FROM MC.SKLAD_KARTA sk LEFT JOIN MC.SKLAD_KARTA_FU fu
 ON fu.KOD_ID=sk.ID AND fu.SKLAD_P=:sklad_p AND fu.S_STAMP='0'
WHERE sk.ID=:id;

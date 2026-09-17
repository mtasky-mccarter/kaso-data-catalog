-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: Card x packaging x code
-- Fan-out: 1:N:N; do not sum root/packaging measures after joining codes.
-- Proves: Current packaging hierarchy and level-associated codes.
-- Does not prove: Root logistics fields are not universal roll-up; missing packaging not universally an error.
-- Evidence: LM-02A, LM-02E
SELECT sk.ID,sk.INT_KOD,lb.RID AS LB_RID,lb.S_STAMP AS LB_S_STAMP,
 lb.FLAGS_B AS LB_FLAGS_B,lb.EAN,lb.EAN_SBK,lb.EAN_KART,lb.EAN_ROW,lb.EAN_PAL,
 b.RID AS CODE_RID,b.SKRATKA,b.BAL,b.S_STAMP AS CODE_S_STAMP,b.FLAGS_B AS CODE_FLAGS_B
FROM MC.SKLAD_KARTA sk
LEFT JOIN MC.SKLAD_KARTA_LB lb ON lb.KOD_ID=sk.ID
LEFT JOIN MC.B_KOD_U b ON b.RID_SKLAD_KARTA_LB=lb.RID
WHERE sk.ID=:id;

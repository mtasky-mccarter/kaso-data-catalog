-- Supplier PO -> PL lines
-- Grain: One PO line and each linked PL line
-- Proves: Current PO to all linked PL lines
-- Does not prove: P_PL as physical receipt or historical completeness
-- Fan-out: 1:N; PO quantities repeat on each PL match, never sum repeated PO quantities.
-- MC only; SQL Navigator 5.5.4.847; Oracle version unknown.
SELECT PO.RID_O AS po_rid, PO.ID_R AS po_line, PO.P_PL,
       PL.RID_O AS pl_rid, PL.ID_R AS pl_line,
       PL.POCET, PL.P_DEL, PL.P_PRIJ, PL.P_PL AS pl_p_pl,
       PL.POCET - PL.P_DEL - PL.P_PRIJ - PL.P_PL AS pl_remaining,
       MC.D_OBJD_L.GetS_STAV(PH.FLAGS_S) AS po_state,
       MC.D_OBJD_L.GetS_STAV(LH.FLAGS_S) AS pl_state
FROM MC.OBJD_O PO
JOIN MC.OBJD_L PH ON PH.RID = PO.RID_O AND PH.TYP_CIS = '00028'
LEFT JOIN (MC.OBJD_O PL JOIN MC.OBJD_L LH ON LH.RID = PL.RID_O AND LH.TYP_CIS = '00029')
  ON PL.RID_V = PO.RID_O || '!' || TO_CHAR(PO.ID_R)
WHERE PO.RID_O = :p_po_rid;

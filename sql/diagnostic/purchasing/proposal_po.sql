-- Návrh -> supplier PO line
-- Grain: One proposal and its current matching PO line
-- Proves: Current forward line reference
-- Does not prove: Complete historical proposal retention or header RID equivalence
-- Fan-out: Unique target line PK; do not infer global reverse 1:1.
-- MC only; SQL Navigator 5.5.4.847; Oracle version unknown.
SELECT N.RID AS proposal_rid, N.RID_V_OBJ_D, N.STAV AS proposal_state,
       L.RID AS po_rid, L.TYP_CIS, O.ID_R,
       MC.D_OBJD_L.GetS_STAV(L.FLAGS_S) AS fulfilment_state
FROM MC.OBJ_D_NAVRH N
LEFT JOIN (MC.OBJD_O O JOIN MC.OBJD_L L ON L.RID = O.RID_O AND L.TYP_CIS = '00028')
  ON N.RID_V_OBJ_D = O.RID_O || '!' || TO_CHAR(O.ID_R)
WHERE N.RID = :p_proposal_rid;

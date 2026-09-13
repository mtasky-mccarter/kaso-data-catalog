-- PL s otvoreným množstvom
-- Grain: One PL line with positive remainder
-- Proves: Positive line remainder plus current canonical fulfilment state
-- Does not prove: S_STAMP as business status, physical receipt from header state, all runtime finalisation branches
-- Fan-out: No receipt fan-out.
-- MC only; SQL Navigator 5.5.4.847; Oracle version unknown.
SELECT L.RID, L.TYP_CIS, L.STAV AS raw_document_state,
       MC.D_OBJD_L.GetS_STAV(L.FLAGS_S) AS fulfilment_state,
       O.ID_R, O.POCET, O.P_DEL, O.P_PRIJ, O.P_PL,
       O.POCET - O.P_DEL - O.P_PRIJ - O.P_PL AS remaining_qty,
       O.P_DEL + O.P_PRIJ + O.P_PL AS processed_qty,
       NVL(O.TERMIN_DOD, NVL(L.TERMIN_DOD, L.DATUM_P)) AS effective_delivery_date
FROM MC.OBJD_L L
JOIN MC.OBJD_O O ON O.RID_O = L.RID
WHERE L.TYP_CIS = '00029'
  AND L.S_STAMP = '0'
  AND O.POCET - O.P_DEL - O.P_PRIJ - O.P_PL > 0;

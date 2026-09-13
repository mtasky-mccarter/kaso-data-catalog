-- Uložené P_PRIJ vs current surviving lineage
-- Grain: One PL line
-- Proves: Stored P_PRIJ alongside surviving row count and net source quantity
-- Does not prove: Full event reconstruction or corruption; no link remains NULL, not a fabricated zero
-- Fan-out: Receipt rows aggregated before join.
-- MC only; SQL Navigator 5.5.4.847; Oracle version unknown.
SELECT O.RID_O, O.ID_R, O.P_PRIJ AS stored_p_prij,
       R.receipt_link_count, R.current_line_net_qty,
       O.P_PRIJ - R.current_line_net_qty AS difference_to_current_line_net
FROM MC.OBJD_O O
JOIN MC.OBJD_L L ON L.RID = O.RID_O AND L.TYP_CIS = '00029'
LEFT JOIN (SELECT R.RID_V, COUNT(*) AS receipt_link_count,
            SUM(R.POCET - R.P_DEL) AS current_line_net_qty
     FROM MC.PRIJEMKY_OBSAH R
     GROUP BY R.RID_V) R
  ON R.RID_V = O.RID_O || '!' || TO_CHAR(O.ID_R)
WHERE L.RID = :p_pl_rid;

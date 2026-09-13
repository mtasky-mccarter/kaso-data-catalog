-- PL -> current receipt lineage
-- Grain: One PL line
-- Proves: Count and net source quantities of surviving linked receipt rows
-- Does not prove: Physical receipt completion; current net source sum is not historical P_PRIJ authority
-- Fan-out: Receipt rows aggregated by RID_V before joining PL.
-- MC only; SQL Navigator 5.5.4.847; Oracle version unknown.
SELECT O.RID_O, O.ID_R, O.P_PRIJ,
       R.receipt_link_count, R.current_line_net_qty
FROM MC.OBJD_O O
JOIN MC.OBJD_L L ON L.RID = O.RID_O AND L.TYP_CIS = '00029'
LEFT JOIN (SELECT R.RID_V, COUNT(*) AS receipt_link_count,
            SUM(R.POCET - R.P_DEL) AS current_line_net_qty
     FROM MC.PRIJEMKY_OBSAH R
     GROUP BY R.RID_V) R
  ON R.RID_V = O.RID_O || '!' || TO_CHAR(O.ID_R)
WHERE O.RID_O = :p_pl_rid;

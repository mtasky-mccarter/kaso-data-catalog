WITH r AS (
  SELECT rid, id_r,
         SUM(p_vrat) AS return_link_qty,
         COUNT(*) AS return_link_count
  FROM mc.vyd_o_p_prij
  GROUP BY rid, id_r
)
SELECT o.rid_o, o.id_r, o.kod_id, o.p_prij,
       NVL(r.return_link_qty,0) AS helper_return_qty,
       NVL(r.return_link_count,0) AS helper_link_count
FROM mc.vyd_o o
LEFT JOIN r ON r.rid=o.rid_o AND r.id_r=o.id_r
WHERE o.rid_o=:issue_rid
ORDER BY o.id_r;

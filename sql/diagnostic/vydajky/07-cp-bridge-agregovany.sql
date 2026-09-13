WITH cp AS (
  SELECT rid_v,
         COUNT(*) AS cp_row_count,
         COUNT(DISTINCT rid_o) AS cp_count
  FROM mc.cestovne_pr_o
  GROUP BY rid_v
)
SELECT l.rid, l.datum_p, l.doprava,
       cp.cp_row_count, cp.cp_count
FROM mc.vyd_l l
LEFT JOIN cp ON cp.rid_v=l.rid
WHERE l.rid=:issue_rid;

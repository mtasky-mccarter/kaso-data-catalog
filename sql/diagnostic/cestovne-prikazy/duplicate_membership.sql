SELECT rid_o, rid_v, COUNT(*) AS rows_per_pair,
       SUM(CASE WHEN stav=5 THEN 1 ELSE 0 END) AS cancelled_rows
FROM mc.cestovne_pr_o
GROUP BY rid_o, rid_v
HAVING COUNT(*) > 1
ORDER BY rows_per_pair DESC, rid_o, rid_v;

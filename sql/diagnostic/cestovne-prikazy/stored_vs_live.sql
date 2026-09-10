WITH a AS (
  SELECT rid_o, COUNT(*) AS cnt FROM mc.cestovne_pr_o WHERE stav <> 5 GROUP BY rid_o
), r AS (
  SELECT o.rid_o, ROUND(NVL(SUM(q.objem_d),0),2) AS objem_calc,
         ROUND(NVL(SUM(q.hmotnost_d),0),2) AS hmotnost_calc,
         ROUND(NVL(SUM(q.pocet_pal),0),2) AS pal_calc
  FROM mc.cestovne_pr_o o JOIN mc.rozvoz_que q ON q.rid_v=o.rid_v
  WHERE o.stav <> 5 GROUP BY o.rid_o
)
SELECT l.rid, l.pocet_dokl, NVL(a.cnt,0) AS pocet_dokl_calc,
       l.objem, NVL(r.objem_calc,0) AS objem_calc,
       l.hmotnost, NVL(r.hmotnost_calc,0) AS hmotnost_calc,
       l.pocet_pal, NVL(r.pal_calc,0) AS pocet_pal_calc
FROM mc.cestovne_pr_l l
LEFT JOIN a ON a.rid_o=l.rid
LEFT JOIN r ON r.rid_o=l.rid
WHERE l.rid=:cp_rid;

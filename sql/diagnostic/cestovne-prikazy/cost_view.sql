SELECT l.rid, l.nakl_p, l.nakl_s, l.typ_rozp_nakl,
       o.rid_r, o.rid_v, o.stav, o.nakl
FROM mc.cestovne_pr_l l
LEFT JOIN mc.cestovne_pr_o o ON o.rid_o=l.rid
WHERE l.rid=:cp_rid
ORDER BY o.rid_r;

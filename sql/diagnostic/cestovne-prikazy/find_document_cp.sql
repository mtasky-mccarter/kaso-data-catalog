SELECT o.rid_r, o.rid_o AS cp_rid, l.skratka,
       l.stav AS cp_state, o.stav AS bridge_state, o.id_r_v, o.vybavene
FROM mc.cestovne_pr_o o
JOIN mc.cestovne_pr_l l ON l.rid=o.rid_o
WHERE o.rid_v=:document_rid
ORDER BY l.datum DESC, o.rid_r;

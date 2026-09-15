SELECT o.rid_o,       o.id_r,       o.kod_id,       v.rid_o AS issue_id,       v.id_r  AS issue_line_id,       v.pocet,       v.p_del,       v.p_vyskl
FROM mc.obj_odb_o o
LEFT JOIN mc.vyd_o v  ON v.rid_v = o.rid_o || '!' || TO_CHAR(o.id_r) AND v.kod_id <> 204
WHERE o.rid_o = :rid_o
ORDER BY o.id_r, v.rid_o, v.id_r;

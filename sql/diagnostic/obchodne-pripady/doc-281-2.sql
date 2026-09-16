SELECT COUNT(*) AS line_count,       SUM(o.pocet) AS ordered_qty,       SUM(o.pocet-o.p_del-o.p_del_dod-o.p_fak-o.p_vyd-o.p_obj) AS open_qty,       SUM(o.p_rez) AS reserved_qty,       SUM(o.p_fak) AS invoiced_qty,       SUM(o.p_vyd) AS issued_qty
FROM mc.obj_odb_o o
WHERE o.rid_o=:rid;

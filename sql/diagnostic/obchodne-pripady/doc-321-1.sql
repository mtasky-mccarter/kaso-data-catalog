SELECT o.rid_o,       o.id_r,       COUNT(*) AS joined_rows
FROM mc.obj_odb_o o
LEFT JOIN mc.dovod_zrus_pol_doklad d  ON d.rid_o = o.rid_o AND d.id_r  = o.id_r
WHERE o.rid_o = :rid_o
GROUP BY o.rid_o, o.id_r
HAVING COUNT(*) > 1;

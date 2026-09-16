SELECT o.rid_o,o.id_r,o.kod_id,o.pocet,o.p_del,o.p_del_dod,d.*
FROM mc.obj_odb_o o
LEFT JOIN mc.dovod_zrus_pol_doklad d  ON d.rid_o=o.rid_o AND d.id_r=o.id_r
WHERE o.rid_o=:rid_o
ORDER BY o.id_r;

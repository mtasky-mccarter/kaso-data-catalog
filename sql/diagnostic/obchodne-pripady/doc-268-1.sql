SELECT o.rid_o,o.id_r,o.kod_id,o.pocet,       o.p_del,o.p_del_dod,o.p_fak,o.p_vyd,o.p_obj,       o.pocet-o.p_del-o.p_del_dod-o.p_fak-o.p_vyd-o.p_obj AS open_qty,       o.cena,o.cena_m,o.dph
FROM mc.obj_odb_o o
WHERE o.rid_o=:rid_o AND o.id_r=:id_r;

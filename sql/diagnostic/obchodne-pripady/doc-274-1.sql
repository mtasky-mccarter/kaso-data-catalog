SELECT o.rid_o,o.id_r,o.kod_id,o.pocet,       o.p_rez,o.p_rez_is,o.p_rez_pl,o.p_obj_d,o.p_dispo,o.p_vykr,       o.p_del,o.p_del_dod,o.p_fak,o.p_vyd,o.p_obj,       o.rid_n,o.rid_v,o.sposob_vybavenia
FROM mc.obj_odb_o o
WHERE o.rid_o=:rid_o AND o.id_r=:id_r;

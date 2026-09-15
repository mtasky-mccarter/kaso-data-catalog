SELECT rid_o,id_r,kod_id,       pocet-p_del-p_del_dod-p_fak-p_vyd-p_obj AS open_qty,       p_rez+p_rez_is+p_rez_pl+p_obj_d+p_dispo+p_vykr AS coverage_qty
FROM mc.obj_odb_o
WHERE rid_o=:rid_o  AND (p_rez+p_rez_is+p_rez_pl+p_obj_d+p_dispo+p_vykr) >      (pocet-p_del-p_del_dod-p_fak-p_vyd-p_obj);

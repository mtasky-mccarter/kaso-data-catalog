SELECT l.rid, l.typ_cis, l.flags_s, l.flags_b,       o.id_r, o.pocet, o.p_rez, o.p_rez_is, o.p_rez_pl,       o.p_obj_d, o.p_dispo, o.p_vykr, o.p_del, o.p_del_dod,       o.p_fak, o.p_vyd, o.p_obj, o.rid_v
FROM mc.obj_odb_l l
JOIN mc.obj_odb_o o ON o.rid_o=l.rid
WHERE l.rid=:rid AND o.id_r=:id_r;

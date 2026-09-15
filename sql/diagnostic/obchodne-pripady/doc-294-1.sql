SELECT l.rid, l.id, l.ext_dokument, l.typ_cis, l.partner,       l.miesto_dod, l.sklad, l.datum_p, l.flags_s, l.flags_b,       o.id_r, o.kod_id, o.id_sz, o.pocet, o.p_rez,       o.p_del, o.p_del_dod, o.p_fak, o.p_vyd, o.p_obj
FROM mc.obj_odb_l l
JOIN mc.obj_odb_o o ON o.rid_o=l.rid
WHERE l.rid=:rid
ORDER BY o.id_r;

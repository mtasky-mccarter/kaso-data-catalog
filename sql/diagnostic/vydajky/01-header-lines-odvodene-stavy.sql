SELECT l.rid, l.id, l.sklad, l.typ_cis, l.datum, l.datum_p,
       l.partner, l.miesto_dod, l.doprava, l.rid_v,
       d_vydaj_l.GetS_STAV(l.flags_s)   AS issue_state_code,
       d_vydaj_l.GetS_STAV_V(l.flags_s) AS warehouse_state_code,
       o.id_r, o.kod_id, o.id_sz, o.pocet, o.p_del,
       o.p_vyskl, o.p_prij, o.p_rez, o.sarza, o.datum_exp,
       o.rid_v AS source_line_ref, o.rid_r_dlaf
FROM mc.vyd_l l
JOIN mc.vyd_o o ON o.rid_o = l.rid
WHERE l.rid = :rid
ORDER BY o.id_r;

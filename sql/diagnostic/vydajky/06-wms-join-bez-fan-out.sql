SELECT l.rid, l.sklad, l.datum_p,
       d_vydaj_l.GetS_STAV_V(l.flags_s) AS warehouse_state_code,
       w.*
FROM mc.vyd_l l
LEFT JOIN mc.wms_que w ON w.rid_d=l.rid
WHERE l.rid=:issue_rid;

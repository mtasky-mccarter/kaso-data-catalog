SELECT l.rid, l.stav AS cp_state,
       d_cpr_l.GetStavCPZlozExt(l.stav,l.flags_b) AS effective_state, w.*
FROM mc.cestovne_pr_l l
LEFT JOIN mc.wms_que w ON w.rid_d=l.rid
WHERE l.rid=:cp_rid;

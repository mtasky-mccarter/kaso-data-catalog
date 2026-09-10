SELECT l.rid, l.skratka, l.datum, l.datum_s,
       l.stav AS raw_state,
       d_cpr_l.GetStavCPZlozExt(l.stav,l.flags_b) AS effective_state,
       l.uzavrel_stamp, l.odchod_stamp, l.prichod_stamp,
       l.vybavil_stamp, l.s_stamp,
       l.doprava, l.auto, l.vodic, l.rid_cp_zluc
FROM mc.cestovne_pr_l l
WHERE l.rid = :cp_rid;

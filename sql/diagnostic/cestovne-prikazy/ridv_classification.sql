SELECT o.rid_r, o.rid_v, o.stav,
       CASE WHEN v.rid IS NOT NULL THEN 'VYD_L'
            WHEN p.rid IS NOT NULL THEN 'PRIJEMKY_LIST'
            WHEN d.rid IS NOT NULL THEN 'DOCASNY_ROZVOZ'
            WHEN f.rid IS NOT NULL THEN 'DLAF_L'
            ELSE 'UNRESOLVED' END AS target_type
FROM mc.cestovne_pr_o o
LEFT JOIN mc.vyd_l v ON v.rid=o.rid_v
LEFT JOIN mc.prijemky_list p ON p.rid=o.rid_v
LEFT JOIN mc.docasny_rozvoz d ON d.rid=o.rid_v
LEFT JOIN mc.dlaf_l f ON f.rid=o.rid_v
WHERE o.rid_o=:cp_rid;

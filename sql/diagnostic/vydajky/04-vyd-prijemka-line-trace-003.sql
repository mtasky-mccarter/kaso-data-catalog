SELECT v.rid_o AS issue_id, v.id_r AS issue_line_id,
       v.kod_id, v.rid_v,
       p.rid_r AS receipt_line_id,
       p.rid_o AS receipt_id
FROM mc.vyd_o v
LEFT JOIN mc.prijemky_obsah p
  ON p.rid_r = v.rid_v
WHERE SUBSTR(v.rid_v,1,3) = '003'
  AND v.rid_o = :issue_rid;

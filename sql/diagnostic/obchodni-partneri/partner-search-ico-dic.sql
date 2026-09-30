-- Returns ALL current matches; do not add ROWNUM=1. ICO/DIC are not unique identity.
SELECT p.id AS partner_id, p.rid AS partner_rid, p.nazov AS partner_name, p.ico, p.dic, p.dic_new, p.s_stamp
FROM mc.obch_partneri p
WHERE p.s_stamp='0'
  AND (p.ico=:ico OR p.dic=:dic OR p.dic_new=:dic_new)
ORDER BY p.id;

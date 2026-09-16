SELECT o.rid_o,o.id_r,o.kod_id,k.*
FROM mc.obj_odb_o o
LEFT JOIN mc.sklad_karta k ON k.id=o.kod_id
WHERE o.rid_o=:rid_o;

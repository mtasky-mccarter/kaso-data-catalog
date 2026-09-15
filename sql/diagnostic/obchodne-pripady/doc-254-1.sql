SELECT o.rid_o,o.id_r,o.kod_id,o.dph,       o.cena,o.cena_m,o.cena_s,o.cena_s2,       o.rid_ct_z,o.rid_ct_a,o.zlavy,o.flags_b,o.xml_data
FROM mc.obj_odb_o o
WHERE o.rid_o=:rid_o AND o.id_r=:id_r;

SELECT o.rid_o,o.id_r,o.kod_id,o.cena,o.cena_m,o.rid_ct_z,o.rid_ct_a,       ctz.rid_obj AS contract_ref_found,       cta.rid_obj AS action_ref_found,       cta.pocet_bl_plan, cta.pocet_bl_st, cta.pocet_bl_ok
FROM mc.obj_odb_o o
LEFT JOIN mc.ct_o ctz ON ctz.rid_obj=o.rid_ct_z
LEFT JOIN mc.ct_o cta ON cta.rid_obj=o.rid_ct_a
WHERE o.rid_o=:rid_o AND o.id_r=:id_r;

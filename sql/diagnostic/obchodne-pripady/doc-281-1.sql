SELECT l.rid,l.id,l.ext_dokument,l.typ_cis,l.flags_s,l.flags_b,       l.datum,l.datum_p,l.datum_ok,l.i_stamp,l.obsluha
FROM mc.obj_odb_l l
WHERE l.rid=:rid;

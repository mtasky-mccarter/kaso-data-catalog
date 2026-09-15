SELECT l.rid,l.id,l.ext_dokument,v.*
FROM mc.obj_odb_l l
LEFT JOIN mc.vyd_l v ON v.rid_v=l.rid
WHERE l.rid=:rid;

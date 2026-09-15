SELECT d.*
FROM mc.dovod_zrus_pol_doklad d
WHERE d.rid_o=:rid_o AND d.id_r=:id_r
ORDER BY d.s_stamp, d.i_stamp;

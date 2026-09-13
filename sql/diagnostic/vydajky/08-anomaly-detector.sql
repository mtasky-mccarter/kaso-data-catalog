SELECT rid_o, id_r, kod_id, pocet, p_del, p_vyskl, p_prij, p_rez
FROM mc.vyd_o
WHERE pocet < 0
   OR p_del < 0
   OR p_vyskl < 0
   OR p_prij < 0
   OR p_del > pocet
   OR p_del + p_vyskl > pocet
   OR (kod_id <> 204 AND p_prij > p_vyskl)
   OR p_rez <> 0;

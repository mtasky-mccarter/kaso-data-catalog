SELECT rid_o, id_r, kod_id, id_sz,
       pocet, p_del, p_vyskl, p_prij, p_rez,
       pocet-p_del AS net_issue_qty,
       pocet-p_del-p_vyskl AS remaining_to_pick_qty,
       p_vyskl-p_prij AS issued_not_returned_qty
FROM mc.vyd_o
WHERE rid_o = :rid
ORDER BY id_r;

SELECT o.rid_r, o.rid_o, o.rid_v, o.stav,
       o.id_r_v, o.vybavene, o.poradie, o.poradie_2,
       o.nakl, o.stav_fin_vysp
FROM mc.cestovne_pr_o o
WHERE o.rid_o = :cp_rid
ORDER BY o.rid_r;

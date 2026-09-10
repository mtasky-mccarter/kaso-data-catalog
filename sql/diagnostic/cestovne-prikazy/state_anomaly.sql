SELECT l.rid, l.stav AS header_state, o.rid_r, o.rid_v, o.stav AS bridge_state
FROM mc.cestovne_pr_l l
JOIN mc.cestovne_pr_o o ON o.rid_o=l.rid
WHERE (l.stav IN (0,1,2,4) AND o.stav NOT IN (l.stav,5))
   OR (l.stav=3 AND o.stav NOT IN (3,5))
   OR (l.stav=5 AND o.stav<>5);

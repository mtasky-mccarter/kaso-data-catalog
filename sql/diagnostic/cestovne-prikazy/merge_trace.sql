SELECT old.rid AS old_cp, old.skratka AS old_display, old.rid_cp_zluc AS merged_into_cp,
       new.skratka AS new_display, old.stav AS old_state, new.stav AS new_state
FROM mc.cestovne_pr_l old
LEFT JOIN mc.cestovne_pr_l new ON new.rid=old.rid_cp_zluc
WHERE old.rid=:cp_rid OR old.rid_cp_zluc=:cp_rid;

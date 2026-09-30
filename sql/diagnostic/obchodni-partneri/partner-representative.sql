-- Grain: one partner row. ZASTUPCA is partner-level representative, not delivery-place dealer.
SELECT p.id AS partner_id, p.nazov AS partner_name, p.zastupca AS rep_user_id,
 u.meno AS rep_first_name, u.priezvisko AS rep_last_name, u.titul AS rep_title,
 u.funkcia AS rep_function, u.el_mail AS rep_email, u.tel_mb AS rep_mobile, u.s_stamp AS rep_user_s_stamp
FROM mc.obch_partneri p
LEFT JOIN mc.b_users u ON u.id=p.zastupca
WHERE p.id=:partner_id;

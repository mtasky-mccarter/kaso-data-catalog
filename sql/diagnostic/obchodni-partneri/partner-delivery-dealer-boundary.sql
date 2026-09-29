-- BOUNDARY helper only. Grain: one partner x current delivery place.
-- Full MIESTA_DODANIA semantics belong to its separate master mapping.
SELECT p.id AS partner_id, p.nazov AS partner_name, md.rid AS delivery_place_rid, md.nazov AS delivery_place_name,
 md.dealer AS dealer_user_id, u.meno AS dealer_first_name, u.priezvisko AS dealer_last_name,
 u.funkcia AS dealer_function, u.el_mail AS dealer_email, u.s_stamp AS dealer_user_s_stamp
FROM mc.obch_partneri p
JOIN mc.miesta_dodania md ON md.id_partner=p.id AND md.s_stamp='0'
LEFT JOIN mc.b_users u ON u.id=md.dealer
WHERE p.id=:partner_id
ORDER BY md.rid;

-- S_STAMP, STAV and TYP_CIS are separate axes.
SELECT p.id AS partner_id, p.nazov AS partner_name, p.s_stamp AS partner_s_stamp,
 p.stav AS partner_state_id, s.nazov AS partner_state_name,
 p.typ_cis AS partner_type_id, t.nazov_zoznam AS partner_type_name
FROM mc.obch_partneri p
LEFT JOIN mc.stavy_op s ON s.id=p.stav
LEFT JOIN mc.typy_cis t ON t.id=p.typ_cis
WHERE p.id=:partner_id;

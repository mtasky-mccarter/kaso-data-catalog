-- Grain: one OBCH_PARTNERI row; only 1:1 / identity lookups.
-- Do not add target S_STAMP='0' to JOINs; expose target lifecycle separately.
SELECT
 p.id AS partner_id, p.rid AS partner_rid, p.nazov AS partner_name, p.s_stamp AS partner_s_stamp,
 p.krajina AS country_id, k.nazov AS country_name, k.nazov_m AS country_name_intl,
 k.iso_nkod AS country_iso_num_raw, k.iso_alpha_3 AS country_iso_alpha3, k.s_stamp AS country_s_stamp,
 p.id_mesto AS city_id, m.nazov AS city_name, m.psc AS city_postal_code, m.krajina AS city_country_id,
 mk.nazov AS city_country_name, m.s_stamp AS city_s_stamp,
 p.mena_p AS currency_id, me.skratka AS currency_code, me.nazov AS currency_name_raw, me.s_stamp AS currency_s_stamp,
 p.stav AS partner_state_id, sop.nazov AS partner_state_name, sop.s_stamp AS state_s_stamp,
 p.typ_cis AS partner_type_id, tc.nazov_zoznam AS partner_type_name, tc.s_stamp AS type_s_stamp,
 p.typ_uhrady AS payment_type_id, tu.nazov AS payment_type_name, tu.splatnost AS payment_due_days,
 tu.sposob_uhr AS payment_method_id, ku.nazov AS payment_method_name, tu.s_stamp AS payment_type_s_stamp,
 p.obch_skupina AS business_group_id, pos.nazov AS business_group_name, pos.s_stamp AS business_group_s_stamp,
 p.segment_trhu AS market_segment_rid, seg.nazov AS market_segment_name, seg.s_stamp AS segment_s_stamp,
 p.zlava AS price_list_id, cp.nazov AS price_list_name, cp.s_stamp AS price_list_s_stamp,
 p.sklad AS warehouse_id, bp.nazov AS warehouse_name, bp.s_stamp AS warehouse_s_stamp,
 p.typ_el_kom AS ecomm_format_id, ek.nazov AS ecomm_format_name, ek.s_stamp AS ecomm_format_s_stamp,
 p.zastupca AS rep_user_id, zu.meno AS rep_first_name, zu.priezvisko AS rep_last_name,
 zu.funkcia AS rep_function, zu.el_mail AS rep_email, zu.tel_mb AS rep_mobile, zu.s_stamp AS rep_user_s_stamp,
 p.nakupca AS buyer_id_raw, nu.id AS buyer_user_match_id, nu.meno AS buyer_first_name, nu.priezvisko AS buyer_last_name
FROM mc.obch_partneri p
LEFT JOIN mc.krajiny k ON k.id=p.krajina
LEFT JOIN mc.mesta m ON m.id=p.id_mesto
LEFT JOIN mc.krajiny mk ON mk.id=m.krajina
LEFT JOIN mc.meny me ON me.id=p.mena_p
LEFT JOIN mc.stavy_op sop ON sop.id=p.stav
LEFT JOIN mc.typy_cis tc ON tc.id=p.typ_cis
LEFT JOIN mc.typy_uhrady tu ON tu.id=p.typ_uhrady
LEFT JOIN mc.kasy_sposob_uhrad ku ON ku.id=tu.sposob_uhr
LEFT JOIN mc.partner_os pos ON pos.id=p.obch_skupina
LEFT JOIN mc.segmenty seg ON seg.rid=p.segment_trhu
LEFT JOIN mc.cenniky_popis cp ON cp.id=p.zlava
LEFT JOIN mc.bartex_pobocky bp ON bp.id=p.sklad
LEFT JOIN mc.el_kom_formaty ek ON ek.id=p.typ_el_kom
LEFT JOIN mc.b_users zu ON zu.id=p.zastupca
LEFT JOIN mc.b_users nu ON nu.id=p.nakupca
WHERE p.id = :partner_id;

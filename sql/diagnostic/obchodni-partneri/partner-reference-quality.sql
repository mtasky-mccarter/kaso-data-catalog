-- Grain: one row per relationship quality summary.
SELECT 'KRAJINA' AS rel_name, COUNT(*) AS src_rows, SUM(CASE WHEN k.id IS NULL THEN 1 ELSE 0 END) AS no_match
FROM mc.obch_partneri p LEFT JOIN mc.krajiny k ON k.id=p.krajina
UNION ALL
SELECT 'ID_MESTO', COUNT(*), SUM(CASE WHEN m.id IS NULL THEN 1 ELSE 0 END)
FROM mc.obch_partneri p LEFT JOIN mc.mesta m ON m.id=p.id_mesto
UNION ALL
SELECT 'ZASTUPCA', COUNT(*), SUM(CASE WHEN u.id IS NULL THEN 1 ELSE 0 END)
FROM mc.obch_partneri p LEFT JOIN mc.b_users u ON u.id=p.zastupca
UNION ALL
SELECT 'NAKUPCA_SOFT', COUNT(*), SUM(CASE WHEN p.nakupca<>0 AND u.id IS NULL THEN 1 ELSE 0 END)
FROM mc.obch_partneri p LEFT JOIN mc.b_users u ON u.id=p.nakupca
ORDER BY 1;

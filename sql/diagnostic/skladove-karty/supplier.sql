-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: Card x supplier row
-- Fan-out: 1:N; preserve ID_DODAVATELA and lifecycle.
-- Proves: Root versus supplier satellite values.
-- Does not prove: DOD_KOD/KOD_DOD/VYROBCA_KOD equivalence or continuous synchronization.
-- Evidence: PM-05E
SELECT sk.ID,sk.INT_KOD,sk.DOD_SK,sk.DOD_KOD,
 d.ID AS SUPPLIER_ROW,d.ID_DODAVATELA,d.KOD_DOD,d.VYROBCA_KOD,d.S_STAMP
FROM MC.SKLAD_KARTA sk LEFT JOIN MC.SKLAD_DODAVATEL d ON d.KOD_ID=sk.ID
WHERE sk.ID=:id;

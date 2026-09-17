-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One active product-context typed note
-- Fan-out: 1:N root-to-note; no root sums.
-- Proves: Current operational typed-note values and dictionary meaning.
-- Does not prove: Not every note is allergen; not full historical or downstream manufacturing truth.
-- Evidence: PM-08E, PM-09B
SELECT sk.ID,sk.INT_KOD,n.ID AS NOTE_ID,n.TYP,t.NAZOV AS NOTE_TYPE,
 n.POZNAMKA,n.S_STAMP,n.ZOBRAZIT_OD,n.ZOBRAZIT_DO
FROM MC.SKLAD_KARTA sk JOIN MC.CIS_POZNAMKY n ON n.RID_V=sk.RID
LEFT JOIN MC.CIS_POZNAMKY_TYPY t ON t.ID=n.TYP
WHERE sk.ID=:id AND n.S_STAMP='0';

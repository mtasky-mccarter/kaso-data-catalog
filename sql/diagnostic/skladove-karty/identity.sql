-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One root card
-- Fan-out: No joins; multiple identifiers may select different cards.
-- Proves: Current identity matches.
-- Does not prove: Historical/global uniqueness; INT_KOD is text, not numeric.
-- Evidence: MP01-A, MP02-A
SELECT ID, SK_ID, RID, RID_OBJ, INT_KOD, SKLAD
FROM MC.SKLAD_KARTA
WHERE (:id IS NOT NULL AND ID=:id)
   OR (:sk_id IS NOT NULL AND SK_ID=:sk_id)
   OR (:rid IS NOT NULL AND RID=:rid)
   OR (:int_kod IS NOT NULL AND INT_KOD=:int_kod);

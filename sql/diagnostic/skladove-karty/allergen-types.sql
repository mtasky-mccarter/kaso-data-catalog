-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One selected active allergen note
-- Fan-out: Multiple notes per card/type remain visible.
-- Proves: Separate caller-selected dictionary types.
-- Does not prove: Caller must select approved dictionary types; 00048/00052 relation unresolved; no free-text inference.
-- Evidence: PM-09B
SELECT sk.ID,sk.INT_KOD,n.ID AS NOTE_ID,n.TYP,t.NAZOV,
 CASE WHEN n.TYP=:direct_type THEN 'DIRECT'
      WHEN n.TYP=:cross_type THEN 'CROSS_CONTAMINATION' END AS SELECTED_CONTEXT
FROM MC.SKLAD_KARTA sk JOIN MC.CIS_POZNAMKY n ON n.RID_V=sk.RID
JOIN MC.CIS_POZNAMKY_TYPY t ON t.ID=n.TYP
WHERE sk.ID=:id AND n.S_STAMP='0' AND n.TYP IN (:direct_type,:cross_type)
 AND :direct_type<>:cross_type;

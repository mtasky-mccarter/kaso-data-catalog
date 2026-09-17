-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One current unresolved card
-- Fan-out: None
-- Proves: Current unresolved value population.
-- Does not prove: No guessed meaning, dictionary join or cleanup rule.
-- Evidence: PM-10B2
SELECT ID,INT_KOD,TYP_T,T_TOVARU,USED,STAV FROM MC.SKLAD_KARTA WHERE TYP_T='00';

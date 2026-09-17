-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One visible compile-time dependency
-- Fan-out: Multiple types per object possible.
-- Proves: Visible static dependency surface.
-- Does not prove: Reader/writer/caller role, external runtime completeness or absence.
-- Evidence: MP01-G, MP04-A
SELECT OWNER,NAME,TYPE,REFERENCED_OWNER,REFERENCED_NAME,REFERENCED_TYPE
FROM ALL_DEPENDENCIES
WHERE REFERENCED_OWNER='MC' AND REFERENCED_NAME IN ('SKLAD_KARTA','C_SKLAD_KARTA');

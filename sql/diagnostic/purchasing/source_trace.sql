-- MC dependency/source trace
-- Grain: One dictionary dependency or source line
-- Proves: Oracle-visible compile dependency or source text
-- Does not prove: Writer/reader role from dependency alone; external jobs or dynamic runtime absence
-- Fan-out: Independent result sets; no business quantity aggregation.
-- MC only; SQL Navigator 5.5.4.847; Oracle version unknown.
SELECT D.OWNER, D.NAME, D.TYPE, D.REFERENCED_OWNER,
       D.REFERENCED_NAME, D.REFERENCED_TYPE, D.DEPENDENCY_TYPE
FROM ALL_DEPENDENCIES D
WHERE D.OWNER = 'MC'
  AND D.REFERENCED_OWNER = 'MC'
  AND D.REFERENCED_NAME IN ('OBJD_L','OBJD_O','OBJ_D_NAVRH',
      'D_OBJD_L','D_OBJD_O','C_OBJ_D_KOMBAJN','C_REZ_OBJ_DOD');

SELECT S.OWNER, S.NAME, S.TYPE, S.LINE, S.TEXT
FROM ALL_SOURCE S
WHERE S.OWNER = 'MC'
  AND S.NAME = :p_source_name
ORDER BY S.TYPE, S.LINE;

-- Scope: MC / OWNER=MC; SQL Navigator 5.5.4.847; Oracle version unknown
-- Grain: One source line
-- Fan-out: No data joins
-- Proves: Source-visible POZN marker exception and ordinary BITAND(STAV,2)=2 guard; replication condition.
-- Does not prove: Executing or globally bypassing locks. Package line window is dated PM-12A locator and may move after DDL.
-- Evidence: PM-12A
SELECT s.OWNER,s.NAME,s.TYPE,s.LINE,s.TEXT
FROM ALL_SOURCE s
WHERE s.OWNER='MC' AND
 ((s.NAME IN ('T_SKLAD_KARTA_STAV_AFTER_MC','T_OBCH_PL_LOCK_MC') AND s.TYPE='TRIGGER')
 OR (s.NAME='MCCARTER_PLAN' AND s.TYPE='PACKAGE BODY' AND s.LINE BETWEEN 1030 AND 1070))
ORDER BY s.NAME,s.TYPE,s.LINE;

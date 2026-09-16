# ODB read-only diagnostics

20 SELECTov zo schváleného v1.2: 9 toolkit SQL vzorov a SQL pre 8 playbookov.
Názvy `doc-<block>-<part>.sql` odkazujú na 0-based intake block a 1-based SELECT.
Prenos opravuje iba chýbajúce whitespace hranice SQL klauzúl; bezpečnostný test
porovnáva všetky ostatné znaky s retained approved extraction.

SQL Navigator 5.5.4.847; Oracle server version unknown. Žiadny SELECT nebol týmto
engineering behom vykonaný na MC. Grain/fan-out a interpretation limits sú
v sql-registry, relationships a playbooks. Coverage sanity nie je ekvivalent
úplného CHECKu s DECODE/negatívnou vetvou. Invoice-line JOIN nie je doplnený.

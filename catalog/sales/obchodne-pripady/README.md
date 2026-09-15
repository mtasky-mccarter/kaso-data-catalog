# Obchodné prípady — Phase A document-backed materialization

Schválený human semantic contract v1.2 bol prenesený do existujúcej schema v1.0.
Autorita prostredia: MC. Maturity: DIAGNOSTIC-GRADE. Publication blocked; closure
nie je exhaustive a nejde o AGENT-READY. Feature branch nie je prijatý main.

Materiál obsahuje 79 L polí, 44 O polí, 50 trigger summaries (17 L / 33 O),
18 skupinových mutation záznamov, 12 relationship záznamov, 33 constraints,
34 indexes, 10 form codes, 16 dokumentových DQ pozorovaní, 8 playbookov a
20 SELECT súborov. CHECK záznamy obsahujú identitu/stav; ich dokumentové popisy
sú v do-not-assume. Prázdny column_refs CHECKu nepreukazuje absenciu stĺpcov.
Úplné výrazy ani chýbajúce názvy 8 O FK sa neodhadujú.

Proveniencia: `evidence/source-extracts/odb/approved-contract.json` je zachovaná
intake extrakcia schváleného DOCX; jeho pôvodný SHA-256 je v accepted manifest.
Extrakcia nie je raw Oracle export. `intake-integrity.json` uchováva výsledok
41 checksum kontrol zo 14. 9. 2026. Pri pokračovaní 15. 9. už pôvodný bundle
nebol na používateľom zadanej ceste; raw XLSX nie sú predstierané ako spracované.

`tools/materialize_odb_phase_a.py` reprodukuje projekciu z checksum-pinned
extrakcie. Nevyvodzuje business význam, nerozbaľuje wildcard writerov a nemení
source NULL na display label. Prázdne DOCX bunky vynecháva, keď nedokazujú NULL.
Zdrojové block čísla sú 0-based indexy zachovanej extrakcie. SQL projekcia pridáva
iba whitespace na hranice klauzúl a rozdeľuje pôvodné SELECTy pri bodkočiarke.

Existujúce VYD boundary IDs sú bez zmeny reconciliované v
`odb.rule.vyd_identity_reconciliation`; nové sales objekty opisujú tie isté
fyzické MC.OBJ_ODB_L/O. Master/VYD field IDs sa používajú, kde už existujú.
Nové external entity records sú iba explicitné field boundaries, bez nového
master business contractu.

Rozdiel oproti VYD/CP: táto fáza má dokumentový dôkaz D, nie predstierané raw
A/B/B2 manifests. Dependency register zachováva dokumentové DML-reference počty ako DEPENDENCY ONLY.
Raw closure/API registre zostávajú nematerializované;
empty register != verified zero. Deväť schválených neblokujúcich gapov zostáva.
Backlog presne oddeľuje chýbajúce raw physical/source/closure claims a publication.

Potrebné vstupy pre ďalší krok: obnovená cesta k pôvodnému bundle/ZIP s
README_HANDOFF.txt a SHA256SUMS.txt; ODB_DIAG a OBJ_ODB_O XLSX; neskôr samostatné
OBJ_H01..H06B. Supporting DOCX zostávajú supporting references.

Overenie: `python tools/validate_catalog.py`, ODB acceptance/SQL safety/publication
fail-closed tests a repository unittest discovery. Testy nie sú Oracle execution
ani dôkaz úplnosti dependency closure. DOCX/PDF sa v tejto fáze nevytvárajú.

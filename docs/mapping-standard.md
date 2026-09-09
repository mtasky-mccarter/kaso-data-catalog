# KASO Data Catalog - Mapping Method & Agent-Ready Standard

## v2.1 - ChatGPT / AI-friendly reference

Tento dokument je zámerne formátovaný jednoducho: bez grafických prvkov, text boxov, log, farebných významov a layoutových závislostí. Primárnym cieľom je presná orientácia ChatGPT, Codexu a ďalších AI nástrojov v pravidlách KASO Data Catalogu. Human-readable DOCX zostáva publikačný výstup; budúci canonical source of truth má byť machine-readable a version-controlled.

## 0. AI QUICK CONTRACT

DOCUMENT_ROLE: Záväzný enterprise pracovný štandard pre mapovanie Oracle databázy BarIS / Dreamer / HandyGO / KASO.

AUTHORITATIVE_PRODUCTION_OWNER: MC - slovenská produkcia.

NON_AUTHORITATIVE_ENVIRONMENTS: MCCZ, TEST, TESTCZ - môžu byť pomocnou stopou, nikdy dôkazom pre MC bez samostatnej validácie.

SQL_CLIENT: SQL Navigator 5.5.4.847.

DATABASE_SERVER_VERSION: NIE JE V TOMTO ŠTANDARDE POTVRDENÁ. AI ju nesmie domýšľať.

DATABASE_ACCESS_MODE: READ-ONLY.

ALLOWED_DB_ACTIVITY: SELECT, JOIN, WITH, GROUP BY, UNION/UNION ALL a read-only Oracle dictionary views podľa compatibility pravidiel nižšie.

FORBIDDEN_DB_ACTIVITY: INSERT, UPDATE, DELETE, MERGE, ALTER, DROP, TRUNCATE, CREATE, GRANT, REVOKE, DDL/DML alebo PL/SQL meniace produkciu.

DEFAULT_TARGET: AGENT-READY pre hlavné transakčné objekty, master dáta a významné lookup/reference objekty.

NEVER_GUESS: TRUE - názov objektu, pole, JOIN, datatype, číselník, formula, lifecycle ani business význam sa nesmú vytvoriť odhadom.

UNVERIFIED_RESULT: TREBA OVERIŤ alebo DATA GAP; nikdy nie potvrdený fakt.

PRIMARY_HUMAN_BUSINESS_AUTHORITY: Martin / používateľ - business význam, reálne procesné použitie, autorita a výnimky.

CHATGPT_ROLE: Analytický orchestrátor: discovery, Mapping Packy, interpretácia, backlog, playbooky, contract.

CODEX_ROLE: Engineering vrstva: parsing, consistency checks, dependency graph, diff, repository, generovanie artefaktov. Codex neurčuje business význam bez dôkazu.

### 0.1 Absolútne pravidlá

- Pred novým mapovaním vždy najprv vyhľadaj existujúci katalóg. POTVRDENÉ mapovanie neopakuj bez dôvodu.
- Pre slovenskú produkciu je autoritatívny iba OWNER=MC.
- Pracuj evidence-first. Technický názov ani Oracle comment sám o sebe nepotvrdzuje business význam.
- Každý významný JOIN potvrď živým read-only testom a popíš kardinalitu aj fan-out riziko.
- Raw field, derived field, snapshot, history a analytická klasifikácia sú odlišné vrstvy.
- Ak nový dôkaz odporuje POTVRDENÉ faktu, fakt sa neprepíše potichu. Najprv konflikt -> TREBA OVERIŤ -> revalidačný test -> revision history.
- AGENT-READY znamená bezpečné autonómne použitie v deklarovanom scope, nie tvrdenie o absolútnej znalosti celého systému.

## 1. ENTERPRISE CIEĽ A ROZSAH

KASO Data Catalog je firemný dátový contract, nie dokumentácia jedného projektu. Cieľom je zmapovať hlavné Oracle objekty tak, aby ktorékoľvek oddelenie vedelo pripraviť spoľahlivý dashboard, report, SQL analýzu, diagnostiku alebo AI automatizáciu bez opakovaného reverse engineeringu databázy.

- ľubovoľné read-only SQL nad potvrdenými dátovými kontraktmi;
- Power BI a iné dashboardy bez opakovaného discovery;
- ad-hoc reporting pre logistiku, customer service, nákup, obchod, financie, výrobu, kvalitu a vedenie;
- diagnostika incidentov s rozlíšením dôkazu a interpretácie;
- AI agenti a automatizácie používajúce potvrdené source-of-truth, JOIN, mutation a temporal pravidlá;
- cross-domain využitie master dát bez duplikovania významu v každom dokumente.

### 1.1 Cieľová úroveň mapovania

Hlavné transakčné objekty, master dáta a významné lookup/reference objekty smerujú defaultne na AGENT-READY. Nižší stav je priebežný stav alebo výnimka pre technický/periférny/helper objekt bez samostatného business contractu. Cieľom nie je znižovať kvalitu, ale zabrániť duplicite a nekonečnému skúmaniu bez business hodnoty.

## 2. DÔKAZNÁ HIERARCHIA

Každé tvrdenie v katalógu musí byť opreté o dôkaz. Viac dôkazov sa môže kombinovať. Technický dôkaz však automaticky nepotvrdzuje business význam.

### A - Oracle metadata
- Zdroj: ALL_TAB_COLUMNS, ALL_CONSTRAINTS, ALL_INDEXES, ALL_OBJECTS a ďalšie read-only dictionary views dostupné účtu.
- Potvrdzuje: existenciu objektu/pola, datatype, nullable/default, PK/UQ/FK/CHECK, indexy, technickú štruktúru.
- Nepotvrdzuje automaticky: business význam.

### B - Živé read-only SELECT/JOIN nad MC
- Potvrdzuje: hodnoty, NULL, duplicity, uniqueness, kardinalitu, orphan stav, edge cases, reálne target JOINy, snapshot population profil.
- JOIN sa nepovažuje za potvrdený iba preto, že názvy polí vyzerajú podobne.

### B2 - Oracle source code
- Zdroj: ALL_SOURCE, TRIGGER, PACKAGE, PACKAGE BODY, PROCEDURE, FUNCTION, VIEW a súvisiace dependencies.
- Potvrdzuje: konštanty, CASE/DECODE, embedded SQL, DML writery, volania, call chain, exceptions, bypass/session logiku, side effects.
- Business význam sa podľa potreby validuje cez B/C/D.

### C - BarIS / Dreamer / HandyGO UI
- Potvrdzuje: používateľský label, UI stav, konkrétny doklad, workflow a zobrazenie.
- UI názov nie je fyzický Oracle názov bez metadata dôkazu.

### D - Business potvrdenie používateľa
- Potvrdzuje: reálny procesný význam, autoritu dát, moment vzniku, používanie a výnimky.

### E - Hypotéza / nejasnosť
- Nikdy nevstupuje do hlavného mapovania ako fakt.
- Patrí iba do Mapping backlogu s presným návrhom validačného testu.

## 3. STATUSY A VÝZNAM

POTVRDENÉ: Technické a/alebo business mapovanie je potvrdené relevantným dôkazom.

TECHNICKY ZNÁME: Fyzická existencia alebo technická väzba je známa; business interpretácia nemusí byť uzavretá.

ODVODENÉ: Hodnota vzniká výpočtom/mapou nad raw dátami; nie je samostatným raw poľom.

TREBA OVERIŤ: Otvorená otázka. Nesmie byť prezentovaná ako fakt.

DATA GAP: Spoľahlivý zdroj nie je dostupný alebo nie je známy.

NEPOUŽÍVAŤ: Pole/kontrakt je metodicky nevhodný alebo nespoľahlivý pre dané použitie.

DEPENDENCY ONLY: Technická dependency je potvrdená, ale writer/reader/caller rola nie je dokázaná.

### 3.1 Objektové maturity statusy
CORE MAPPED: Fyzický model, granularita, identita, hlavné polia a JOINy sú zmapované.

DIAGNOSTIC-GRADE: Navyše source of truth, temporal contract, mutation surface, relevantný source, DQ, SQL toolkit a playbooky.

EXHAUSTIVE DEPENDENCY-GRADE: Navyše primerane uzavretý source-visible dependency contract a caller/boundary surface.

AGENT-READY: Objekt je bezpečne použiteľný človekom alebo AI v deklarovanom scope; blocking backlog je uzavretý a systémové hranice sú explicitné.

## 4. KASO MAPPING METHOD v2.1

Mapovanie prebieha evidence-first v siedmich fázach. Fázy sa môžu čiastočne prekrývať, ale objekt sa nesmie uzavrieť skôr, než spĺňa Definition of Done pre cieľový status.

### FÁZA 0 - PRE-FLIGHT / EXISTUJÚCA ZNALOSŤ
- Vyhľadaj existujúce záznamy tabuľky, view, poľa, číselníka, triggera, package, procedure, JOINu, formule a business pravidla.
- Identifikuj POTVRDENÉ fakty, konflikty, otvorený backlog a externé autoritatívne domain contracts.
- Výstup: delta scope - čo už vieme, čo treba rozšíriť, čo treba revalidovať.

### FÁZA 1 - CORE PHYSICAL DISCOVERY
- Získaj TABLE/VIEW metadata, úplný field inventory, datatype, nullable/default/comment, PK/UQ/FK/CHECK, indexy, triggery a základné dependencies.
- Definuj granularitu jedného riadku a technickú identitu.
- Business význam podľa názvu poľa nehádať.

### FÁZA 2 - LIVE DATA PROFILING
- Profiluj MC: row count, NULL/non-NULL, distinct, duplicity, uniqueness kandidátov, distribúcie stavov, dátumové rozpätia, RID prefixy, sentinel hodnoty, orphan testy, cardinality a edge cases.
- Population counts a value profiles vždy označ ako snapshot s dátumom.

### FÁZA 3 - SOURCE & MUTATION DISCOVERY
- Analyzuj relevantné TRIGGER/PACKAGE/PACKAGE BODY/PROCEDURE/FUNCTION/VIEW.
- Mapuj: event/podmienka -> sledované polia -> session/bypass -> volania -> priame mutácie -> side effects -> exceptions -> business efekt -> diagnostický význam.
- Pre kritické polia vytvor Mutation Matrix.

### FÁZA 4 - DEPENDENCY CLOSURE / AGENT HARDENING
- Uzavri direct inbound/outbound dependencies a podľa významu transitive closure.
- Zmapuj core API caller surface, views, synonyms, grants, background jobs a cross-schema boundary.
- Writer/reader/caller klasifikuj iba s dôkazom; inak DEPENDENCY ONLY.
- Runtime SQL mimo Oracle source explicitne označ ako systémovú hranicu.

### FÁZA 5 - BUSINESS & TEMPORAL VALIDATION
- Rozlíš RAW CURRENT, STORED SNAPSHOT, DERIVED CURRENT, TRANSITION STAMP, LAST UPDATE, SELECTIVE HISTORY a DATA GAP.
- Urči source of truth a čo sa spätne rekonštruovať nedá.
- Business význam potvrď SQL↔UI alebo používateľom, ak technické dôkazy nestačia.

### FÁZA 6 - DIAGNOSTIC LAYER & CLOSURE
- Priprav canonical read-only SQL, DO NOT ASSUME, diagnostické playbooky, provenance, revision history a Mapping backlog.
- Urob closure audit voči AGENT-READY Definition of Done.
- Až potom povýš objekt na finálny status.

## 5. POVINNÝ CONTRACT MAPOVANÉHO OBJEKTU
BUSINESS CONTRACT: doména, business objekt, účel, granularita, hranice scope.

IDENTITY: PK alebo technický kľúč, alternate uniqueness, environment scope, RID/text pravidlá.

PHYSICAL SCHEMA: všetky fyzické polia, datatype, nullable/default/comment, canonical alias, business význam, status.

CONSTRAINTS & INDEXES: PK/UQ/FK/CHECK, ENABLED/VALIDATED stav, access paths, function-based indexy podľa relevance.

RELATIONSHIP CONTRACT: JOIN polia, kardinalita, podmienky, orphan/duplicate test, fan-out safety.

SOURCE OF TRUTH: raw autorita, snapshot/helper/cache, current vs history.

VALUE DOMAINS: observed values, lookup code+name, NULL/sentinel pravidlá.

LIFECYCLE & TEMPORAL: stavy, prechody, transition stamps, rollback vetvy, history/data gap.

MUTATION MATRIX: direct writers, triggers, packages/APIs, externé domény, podmienky zápisu.

SOURCE FLOW: event, condition, call, DML, side effect, exception, business effect.

DEPENDENCIES: direct/indirect dependency surface, caller surface, cross-schema/runtime boundaries.

DATA QUALITY: NULL, duplicity, orphan, drift, legacy, historizačné medzery.

DO NOT ASSUME: neintuitívne pravidlá a známe pasce.

DIAGNOSTIC PLAYBOOKS: symptóm, prvý SQL, interpretácia, ďalší krok, source flow, boundary.

CANONICAL SQL TOOLKIT: identity lookup, header+lines, JOINs, state, quantity/value, history, anomaly, dependency trace.

EVIDENCE & REVISION: Mapping Pack provenance, snapshot dátum, zdroj tvrdenia, revision history, backlog.

## 6. MAPPING PACK STANDARD
Používateľ nemá ručne reverse-engineerovať veľké množstvo source objektov, ak sa potrebné dôkazy dajú vytiahnuť širším read-only exportom. Preferuj 3-10 logických Mapping Packov pred desiatkami mikrodotazov.

MP-01 DISCOVERY: columns, constraints, indexes, triggers, object types, comments -> core inventory

MP-02 LIVE PROFILE: counts, nulls, distinct, duplicate/orphan/cardinality, value profile -> population + DQ

MP-03 SOURCE/MUTATION: ALL_SOURCE, trigger/package/body, DML hits, call context -> mutation matrix + lifecycle

MP-04 DEPENDENCY: ALL_DEPENDENCIES closure, caller surface, views, synonyms, grants -> dependency contract

MP-05 EDGE/VALIDATION: konkrétne RID, legacy, polymorfné targety, UI porovnania -> close backlog

MP-06 CLOSURE: negative completeness tests, unresolved review, evidence manifest -> final status

### 6.1 Pravidlá exportu
- RID, kódy a identifikátory s možnou úvodnou nulou exportuj ako text.
- NULL zachovaj ako NULL. Nevyrábaj prezentačný text, ktorý mení zdrojovú hodnotu.
- Každý pack pomenuj, časovo identifikuj a zapíš do proveniencie.
- Ďalší pack žiadaj iba vtedy, keď konkrétna medzera blokuje cieľový contract.
- Snapshot population výsledok sa nesmie prezentovať ako nemenná business konštanta.

## 7. MUTATION MATRIX A SOURCE FLOW
Pri stavových, množstevných, finančných a inak kritických objektoch je povinné zistiť KTO mení kritické polia. Samotný popis stĺpca nestačí.

field -> direct writer -> trigger -> package/API -> condition -> side effect -> diagnostic consequence

Pri významnom flow dokumentuj presne:

trigger/procedure -> event/condition -> watched fields -> session/bypass -> calls -> direct mutations -> side effects -> exceptions -> business effect -> diagnostic meaning

## 8. DEPENDENCY CLOSURE A HRANICE ÚPLNOSTI
- ALL_DEPENDENCIES a ALL_SOURCE používaj spolu. Compile-time dependency a source-text/API call nie sú totožné.
- Pri direct dependency klasifikuj writer/reader/caller iba s dôkazom; inak DEPENDENCY ONLY.
- Externú doménu detailne neduplikuj. Popíš boundary contract a odkáž na autoritatívny domain záznam.
- Grant alebo synonym znamená capability, nie automaticky reálny runtime flow.
- Negatívny job/scheduler/cross-schema audit je dôkaz iba v rozsahu dictionary views dostupných aktuálnemu účtu.
- Runtime SQL generovaný mimo Oracle source musí byť explicitne uvedený ako systémová hranica.

## 9. TEMPORAL CONTRACT A SOURCE OF TRUTH
RAW CURRENT: Aktuálna fyzická hodnota; nehovorí predchádzajúce hodnoty.

STORED SNAPSHOT: Procesne uložený stav/agregát; nemusí sa rovnať dnešnému recompute.

DERIVED CURRENT: Výpočet nad aktuálnymi raw dátami; nie historický stav v minulosti.

TRANSITION STAMP: Auditná stopa konkrétneho prechodu; nie kompletný event timeline.

LAST UPDATE: Posledná zmena riadku; nehovorí automaticky, ktoré business pole sa zmenilo.

SELECTIVE HISTORY: História vybraných udalostí; nie úplná história.

DATA GAP: Spoľahlivý historický zdroj nie je dostupný; rekonštrukciu nemožno domyslieť.

## 10. DIAGNOSTICKÝ ŠTANDARD

### 10.1 Canonical playbook
SYMPTÓM -> prvý read-only SQL -> čo výsledok dokazuje -> čo nedokazuje -> ďalší krok -> trigger/package flow -> external dependency -> business/temporal boundary

### 10.2 Canonical SQL Toolkit
- identifikácia objektu podľa PK/RID/display ID;
- hlavička + položky bez nebezpečného fan-out;
- hlavné master/lookup JOINy;
- raw a odvodený stav/lifecycle;
- quantity/value model a source-of-truth výpočet;
- history/audit pohľad s jasnými limitmi;
- anomaly detection / integrity shortlist;
- external dependency trace;
- stored snapshot vs live recompute, ak je relevantné;
- pri každom dôležitom SQL vysvetli granularitu, riziko duplicít a limit interpretácie.

## 11. SQL NAVIGATOR 5.5.4.847 - KOMPATIBILNÝ SQL ŠTANDARD
Používateľ pracuje v SQL Navigator 5.5.4.847. Táto verzia je záväzný klientsky kontext pre všetky Mapping Packy a diagnostické SQL. Oracle databázová serverová verzia nie je v tomto štandarde potvrdená, preto ju ChatGPT ani Codex nesmú predpokladať.

### 11.1 Povinné compatibility pravidlá
- Generuj plain Oracle SQL určený na spustenie v SQL Editore SQL Navigator 5.5.4.847.
- Nepoužívaj príkazy, skripty alebo UI workflow špecifické pre novšie verzie SQL Navigatora, SQL Developer, SQLcl alebo iné moderné klienty.
- Preferuj konzervatívnu Oracle syntax a read-only dictionary views ALL_* dostupné účtu.
- Ak je syntax alebo funkcia závislá od Oracle DB verzie a DB verzia nie je potvrdená, označ to TREBA OVERIŤ a priprav kompatibilnejšiu alternatívu.
- Pre limitovanie vzorky preferuj ROWNUM namiesto novších FETCH FIRST / OFFSET konštrukcií, pokiaľ nie je novšia syntax na MC výslovne overená.
- Nepoužívaj moderné JSON, MATCH_RECOGNIZE, CROSS/OUTER APPLY, recursive SQL, novšie PIVOT/UNPIVOT alebo iné version-sensitive prvky iba z pohodlnosti. Použi ich len po explicitnom overení kompatibility na MC.
- Pri string agregácii alebo inom version-sensitive helperi preferuj viac riadkov alebo jednoduchší export, ak nie je konkrétna funkcia potvrdená.
- WITH/CTE, CASE/DECODE, UNION ALL a bežné analytic SQL používaj iba vtedy, keď sú potrebné a overiteľné v aktuálnom MC prostredí; pri pochybnosti poskytni jednoduchší variant.
- SQL musí byť copy/paste spustiteľný bez potreby klientskych makier novších nástrojov.
- Každý Mapping Pack musí zostať read-only bez ohľadu na to, čo zdrojový trigger/package obsahuje.

### 11.2 Dôležité rozlíšenie klient vs databáza
SQL Navigator je klient, ktorý posiela Oracle SQL databáze. Schopnosť konkrétnej SQL syntaxe preto môže závisieť aj od verzie Oracle servera, nie iba od SQL Navigatora. Keď serverová verzia nie je potvrdená, AI musí voliť konzervatívny SQL štýl a nesmie tvrdiť kompatibilitu novšej Oracle funkcie bez testu.

## 12. DO NOT ASSUME - POVINNÁ SEKČIA
- RID prefix môže byť routing stopa, nie sám o sebe dôkaz úspešného target JOINu.
- Deklarovaný FK môže byť DISABLED / NOT VALIDATED.
- 1:N JOIN môže znásobiť headerové sumy.
- UI filter nie je univerzálny data contract.
- UI stav môže byť odvodený z FLAGS/package funkcie a nemusí byť fyzický stĺpec.
- Last-update stamp nie je event história.
- Grant/synonym neznamená reálny runtime flow.
- Stored derived hodnota môže byť historický snapshot a líšiť sa od live recompute.
- Globálna uniqueness medzi MC/MCCZ/TEST/TESTCZ sa nepredpokladá bez dôkazu.
- Oracle comment je technická stopa, nie automaticky business pravda.
- Moderná Oracle syntax nie je povolená iba preto, že ju pozná ChatGPT; musí byť kompatibilná s aktuálnym MC/SQL Navigator workflow.

## 13. CHANGE MANAGEMENT A PROVENIENCIA
- Potvrdený fakt sa nikdy neprepíše potichu.
- Každý Mapping Pack eviduje názov, dátum, environment, účel a ktorú časť contractu potvrdzuje.
- Population counts a value profiles majú snapshot dátum.
- Každý finálny objekt obsahuje revision history a Mapping backlog.
- Zmena canonical aliasu, granularitnej definície, JOIN kľúča alebo business významu je breaking change a musí byť explicitná.
- Ak sa pole prestane používať, nemaže sa bez stopy; označí sa NEPOUŽÍVAŤ alebo nahradené a uvedie sa nový autoritatívny zdroj.
- Externý domain contract sa referencuje autoritatívnou verziou; detail sa zbytočne neduplikuje.

## 14. ROLY
MARTIN / BUSINESS OWNER: Spúšťa read-only Mapping Packy, exportuje výsledky, poskytuje UI/business validáciu a schvaľuje reálny význam/výnimky. Nemá ručne reverse-engineerovať source, ak sa dá potrebný dôkaz exportovať.

CHATGPT: Navrhuje discovery a Mapping Packy, analyzuje exporty, rozhoduje čo je dôkaz vs hypotéza, pripravuje backlog, playbooky, canonical SQL a finálny contract. Nesmie domýšľať názvy ani business význam.

CODEX: Spracúva súbory a repozitár, parsuje exporty, robí consistency checks, dependency graph, linter, diff a generovanie artefaktov. Nesmie autonómne povýšiť business význam bez dôkazu D/C/B podľa situácie.

## 15. BUDÚCI CANONICAL FORMÁT - MACHINE READABLE
DOCX je human-readable publikačný výstup. Dlhodobý source of truth má byť strojovo čitateľný a version-controlled. Konkrétnu implementáciu repozitára táto verzia ešte nezavádza.

- Každý objekt, pole, JOIN, rule, dependency a evidence má mať samostatne adresovateľný záznam.
- Oracle názvy sa zachovávajú presne. Canonical aliasy sú anglicky, ASCII, snake_case.
- Status a evidence nesmú byť iba vo voľnom texte; musia byť strojovo validovateľné.
- Potvrdená znalosť master objektu sa nereplikuje do každej domény; ostatné objekty na ňu odkazujú.
- Z machine-readable vrstvy sa má dať generovať DOCX, SQL context pre agentov, index, dependency mapa a validačné reporty.
- Codex je vhodný na build/validate/diff workflow; ChatGPT na analytické rozhodnutia a business orchestration.

Oracle evidence -> machine-readable canonical catalog -> generated documentation + SQL toolkit + agent context

## 16. AGENT-READY DEFINITION OF DONE v2.1
- [ ] Existujúci katalóg bol pred discovery prehľadaný.
- [ ] MC autoritatívne metadata sú kompletné pre deklarovaný scope.
- [ ] Granularita a identity scope sú uzavreté.
- [ ] Úplný field inventory a canonical aliasy sú zdokumentované.
- [ ] PK/UQ/FK/CHECK/indexy sú zdokumentované vrátane validation statusu.
- [ ] Hlavné JOINy sú live otestované a majú cardinality contract.
- [ ] JOIN fan-out safety je explicitná.
- [ ] Source of truth vs snapshot/current/history je rozlíšený.
- [ ] State/quantity/value model je uzavretý podľa relevance.
- [ ] Relevantné triggers/packages/procedures sú zmapované.
- [ ] Mutation matrix existuje pre kritické polia.
- [ ] Direct/indirect dependency contract je primerane uzavretý.
- [ ] Core API caller / synonym / grant / job / cross-schema boundaries sú uzavreté podľa relevance.
- [ ] Runtime boundary je explicitne uvedená.
- [ ] DQ a edge cases sú zdokumentované.
- [ ] DO NOT ASSUME sekcia existuje.
- [ ] Diagnostic playbooky existujú podľa relevance.
- [ ] Canonical read-only SQL toolkit je pripravený.
- [ ] SQL je kompatibilne navrhnutý pre SQL Navigator 5.5.4.847; version-sensitive syntax nie je použitá bez overenia.
- [ ] Mapping backlog nemá blocking body.
- [ ] Evidence/provenance a snapshot dátumy sú evidované.
- [ ] Revision history je aktualizovaná.
- [ ] Kritické business významy sú potvrdené relevantným dôkazom.

## 17. KRITÉRIUM, KEDY PRESTAŤ S DIGGINGOM
Digging sa ukončí, keď sú všetky blocking otázky pre cieľový contract uzavreté a zostávajúce nejasnosti sú explicitné neblokujúce boundaries alebo DATA GAP. AGENT-READY nevyžaduje nekonečný reverse engineering každej tranzitívnej závislosti bez business hodnoty; vyžaduje dostatočný contract pre bezpečné autonómne použitie.

## 18. HANDOVER INŠTRUKCIA PRE NOVÝ CHAT / CODEX
1. Read this standard first.
2. Search existing KASO Data Catalog before proposing new mapping.
3. Treat OWNER=MC as authoritative for Slovak production.
4. Use read-only SQL only. Target SQL Navigator 5.5.4.847 and conservative Oracle syntax.
5. Do not guess. Put unverified claims only into Mapping backlog as TREBA OVERIŤ or DATA GAP.
6. Start with MP-01 Discovery, then continue autonomously through live profile, source/mutation, dependency, business/temporal validation, diagnostic layer and closure.
7. Ask Martin for another export or UI/business validation only when a concrete gap blocks safe contract closure.
8. Default target for main transaction objects, master data and important lookups is AGENT-READY.

## 19. UZAVRETÉ ROZHODNUTIA
1. KASO Data Catalog je enterprise firemný dátový contract, nie projektová dokumentácia.
2. Hlavné transakčné objekty, master dáta a významné lookupy smerujú defaultne na AGENT-READY.
3. AGENT-READY je relatívne k deklarovanému scope a dostupným dôkazom; hranice sa uvádzajú explicitne.
4. Mapovanie je evidence-first, výhradne read-only a autoritatívne pre slovenskú produkciu iba na MC.
5. Source/mutation a dependency closure sú povinnou súčasťou významných agent-ready objektov.
6. Dokumentácia musí rozlišovať current, snapshot, derived, audit/history a DATA GAP.
7. Používateľská manuálna práca sa minimalizuje cez širšie Mapping Packy.
8. SQL workflow je viazaný na SQL Navigator 5.5.4.847; DB server verziu nemožno domýšľať.
9. Budúci canonical source of truth bude machine-readable/version-controlled; DOCX bude publikačný výstup.
10. ChatGPT zostáva analytický orchestrátor, Codex engineering/automation vrstva, Martin business autorita.
11. Ďalšia fáza projektu: navrhnúť machine-readable schému a pilotne previesť uzavretý CESTOVNE_PR_L/O v1.1.

## 20. REFERENČNÉ KATALÓGOVÉ ZDROJE
- KASO Data Catalog - Technical & Diagnostic Reference - cestovné príkazy v1.1: benchmark EXHAUSTIVE DEPENDENCY-GRADE / AGENT-READY.
- KASO Data Catalog - Technical & Diagnostic Reference - obchodné prípady v1.2: diagnostic-grade field/JOIN/temporal/fan-out contract.
- KASO Data Catalog - Technical & Diagnostic Reference - výdajky v1.0: mutation, quantity, return lifecycle a WMS/transport boundaries.
- KASO Data Catalog Other Mapped Objects v0.4: prechodné objekty, WMS backlog, externé domain contracts a provenance.

## 21. REVÍZNA HISTÓRIA
2.1 - 9. 9. 2026: ChatGPT/AI-friendly repackaging. Odstránené design-manual závislosti; obsah preusporiadaný na parser-friendly headings, key-value pravidlá a jednoduché listy. Doplnený záväzný SQL klient SQL Navigator 5.5.4.847 a compatibility contract bez predpokladania Oracle serverovej verzie.

2.0 - 9. 9. 2026: Prvý samostatný enterprise Mapping Method & Agent-Ready Standard. Zavedený AGENT-READY by default pre firemné dátové jadro, evidence-first workflow, Mapping Pack standard, dependency closure, temporal contract a roly ChatGPT/Codex/business owner.

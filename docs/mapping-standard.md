# KASO Data Catalog - Mapping Method & Agent-Ready Standard

## v2.2 - ChatGPT / Codex handoff & canonical pipeline

Tento dokument je zámerne formátovaný jednoducho: bez grafických prvkov, text boxov, log, farebných významov a layoutových závislostí. Primárnym cieľom je presná orientácia ChatGPT, Codexu a ďalších AI nástrojov v pravidlách KASO Data Catalogu. Human-readable DOCX zostáva publikačný výstup. Canonical source of truth je machine-readable, version-controlled KASO Data Catalog v GitHub repozitári; publikácie a viewery sa z neho generujú.

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

CANONICAL_SOURCE_OF_TRUTH: GitHub `main` machine-readable catalog. DOCX/PDF/web viewer sú odvodené publikácie, nie konkurenčná autorita.

HANDOFF_GATE: `READY FOR CODEX HANDOFF` - ChatGPT ho smie vyhlásiť až po semantic closure a uzavretí blocking backlogu pre cieľový scope.

CODEX_ENTRYPOINT: najprv prečíta `AGENTS.md`, aktuálny mapping standard, handoff package a existujúci domain contract; potom vykoná iba engineering kroky.

VIEWER_ROLE: read-only prezentačná vrstva generovaná z canonical YAML; nesmie obsahovať význam, ktorý nie je v canonical contracte.

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

## 4. KASO MAPPING METHOD v2.2

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
MARTIN / BUSINESS OWNER: Spúšťa read-only Mapping Packy, exportuje výsledky, poskytuje UI/business validáciu a schvaľuje reálny význam/výnimky. Nemá ručne reverse-engineerovať source, ak sa potrebný dôkaz dá exportovať.

CHATGPT / MAPPING ORCHESTRATOR: Vedie F0-F6. Pred discovery vyhľadá existujúci machine-readable katalóg a Project files, navrhuje Mapping Packy, analyzuje exporty, odlišuje dôkaz od hypotézy, uzatvára business/temporal/mutation/dependency contract, pripravuje backlog, playbooky a canonical SQL. ChatGPT rozhoduje o semantic closure; nesmie domýšľať názvy ani business význam.

CODEX / CATALOG ENGINEER: Nastupuje po `READY FOR CODEX HANDOFF`. Číta `AGENTS.md` a handoff package, spracúva súbory a repozitár, materializuje schválený contract do YAML/SQL/evidence manifests, robí parsing, consistency checks, dependency graph, lint, diff, testy, PR a generovanie publikácií/viewera. Nesmie vytvoriť nový business fakt, meniť význam, povýšiť status ani uzavrieť backlog bez dôkazu dodaného ChatGPT/business ownerom.

## 15. CANONICAL MACHINE-READABLE FORMÁT A PUBLIKAČNÝ PIPELINE
Canonical source of truth je machine-readable KASO Data Catalog vo version-controlled GitHub repozitári. DOCX/PDF a budúci web viewer sú odvodené human-readable publikácie.

- Každý objekt, pole, JOIN, rule, dependency, evidence, backlog a revision má samostatne adresovateľný záznam.
- Oracle názvy sa zachovávajú presne; canonical aliasy sú anglicky, ASCII, snake_case.
- Status a evidence sú strojovo validovateľné, nie iba vo voľnom texte.
- Potvrdená znalosť master/externej domény sa neduplikuje; ostatné contracts na ňu odkazujú.
- GitHub `main` je autorita po úspešnom review/CI. Feature branch/PR je návrh, nie potvrdený canonical stav.
- DOCX sa po zavedení generátora generuje z canonical vrstvy; ručná oprava DOCX nesmie potichu meniť canonical význam.
- Web viewer je read-only frontend nad canonical catalogom: vyhľadávanie objektov/polí/JOINov/packageov/triggerov, dependency mapa, evidence, SQL, backlog a revision history.
- Viewer ani generátor nesmú dopĺňať chýbajúci business význam heuristikou.

Pipeline:

Oracle evidence -> ChatGPT semantic mapping -> READY FOR CODEX HANDOFF -> Codex engineering -> PR/validation -> GitHub main canonical catalog -> generated DOCX/PDF/viewer + SQL/agent context

## 16. AGENT-READY DEFINITION OF DONE v2.2
- [ ] Existujúci katalóg bol pred discovery prehľadaný.
- [ ] MC autoritatívne metadata sú kompletné pre deklarovaný scope.
- [ ] Granularita a identity scope sú uzavreté.
- [ ] Úplný field inventory a canonical aliasy sú zdokumentované.
- [ ] PK/UQ/FK/CHECK/indexy sú zdokumentované vrátane validation statusu.
- [ ] Hlavné JOINy sú live otestované a majú cardinality contract + fan-out safety.
- [ ] Source of truth vs snapshot/current/history je rozlíšený.
- [ ] State/quantity/value model je uzavretý podľa relevance.
- [ ] Relevantné triggers/packages/procedures sú zmapované.
- [ ] Mutation Matrix existuje pre kritické polia.
- [ ] Direct/indirect dependency contract a core API caller surface sú primerane uzavreté.
- [ ] Synonym/grant/job/cross-schema/runtime boundaries sú uzavreté podľa relevance.
- [ ] DQ a edge cases, DO NOT ASSUME, playbooky a canonical read-only SQL existujú.
- [ ] SQL rešpektuje SQL Navigator 5.5.4.847; version-sensitive syntax nie je použitá bez overenia.
- [ ] Mapping backlog nemá blocking body.
- [ ] Evidence/provenance, snapshot dátumy a revision history sú aktualizované.
- [ ] Kritické business významy sú potvrdené relevantným dôkazom.
- [ ] ChatGPT vykonal semantic closure audit a vydal `READY FOR CODEX HANDOFF`.
- [ ] Codex materializoval contract bez semantic loss; generic + domain acceptance testy a CI prešli.
- [ ] PR diff obsahuje iba zamýšľané zmeny a po merge je canonical `main` zelený.

## 17. KRITÉRIUM, KEDY PRESTAŤ S DIGGINGOM
Digging sa ukončí, keď sú všetky blocking otázky pre cieľový contract uzavreté a zostávajúce nejasnosti sú explicitné neblokujúce boundaries alebo DATA GAP. AGENT-READY nevyžaduje nekonečný reverse engineering každej tranzitívnej závislosti bez business hodnoty; vyžaduje dostatočný contract pre bezpečné autonómne použitie. Potom sa už nepokračuje v všeobecnom discovery, ale vykoná sa semantic closure a handoff.

## 18. CHATGPT -> CODEX HANDOFF PROTOCOL
`READY FOR CODEX HANDOFF` je formálny prechod medzi analytickou a engineering vrstvou. ChatGPT ho vyhlási iba vtedy, keď:

1. blocking backlog pre cieľový scope = 0;
2. AGENT-READY semantic DoD je splnený alebo je explicitne uvedený nižší schválený target maturity;
3. všetky tvrdenia určené na materializáciu majú status a evidence/provenance;
4. neblokujúce DATA GAP/boundaries sú explicitné;
5. je jasné, ktoré existujúce canonical záznamy sa vytvárajú, menia alebo iba referencujú.

Povinný handoff package obsahuje minimálne:

```text
KASO CODEX HANDOFF
Domain:
Objects:
Target maturity:
Authoritative environment: MC
Canonical repo/path:
Existing canonical refs:
Approved evidence / Mapping Packs:
Confirmed semantic contract:
Critical JOINs + fan-out rules:
Source-of-truth / temporal rules:
Mutation/dependency boundaries:
DO NOT ASSUME:
Blocking backlog: NONE | items
Non-blocking gaps/boundaries:
Canonical SQL to materialize:
Repository actions required:
Publication actions required:
Acceptance tests / expected counts:
Breaking-change flag + revision note:
```

Handoff nie je náhrada dôkazov. Pri väčšom objekte má odkazovať na evidence/exporty a finálny mapping contract, nie ich celé duplikovať.

## 19. CODEX ENGINEERING WORKFLOW
Po handoffe Codex:

1. prečíta `AGENTS.md`, mapping standard a existujúci domain contract v `main`;
2. vytvorí feature branch; canonical `main` nemení nekontrolovane;
3. prenesie iba schválené fakty do machine-readable records a evidence manifests;
4. zachová stabilné ID a revision/change-management pravidlá; breaking change explicitne označí;
5. spustí validator, generic testy, domain acceptance gate a SQL safety lint podľa relevance;
6. skontroluje unresolved references, duplicate IDs, evidence requirements a semantic-loss acceptance assertions;
7. pripraví PR s jasným scope, známymi boundaries a výsledkom testov;
8. merge povolí až pri zelenom CI a čistom diff-e; po merge overí `main` workflow;
9. generuje/aktualizuje DOCX/PDF/viewer iba z canonical vrstvy, keď je generátor dostupný.

Codex pri konflikte, chýbajúcom dôkaze alebo nejasnom business význame nezvolí „najpravdepodobnejšie“ riešenie. Zastaví engineering konkrétneho faktu a vráti ho ChatGPT ako `HANDOFF BLOCKED` s presným dôvodom.

## 20. NOVÝ CHAT - POVINNÉ SPRÁVANIE
Ak používateľ otvorí nový chat v KASO projekte a zadá nový objekt/skupinu objektov:

1. najprv vyhľadaj Project files a canonical GitHub catalog; zisti existujúce facts/backlog/boundaries;
2. neopakuj POTVRDENÉ mapping bez dôvodu; priprav delta scope;
3. pokračuj F0-F6 a Mapping Pack workflow autonómne;
4. pýtaj ďalší export alebo UI/business potvrdenie iba pri konkrétnom blocking gape;
5. default target významných objektov = AGENT-READY;
6. po semantic closure explicitne oznám `READY FOR CODEX HANDOFF` a vytvor handoff package;
7. Codex používaj na repository/build/validate/publish engineering, nie na určovanie neovereného business významu.

## 21. UZAVRETÉ ROZHODNUTIA
1. KASO Data Catalog je enterprise firemný dátový contract, nie projektová dokumentácia.
2. Hlavné transakčné objekty, master dáta a významné lookupy smerujú defaultne na AGENT-READY.
3. Mapovanie je evidence-first, výhradne read-only a pre slovenskú produkciu autoritatívne iba na MC.
4. ChatGPT vlastní semantic mapping a closure; Codex vlastní engineering materializáciu a validáciu.
5. Formálny prechod je `READY FOR CODEX HANDOFF` + štandardizovaný handoff package.
6. Canonical source of truth je machine-readable GitHub `main`; DOCX/PDF/viewer sú odvodené publikácie.
7. Source/mutation, temporal contract a dependency closure sú povinné pre významné agent-ready objekty.
8. Používateľská manuálna práca sa minimalizuje cez širšie Mapping Packy.
9. SQL workflow je viazaný na SQL Navigator 5.5.4.847; DB server verziu nemožno domýšľať.
10. Runtime SQL mimo Oracle-visible source zostáva explicitná systémová hranica.
11. CESTOVNE_PR_L/O v1.1 je prvý production machine-readable AGENT-READY pilot a acceptance benchmark.
12. Webový KASO Catalog Viewer má byť read-only prezentačná vrstva generovaná z canonical catalogu, nie nový source of truth.

## 22. REFERENČNÉ KATALÓGOVÉ ZDROJE
- GitHub `mtasky-mccarter/kaso-data-catalog`, branch `main`: canonical machine-readable KASO Data Catalog.
- `AGENTS.md`: záväzné repository/Codex pravidlá.
- `docs/mapping-standard.md`: repository transcription tohto štandardu.
- KASO Data Catalog - Technical & Diagnostic Reference - cestovné príkazy v1.1: benchmark EXHAUSTIVE DEPENDENCY-GRADE / AGENT-READY.
- KASO Data Catalog - Technical & Diagnostic Reference - obchodné prípady v1.2: diagnostic-grade field/JOIN/temporal/fan-out contract.
- KASO Data Catalog - Technical & Diagnostic Reference - výdajky v1.0: mutation, quantity, return lifecycle a WMS/transport boundaries.
- KASO Data Catalog Other Mapped Objects v0.4: prechodné objekty, WMS backlog, externé domain contracts a provenance.

## 23. REVÍZNA HISTÓRIA
2.2 - 10. 9. 2026: Formalizovaný ChatGPT -> Codex handoff. Zavedený stav `READY FOR CODEX HANDOFF`, povinný handoff package, Codex engineering workflow, nový-chat protocol, GitHub `main` ako canonical source of truth a DOCX/PDF/viewer ako odvodené publikácie. Aktualizovaný AGENT-READY DoD o repository acceptance a post-merge CI.

2.1 - 9. 9. 2026: ChatGPT/AI-friendly repackaging. Odstránené design-manual závislosti; obsah preusporiadaný na parser-friendly headings, key-value pravidlá a jednoduché listy. Doplnený záväzný SQL klient SQL Navigator 5.5.4.847 a compatibility contract bez predpokladania Oracle serverovej verzie.

2.0 - 9. 9. 2026: Prvý samostatný enterprise Mapping Method & Agent-Ready Standard. Zavedený AGENT-READY by default pre firemné dátové jadro, evidence-first workflow, Mapping Pack standard, dependency closure, temporal contract a roly ChatGPT/Codex/business owner.

# KASO Data Catalog — Machine-readable schema v1.0

## 1. Účel
Machine-readable vrstva je dlhodobý source of truth katalógu. DOCX/PDF publikácie sú generované pohľady; potvrdený fakt sa má udržiavať v štruktúrovanom contracte a viazať na evidenciu.

Schema v1.0 je navrhnutá pre evidence-first mapovanie Oracle objektov v KASO. Slovenská produkcia `OWNER=MC` je autoritatívna pre slovenský contract. MCCZ, TEST a TESTCZ sú samostatné prostredia a ich dáta sa bez samostatnej validácie nepovyšujú na dôkaz pre MC.

## 2. Základné pravidlá
- Oracle názvy sa zachovávajú presne; canonical aliasy sú anglicky, ASCII a `snake_case`.
- RID/kódy s možnou úvodnou nulou sa modelujú ako text, nie číslo.
- Source `NULL` sa zachová ako YAML `null`; literal string `NULL` sa nesmie potichu meniť.
- POTVRDENÉ tvrdenie musí mať validný evidence manifest a nesmie byť podopreté iba triedou E.
- Writer/reader/caller rola sa neodvodzuje iba z grantov alebo compile-time dependency; bez source dôkazu zostáva `DEPENDENCY ONLY` alebo `ACCESS CAPABILITY`.
- Population counts, value distributions a live integrity výsledky sú snapshoty s dátumom, nie večné business konštanty.
- Oracle serverová verzia nie je potvrdená. Canonical SQL je deklarovaný ako read-only a kompatibilný so SQL Navigator 5.5.4.847 v overenom scope.

## 3. Record kinds
Schema v1.0 momentálne obsahuje 23 JSON Schema Draft 2020-12 definícií:

1. `object` — business/physical contract objektu, granularita, identita, maturity a scope.
2. `fields` — úplný fyzický field inventory, datatype, NULL/default/comment, alias, význam, status a evidencia.
3. `constraints` — PK/UQ/FK/CHECK a stav enforcementu/validácie.
4. `indexes` — indexy a ich stĺpcové poradie.
5. `relationships` — JOIN contract, cardinality, fan-out, orphan/duplicate testy a polymorfné targety.
6. `value-domains` — potvrdené kódy/flagy/stavy a live výskyt.
7. `temporal` — RAW CURRENT, STORED SNAPSHOT, DERIVED CURRENT, TRANSITION STAMP, LAST UPDATE, SELECTIVE HISTORY a DATA GAP.
8. `mutations` — Mutation Matrix kritických polí a writerov.
9. `flows` — event/podmienka → watched fields → bypass → calls → direct mutations → side effects → exceptions → business/diagnostic effect.
10. `dependencies` — klasifikovaný dependency register.
11. `dependency-edges` — source-visible direct/transitive dependency closure s depth a edge provenance.
12. `dependency-nodes` — unikátne inbound/outbound closure uzly s minimálnou depth; uzol nie je dependency edge.
13. `oracle-entities` — technické Oracle objekty/boundaries, ktoré nemusia mať plný business-object contract.
14. `api-references` — source member referencie na core package API, caller/member/hit-line register.
15. `data-quality` — snapshotované DQ pozorovania a diagnostické limity.
16. `do-not-assume` — explicitné zákazy nebezpečných inferencií.
17. `playbooks` — diagnostické postupy symptóm → SQL → dôkaz/limit → next step/boundary.
18. `sql-registry` — registry canonical read-only SQL a kompatibilita.
19. `backlog` — TREBA OVERIŤ/DATA GAP s blocking flagom a closure condition.
20. `revisions` — revision history a breaking-change evidencia.
21. `evidence-manifest` — provenance, evidence class, snapshot, retention a checksum.
22. `contract` — agregujúci domain contract s object/component/boundary/evidence refs.
23. `common` — zdieľané typy: ID, refs, alias, status, maturity, temporal class, evidence class a retention.

## 4. Stable IDs a reference graph
Každý záznam, ktorý môže byť cieľom cross-file väzby, používa stabilné ID. ID nie je display label ani filesystem path. Validator vytvorí globálny index ID a kontroluje duplicity aj unresolved refs.

`contract.yaml` je vstupný bod domény. Odkazuje na hlavné objekty, komponenty, boundary records a evidence manifests. Detailný contract sa nesmie duplikovať do susedných domén; cross-domain objekt má mať boundary relationship a autoritatívny detail v svojej doméne.

## 5. Evidence model
Evidence manifest eviduje minimálne `evidence_id`, triedu A/B/B2/C/D/E, prostredie, owner, source file/query, snapshot a retention. `SNAPSHOT_CRITICAL` evidencia musí byť fyzicky retained s kontrolovateľným checksumom; transient/reproducible evidencia môže byť reprezentovaná manifestom bez uloženia surového exportu podľa retention policy.

Canonical evidence umiestnenie je `evidence/manifests/`. Projektový layout test zámerne odmieta YAML manifesty priamo v koreňovom `evidence/`, aby nevznikli dve konkurenčné kópie toho istého dôkazu.

## 6. Dependency a API hardening
`dependencies` zachytáva klasifikovanú rolu objektu voči contractu; `dependency-edges` zachytáva skutočné graph hrany a `dependency-nodes` unikátne členstvo uzla v closure. Pri exhaustive audite sa direct/transitive counts musia viazať na konkrétny evidence dataset a depth. Edge count a node count sa nesmú zamieňať.

`api-references` zachytáva source-visible member referencie na core package API. Summary (`record_count`, `caller_count`, `member_count`) je testovaný proti records a každý `hit_count` proti počtu `hit_lines`. Tento register dokazuje source member reference, nie automaticky runtime frequency ani business autoritu.

## 7. Mutation a temporal contract
Pre kritické polia sa používa `mutations` a pre trigger/procedure správanie `flows`. Cieľom je bezpečne oddeliť current state od transition auditov, derived snapshots a selective history. `reconstructable=false` je explicitný zákaz tvrdiť úplnú históriu, ak ju zdroj nevie poskytnúť.

## 8. SQL contract
`sql-registry` odkazuje na samostatné `.sql` súbory. SQL telo sa nevkladá do YAML, aby sa zachovala copy/paste použiteľnosť a samostatná kontrola read-only safety. V produkčnom mapping scope sú povolené iba read-only SELECT/JOIN/WITH/GROUP BY/UNION a ALL_* dictionary views podľa Mapping Standardu.

## 9. Validator
`tools/validate_catalog.py` kontroluje JSON Schema conformance, YAML strictness, global ID uniqueness, cross-file references, evidence targeting, evidence-class pravidlá, retained checksumy a ďalšie cross-file invariants. Doplnkové unittesty kontrolujú api-reference summaries, dependency-edge summaries, repository layout a domain-specific acceptance gate.

Validator nie je Oracle parser a sám o sebe nepotvrdzuje business význam, JOIN správnosť ani úplnosť runtime SQL mimo Oracle source. Tieto tvrdenia musia zostať viazané na A/B/B2/C/D evidence a closure audit.

## 10. CI
GitHub Actions používa Python 3.11 a aktuálnu Node-runtime generáciu action balíkov (`actions/checkout@v7`, `actions/setup-python@v7`). Workflow beží pri pull requestoch do `main` a do stacked schema branch; `main` sa kontroluje aj po push/merge. Samostatné feature-branch push runy sa nespúšťajú, ak ten istý change pokrýva PR validation, aby sa nevytvárali duplicitné CI runy a notifikácie.

## 11. Production acceptance pattern
Generic schema sa nepovažuje za dostatočnú len na základe synthetic fixtures. Komplexný reálny objekt musí mať domain-specific acceptance test, ktorý overí, že pri migrácii nebol potichu stratený field inventory, identita, state/temporal contract, polymorfné JOINy, mutation/source flow, dependency surface, diagnostics, evidence a blocking backlog.

Pilot `CESTOVNE_PR_L + CESTOVNE_PR_O v1.1` je prvý production acceptance gate tohto formátu. Generic schéma nesmie kvôli jednému objektu domýšľať business pravdu; domain-specific test kontroluje iba lossless reprezentáciu už preskúmaného a akceptovaného contractu.

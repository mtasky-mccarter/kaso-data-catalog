# READY FOR CODEX HANDOFF — KASO Data Catalog — Skladové karty / Product Master

## 1. Domain / scope
- Domain: Product Master / skladové karty
- Authoritative environment: MC production
- Oracle owner: MC
- Root object: MC.SKLAD_KARTA
- Target maturity: EXHAUSTIVE DEPENDENCY-GRADE / AGENT-READY
- Blocking backlog: 0
- Proposed initial canonical contract revision: 1.0
- Canonical repository: mtasky-mccarter/kaso-data-catalog
- Canonical branch: main
- Target canonical path: catalog/master/skladove-karty/
- Target diagnostic SQL path: sql/diagnostic/skladove-karty/
- Publication: DO NOT generate yet; documentation_version/publication approval is deferred.

## 2. Existing canonical context
- main is the machine-readable source of truth.
- catalog/master currently contains no Product Master contract for SKLAD_KARTA.
- Existing contracts (e.g. warehouse/vydajky) are references for repository structure, stable IDs, evidence manifests, SQL registry, backlog and revision handling.
- Preserve repo rules from AGENTS.md, docs/mapping-standard.md and docs/publication-standard.md.

## 3. Business contract
MC.SKLAD_KARTA is the central current master of stock/product cards used across BarIS/Dreamer/KASO processes. One root row = one skladová karta.

Scope includes root master plus directly maintained/interpreted master satellites and important lookups required to safely use the card:
- MC.SKLAD_KARTA
- MC.SKLAD_KARTA_LB
- MC.B_KOD_U
- MC.SK_LOG_UDAJE
- MC.SKLAD_DODAVATEL
- MC.SKLAD_KARTA_FU
- MC.SKLAD_PARTNER_KODY
- MC.SK_JEDNOTKY
- relevant lookup/reference objects confirmed by metadata/live joins
- typed notes: CIS_POZNAMKY + CIS_POZNAMKY_TYPY, with product-context RID_V relation
- cost/regulatory layer: SK_NAKL_POLOZKY + NAKL_KOEF and relevant helper definitions
- relevant CIS_DU_O definitions for DU1/4/5/6/7/8/9
- report runtime objects only as downstream evidence/boundary for Recyklačný fond SK/CZ

Explicitly exclude from Product Master:
- Kusy
- Blokácie
- Pasívne kusy
These belong to a future Stock/Inventory domain.

Manufacturing, orders, issues, receipts, pricing, WMS/inventory and other transaction domains remain boundaries unless an already-canonical contract is referenced.

## 4. Root physical facts — MC.SKLAD_KARTA
Snapshot / mapping closure: 2026-09-14 to 2026-09-15.

- 169 physical columns
  - 110 NUMBER
  - 55 VARCHAR2
  - 3 DATE: ZALOZENA, DATUM_MINMAX, DATUM
  - 1 XMLTYPE
- PK: XPK_SKLAD_KARTA(ID)
- ID NUMBER(8), NOT NULL
- SK_ID NOT NULL, unique
- RID VARCHAR2(16), NOT NULL, unique
- RID_OBJ VARCHAR2(16), NOT NULL, unique index
- INT_KOD VARCHAR2(30), NOT NULL
- design uniqueness: (INT_KOD, SKLAD)
- current MC INT_KOD is unique, but this is a snapshot fact, not a permanent/global contract.
- 32 outbound foreign keys
- 35 index rows / 31 index names
- 21 enabled direct triggers
- 416 dependency rows / 414 dependent objects
- 53 dependent views
- 33 source-visible direct writer objects outside C_SKLAD_KARTA
- 324 inbound FKs from 294 tables to ID; 253 child FKs use KOD_ID

Current snapshot rows: 7,429.
Current equality observations:
- ID = SK_ID on 100% of current rows
- RID = RID_OBJ on 100% of current rows
These are current observations only, not cross-environment or historical identity rules.

## 5. Identity / code rules
- Root grain: one current stock/product master card.
- ID is the physical PK.
- SK_ID/RID/RID_OBJ are alternate technical identifiers with their own uniqueness constraints/indexing.
- Preserve RID/code values as text where leading zeros are possible.
- INT_KOD is user-facing internal code. Do not assume universal numeric format, fixed length, or TO_NUMBER safety.
- Observed INT_KOD patterns include numeric, N-prefix, FIN/other alphanumeric. Prefixes are conventions, not replacement for typed classification.
- No global uniqueness may be assumed across MC/MCCZ/TEST/TESTCZ.

## 6. Current state model
- USED = technical active/storno layer; it is not equivalent to “is sold”.
- STAV = business/sales state layer; it is independent from USED.
- Current STAV distribution: 8=4366, 2=2549, 6=177, 3=168, 4=167, 0=2.
- Current USED distribution: 0=4504, 1=2925.
- 35 current rows have USED=1 and STAV=8, proving the two dimensions are not interchangeable.
- STAV=8 source flow calls MCCARTER_PLAN.MC_UKONCENY_PREDAJ_SK and can zero future OBCH_PL_O planned quantities.

T_TOVARU is the usable current type classification. Current examples/counts include:
- 1 Materiál: 2513
- 47 Náhradné diely: 1364
- 3 Výrobok: 1195
- 0 Tovar: 897
- 2 Polotovar: 649
- 7 labels/cartons: 325
Active Tovar + Výrobok snapshot: 556.

TYP_T:
- current population: 12 rows with value '00'
- PM-10B2 showed no resolution through TOVAR_TYP.ID, TOVAR_TYP.TYP_T, or CIS_TREE.TREE
- classify as TECHNICKY ZNÁME / business TREBA OVERIŤ, current unresolved legacy-like value
- DO NOT use as product classification in AI/DQ rules.

## 7. Temporal contract
Classification: RAW CURRENT master.
- I_STAMP = technical insert stamp
- U_STAMP = last technical update stamp
- S_STAMP = technical remove/storno stamp
- N_STAMP = selective process stamp related to Novinka; not creation date, not universal lifecycle stamp
- SKLAD_KARTA_INTKOD_Z and HIST_ZMIEN provide selective history only
- SK_TEMP is a process/change queue, not full audit history
- arbitrary historical reconstruction of all master attributes is NOT available

Downstream historical transaction joined to current SKLAD_KARTA must not be treated as historical master truth unless the transaction stores its own confirmed snapshot.

## 8. Self-reference semantics
### NAHRADA
Technical mechanism is confirmed:
- SKLAD_KARTA.NAHRADA -> SKLAD_KARTA.ID
- one self-anchor per group (anchor ID = NAHRADA)
- other members point to the anchor
- PM-10F: 164 groups; 3,162 rows with NAHRADA<>0; 164 self anchors; 2,998 non-anchor members; 837 members USED=1
- groups are real and can be large

Business meaning is NOT confirmed. User does not know current business use and will verify with KASO.
Status: TECHNICKY ZNÁME + TREBA OVERIŤ (non-blocking).
AI/DQ MUST NOT treat group members as physically or commercially substitutable and MUST NOT merge/change cards based on NAHRADA.

### HLAVNA_TP
- separate mechanism from NAHRADA
- current population effectively self-only
- related source function includes C_SKLAD_KARTA.ZmenPredajnyVariant and FLAGS_B position 41 logic
- no current multi-card variant group observed
- current business use remains non-blocking.

### NAHRADZA_KARTU
- directional relation to an older/replaced card is source-visible
- current only about 13 nonzero links
- do not infer automatic business replacement/merge semantics beyond the confirmed directional technical link.

## 9. Logistics master
### SKLAD_KARTA_LB
- 73 fields
- FK KOD_ID -> SKLAD_KARTA.ID
- PK RID
- UQ(SKRATKA, SKLAD)
- 2,151 rows / 1,846 cards
- 450 active rows/cards context snapshot
- levels: 0 Kus, 1 SubKartón, 2 Kartón, 3 Vrstva, 4 Paleta
- active relevant Tovar+Výrobok: 429/556 cards with active LB; 13 cards have >1 active LB
- each relevant card with active LB has exactly one FLAGS_B[1] main LB
- active relevant LB rows: 442
- EAN/level snapshot: piece 442, carton 428, subcarton 0, layer 1, pallet 9

### B_KOD_U
- 36 fields
- FK RID_SKLAD_KARTA_LB -> SKLAD_KARTA_LB.RID
- 4,929 rows; 4,907 linked
- no orphan LB in mapped snapshot
- linked KOD_ID matches LB
- source maintains codes for multiple packaging levels; reverse mutation exists
- FLAGS_B[2] is main code behavior; current main codes are piece EAN

Observed DQ candidates (not all are automatic business errors):
- 5 active LB missing exact piece B_KOD_U
- 4 active B_KOD_U unlinked to LB
- 1 linked to inactive LB
- 1 code not represented by LB level
- 14 main LB without main piece code
- 27 active codes shared across >1 KOD_ID

Root logistics fields are not a universal live roll-up of the packaging hierarchy.

## 10. Supplier / VAT / partner satellites
### SK_LOG_UDAJE
- 5,367 total, 1,723 active, 1,632 cards
- no root orphans in mapped snapshot
- current grain: KOD_ID + SKLAD_P + optional SARZA; current SARZA all NULL
- no active duplicate current natural grain
- contextual overrides of root KRAJINA_P / TYP_CENOVKY exist in API; current override population may be NULL

### SKLAD_DODAVATEL
- 118 active rows / 115 cards / 17 suppliers
- no active duplicate (KOD_ID, ID_DODAVATELA)
- root DOD_SK matches 102; 13 cards have root main supplier absent from satellite
- source procedure ZapisHlavnehoDodavatela may copy DOD_SK and DOD_KOD under conditions
- DOD_KOD, KOD_DOD and VYROBCA_KOD are NOT synonyms
- preferred business term for DOD_KOD: “kód dodávateľa”

### SKLAD_KARTA_FU
- 2,561 active rows / 912 cards
- warehouses observed: 45=910, 51=830, 48=812, 55=9
- SAME_AS_ROOT snapshot: 2,080 false / 481 true
- effective VAT may be warehouse/session specific; root UROVEN_DPH is not universal.

### SKLAD_PARTNER_KODY
- active 242 rows / 102 cards / 32 partners
- no duplicates on (KOD_ID, PARTNER, BALENIE) in snapshot
- (PARTNER, KOD_PARTNERA) is not globally unique
- DO NOT use ROWNUM=1 without the correct grain.

## 11. Lookup/reference closure
Confirmed used references in mapped lookup scope had zero orphans in the tested snapshot.
Examples include MENY, COL_SADZOBNIK, KALKUL_POLOZKY, VYROBCOVIA, SKLAD_CS, KRAJINY, B_USERS, STAVY_SK, OBCH_PARTNERI, ART_SKUPINY, OBCHODNE_ZNACKY and others defined by root FK metadata.

Important interpretation limits:
- VYROBCA currently mostly contains sentinel/technical values; do not treat as general manufacturer authority.
- lookup S_STAMP != 0 does not automatically invalidate an existing root reference.
- Oracle comments are technical clues, not sufficient business proof.

## 12. Allergens / typed notes
Current operational allergen authority is typed notes, not root FLAGS_A/ALERGENY.

Product-context relation:
SKLAD_KARTA.RID -> CIS_POZNAMKY.RID_V -> CIS_POZNAMKY.TYP -> CIS_POZNAMKY_TYPY.ID

- CIS_POZNAMKY is generic/polymorphic globally; the product RID relation is valid only in product-card context.
- active typed notes snapshot: 915 on 594 SKUs; 34 active types
- allergen branch snapshot: 574 active allergen note records on 265 SKUs
- direct allergen and cross-contamination are separate semantics and must stay separate
- user/business confirms these notes are actively used and feed downstream production/manufacturing warnings/reports
- exact manufacturing reader in Oracle source was not resolved; keep Manufacturing as explicit boundary

Legacy/dormant mechanism:
- C_SKLAD_KARTA.GetAlergen/GetAlergeny uses FLAGS_A + LATKY_ZLOZENIA.PORADIE
- LATKY_ZLOZENIA type 000426 contains 14 standard allergen categories
- current root FLAGS_A and ALERGENY are entirely NULL
- classify as implemented but current-unpopulated/dormant; do not call obsolete without proof.

Open note-type ambiguity:
- 00048 “Alergény z krízovej kontaminácie - orechy”
- 00052 “Alergény z krížovej kontaminácie - orechy”
User cannot confirm whether 00048 is legacy/replaced by 00052. Keep non-blocking TREBA OVERIŤ; no auto-clean rule.

## 13. Cost / recycling coefficients
Core objects:
- CIS_DU_O
- NAKL_KOEF
- SK_NAKL_POLOZKY
- IMP_MC_SK_NAKL_POL

NAKL_KOEF semantics from source:
- TYP_UPL 0 quantity, 1 volume, 2 weight, 3 purchase cost
- ZARADENIE 0 recycling, 1 electro, 2 hazardous, 3 other, 4 excise, 5 bonus, 6 deposit, 7 sugar
- TYP_KRAJINY is a 4-character applicability mask, NOT a country code

Registry snapshot:
- 48 coefficients, 47 active
- 4,488 active assignment references
- active assignments: 4,488; effective today: 4,487; one expired active assignment; no active/effective duplicate SKU+coefficient in tested snapshot

BOM auto process (MCCARTER.imp_SK_NAKL_POL_VYR):
- identifies finished products via executable INT_KOD prefix heuristic
- reads component mapping through BOM/structure
- uses component HMOTNOST_NETTO
- BOM quantity includes norm loss where defined
- DU7 controls recycle split; DU8 virgin, DU9 recycled
- supports CZ;SK token pairs, current token2 SK branch is dormant/mostly unused
- source deletes same product+NK_ID and inserts one row per component/token, which can overwrite instead of aggregate.

Confirmed DQ incidents:
- DQ-COEF-001: stale BOM-auto rows (101 product×coefficient groups / 42 products in PM07B)
- DQ-COEF-002: CRITICAL overwrite/no aggregation when multiple BOM components map to same NK_ID; 64 multi-component groups in PM07A
- DQ-COEF-003: stored vs current recompute mismatch
- DQ-COEF-004: missing stored auto coefficient where current mapping suggests one should exist (scope-sensitive)
- DQ-COEF-005: SK/CZ prefix naming is legacy/transitional; informational/warn, not jurisdiction truth
- DQ-COEF-006: report may include invalid/storned assignment in sugar/reporting branch due missing lifecycle filter

Coefficient quantity can include norm loss and is not automatically pure physical packed weight.

## 14. FLAGS[12] — reporting eligibility
Business meaning CONFIRMED:
SKLAD_KARTA.FLAGS position 12 = “Nezahŕňaj do prepočtu odpadov výrobkov”.

Typical business case: private-label/cofilling where another brand owner bears the waste-reporting responsibility.

Rules:
- FLAGS[12]=1 + cost/material coefficients is VALID and not a DQ defect.
- Do not infer private label/cofilling from product name or brand; the reporting switch in this scope is FLAGS[12].
- Current flag has no full historical valid-from history; historical eligibility cannot be reconstructed from current root alone.

## 15. Recyklačný fond SK/CZ — confirmed report defect
Dreamer user reports:
- Recyklačný fond SK: CRW_REPORTS.ID=101, ID_FORM_SQL=20130, runtime TLAC_NASTAVENIA=000146, RID_RPT=455230002
- Recyklačný fond CZ: CRW_REPORTS.ID=102, ID_FORM_SQL=20130, runtime TLAC_NASTAVENIA=000149, RID_RPT=455230003

Runtime SQL captured from TLAC_QUEUE proves:
- detail sections apply SUBSTR(SK.FLAGS,12,1)='0'
- final RF total does not apply this filter in both SK and CZ variants

SK Q2/2026 reconciliation:
- total without flag exclusion: 154.416745 t -> PDF 154.42 t
- total with FLAGS[12]=0: 150.787039 t -> approx. 150.79 t
- excluded difference: 3.629706 t
- 12 contributing cards; user business-validated all 12 as private-label/cofilling

Canonical incident:
- DQ-REPORT-001
- severity: CRITICAL
- status: POTVRDENÉ
- scope: Recyklačný fond SK + CZ report total logic
- fix belongs to report SQL, NOT to SKLAD_KARTA values or coefficients
- task has already been recorded for Miroslav Jánošík outside the catalog.

## 16. CIS_DU supplemental definitions
Relevant confirmed current definitions:
- DU1 Typ štítka SSCC
- DU4 WRIN
- DU5 Filter
- DU6 Týždne prognózy
- DU7 percent/recycled share
- DU8 auto coefficient mapping — virgin/non-recycled
- DU9 auto coefficient mapping — recycled
Other DU slots without active definition/population must not be assigned guessed meaning.

## 17. Mutation / source flow requirements
Materialize root insert/update/storno behavior and critical-field Mutation Matrix from approved trigger/package evidence.
Critical source facts include:
- root insert trigger defaults HLAVNA_TP=self, NAHRADA=self, SK_ID=ID, RID_OBJ=RID, USED=1, DATUM=SYSDATE and other technical defaults
- replication bypass exists for update/delete paths
- root storno cascades/stornos related B_KOD_U, SKLAD_KARTA_LB, SKLAD_DODAVATEL under confirmed source rules
- STAV->8 side effect into MCCARTER_PLAN.MC_UKONCENY_PREDAJ_SK
- C_SKLAD_KARTA contains source-visible maintenance APIs; only classify specific caller/writer roles when source proves them
- no scheduler/caller absence may be treated as proof that external/app scheduling does not exist.

## 18. Dependency / boundary contract
- Direct root dependency snapshot: 416 dependency rows / 414 objects
- C_SKLAD_KARTA is central API with large source dependency surface
- source-visible direct writers outside C_SKLAD_KARTA: 33
- static cross-schema ALL_DEPENDENCIES for root/API may be zero, but cross-schema synonyms/grants exist
- synonyms observed include MC_ST.SKLAD_KARTA and MC_WWW references to C_SKLAD_KARTA/SKLAD_KARTA
- grants/synonyms = ACCESS CAPABILITY / DEPENDENCY ONLY until runtime/source role is proven
- dynamic SQL and application runtime outside Oracle source are explicit system boundaries.

External SK->CZ synchronization:
- business/technical evidence confirms batch `prenosdatcz.bat`
- Windows Scheduler every two hours
- source SK -> target CZ; current description includes card creation/update and EAN/selected master attributes
- existing-card pairing described via internal code
- exact SQL/scripts/procedures are DATA GAP and must not be invented.

## 19. DO NOT ASSUME — mandatory
1. ID=SK_ID and RID=RID_OBJ are current observations, not immutable/cross-environment laws.
2. INT_KOD is currently unique in MC but design uniqueness is (INT_KOD,SKLAD).
3. USED=1 does not mean “in sale”; STAV and technical active state are separate.
4. N_STAMP is not creation/current-state/exit/last-update timestamp.
5. Current master attributes are not historical transaction truth.
6. NAHRADA is a confirmed technical group relation, but not a confirmed business substitution rule.
7. lookup S_STAMP nonzero does not automatically invalidate an existing root reference.
8. grants/synonyms/dependencies do not prove runtime reader/writer/caller roles.
9. missing logistics is not a universal error; scope by card type/use case.
10. VYROBCA is not general manufacturer authority.
11. selective history and SK_TEMP are not complete audit history.
12. no trigger ordering assumptions without source/DB evidence.
13. no absence-of-dependency/job claim proves no external/dynamic flow.
14. do not enforce NETTO<=gross or unit conversions until units are business-confirmed.
15. root logistics fields are not authoritative roll-up of all packaging levels.
16. process documents/proposals are not implementation unless separately evidenced.
17. INT_KOD prefixes are conventions, not taxonomy replacement.
18. coefficient values may include norm loss; not pure physical mass by default.
19. missing coefficient is not globally a DQ defect; scope matters.
20. TetraPak composite/breakdown can double count if layers are mixed; preserve provenance.
21. coefficient unit must not be inferred from label alone.
22. DU7/8/9 are supplemental mapped fields, not universal business taxonomy.
23. scheduler identity must not be inferred.
24. TYP_KRAJINY is applicability mask, not country code.
25. S_STAMP=0 assignment does not by itself prove effective-today semantics.
26. BOM DATUM_OD is generation/effective date, not necessarily origin date.
27. current assignment uniqueness observations are not physical UQ constraints unless metadata says so.
28. imp_SK_NAKL_POL_VYR INT_KOD prefix logic is executable heuristic, not universal business rule.
29. source supports dual CZ;SK mapping; current token2 use may be dormant.
30. SK_LOG_UDAJE overrides are contextual; root fields are not universal effective context.
31. supplier satellite is not assumed continuously synchronized with root.
32. TYP_T='00' is unresolved; do not classify with it.
33. partner code pair is not globally unique.
34. DU meanings are only those explicitly evidenced.
35. SK/CZ coefficient name prefixes are legacy/transitional, not jurisdiction keys.
36. reporting jurisdiction comes from transaction/partner/report context, not coefficient name.
37. product component weights are inputs; placed-on-market quantity is downstream/report-specific.
38. sold-minus-credit/report logic must use exact report/runtime contract where needed.
39. SKLAD_DODAVATEL.KOD_DOD != VYROBCA_KOD unless separately proven.
40. root VAT is not universal due SKLAD_KARTA_FU overrides.
41. BOM overwrite/stale defects are confirmed and must not be normalized away.
42. dynamic config variables can materially alter behavior.
43. a UI tab is not automatically one physical table.
44. inventory tabs are outside Product Master.
45. root FLAGS_A/ALERGENY are not current allergen authority.
46. LATKY_ZLOZENIA+FLAGS_A mechanism is dormant/current-unpopulated, not proven obsolete.
47. CIS_POZNAMKY is generic/polymorphic; product RID relation is context-specific.
48. typed note meaning comes from type dictionary.
49. FLAGS/FLAGS_B positional strings are not universally boolean.
50. FLAGS[12] is confirmed reporting exclusion; exact historical start is not fully reconstructable.
51. historical source comments are not runtime rules.
52. FLAGS[12]=1 + coefficients is valid.
53. current allergen authority is typed notes.
54. identify allergens by note-type dictionary, not free text alone.
55. not every note is an allergen.
56. manufacturing allergen use is business-confirmed; exact B2 reader unresolved and remains boundary.
57. do not absorb Manufacturing domain into Product Master.
58. do not equate ZS-NAKL-KOEF-ODPAD-PODM with FLAGS[12] implementation.
59. TOVAR_TYP.TYP_T join hypothesis was disproved; PM-10B2 also failed ID/tree resolution for current '00'.
60. UI “Nezadaná” does not disprove live/source-visible NAHRADA grouping.

## 20. Canonical DQ rules to materialize
At minimum:
- identity/uniqueness snapshot checks with dated semantics
- root lookup orphan checks
- root-vs-satellite supplier divergence diagnostic
- SKLAD_KARTA_FU VAT context divergence diagnostic
- packaging/EAN anomalies with scope and non-error caveats
- typed-note allergen coverage and duplicate/type ambiguity diagnostics
- DQ-COEF-001 through DQ-COEF-006
- DQ-REPORT-001 Recyklačný fond SK/CZ footer eligibility defect
- unresolved TYP_T current '00' as warning/non-blocking legacy condition, not cleanup target
- NAHRADA group diagnostics only; no auto-remediation.

## 21. Diagnostic playbooks to materialize
At minimum:
1. “Nesedí stav skladovej karty” -> compare USED, STAV, S_STAMP, relevant source flow.
2. “Chýba / nesedí EAN alebo balenie” -> root -> SKLAD_KARTA_LB -> B_KOD_U, preserve level/fan-out.
3. “Nesedí dodávateľský kód” -> root DOD_SK/DOD_KOD vs SKLAD_DODAVATEL.KOD_DOD/VYROBCA_KOD, no synonym assumption.
4. “Nesedí DPH” -> root vs SKLAD_KARTA_FU warehouse/context.
5. “Nesedia alergény” -> typed notes + type dictionary; root flags are not current authority; Manufacturing boundary if downstream warning differs.
6. “Nesedia nákladové/recyklačné koeficienty” -> current assignments, lifecycle/effective date, BOM recompute, provenance, DQ-COEF rules.
7. “Recyklačný fond total nesedí detailu” -> runtime/report eligibility, FLAGS[12], DQ-REPORT-001.
8. “Historický report nesedí dnešnej karte” -> current master vs transaction snapshot/history boundary.
9. “NAHRADA vyzerá nesprávne” -> show anchor/members and source-visible grouping; do not infer business substitutability.

## 22. Canonical read-only SQL to materialize
Codex must create a safe SQL registry and files for at least:
- root identity lookup by ID / SK_ID / RID / INT_KOD
- root current state view (USED/STAV/S_STAMP)
- root lookup resolution without fan-out
- logistics hierarchy SKLAD_KARTA -> LB -> B_KOD_U
- packaging/EAN anomaly diagnostics
- supplier root-vs-satellite comparison
- VAT/root-vs-FU context comparison
- partner-code grain check
- allergen typed-note current view
- allergen direct vs cross-contamination view
- coefficient current/effective assignment view
- BOM current recompute vs stored comparison
- DQ-COEF-001..006 diagnostics
- FLAGS[12] current card shortlist
- Recyklačný fond reconciliation diagnostic using report-equivalent logic with explicit interpretation limits
- NAHRADA group + member diagnostic
- TYP_T unresolved current diagnostic
- dependency/source trace registry queries

Every SQL file must state result grain, fan-out risk/limit, what it proves and what it does not prove. Conservative Oracle syntax only; read-only.

## 23. Approved evidence / Mapping Pack families
Use approved evidence from this mapping session, including but not limited to:
- MP-01 discovery / root metadata
- MP-02 live profile and self-reference profiles
- MP-03 source/mutation
- MP-04 dependency/lookup profiling
- MP-05 edge/validation
- PM04I lookup mapping
- PM06A/PM06C cost/coefficient mapping and recompute audit
- PM07A/PM07B/PM07C coefficient DQ closure
- PM08/PM09 allergen/typed-note/flags mapping
- PM09E waste flag12 source
- PM09F remaining root source closure
- PM10A current waste reporting condition
- PM10B2 product type current resolution
- PM10C typed note API downstream callers
- PM10F replacement equivalence groups
- PM10F2 replacement equivalence active members
- PM11A–PM11N report discovery/runtime trace
- PM11P SK flag12 reconciliation
- PM11S1/PM11S2 CZ runtime/footer validation
- Dreamer screenshots for Recyklačný fond SK/CZ parameter flow and PDF output
- Project/process documents for stock-card process and cost coefficient business process

Evidence classes must remain A/B/B2/C/D/E per mapping standard. Do not upgrade E/hypothesis into materialized fact.

## 24. Non-blocking backlog to materialize
1. NAHRADA exact business meaning / runtime use — TREBA OVERIŤ with KASO; blocking=false.
2. TYP_T='00' legacy origin / intended dictionary — TREBA OVERIŤ; blocking=false.
3. allergen type 00048 vs 00052 legacy/replacement relation — TREBA OVERIŤ; blocking=false.
4. exact Oracle-visible Manufacturing allergen reader — TREBA OVERIŤ / boundary; blocking=false.
5. canonical units for HMOTNOST / NETTO / OBJEM — TREBA OVERIŤ with business/KASO; do not enforce unit-based DQ until confirmed; blocking=false.
6. exact implementation contents of SK->CZ prenosdatcz.bat and called SQL/scripts — DATA GAP; blocking=false.
7. full historical reconstruction of arbitrary master fields — DATA GAP by current evidence; blocking=false.

## 25. Acceptance baseline / tests
Codex must encode dated expectations where appropriate and avoid treating snapshot counts as eternal invariants.

Structural acceptance:
- 169 root fields materialized losslessly
- root PK/UQ/FK/CHECK/index inventory represented
- 21 enabled direct root triggers represented
- 32 outbound root FKs represented
- relationship/join contracts include cardinality/fan-out limits
- direct master satellites and typed-note/coefficient relations represented
- blocking backlog = 0

Snapshot acceptance (2026-09-14 unless otherwise stated):
- SKLAD_KARTA rows = 7,429
- current ID=SK_ID 100%
- current RID=RID_OBJ 100%
- lookup profile used refs had zero orphans for the tested scope
- NAHRADA PM-10F counts retained as dated evidence, not constraints
- PM11P SK report reconciliation retained as dated incident evidence

Semantic acceptance:
- USED and STAV remain separate dimensions
- current master vs history boundary explicit
- root allergen fields not marked current authority
- typed notes marked current allergen authority
- FLAGS[12] business/reporting rule materialized
- DQ-REPORT-001 present with SK and CZ scope
- NAHRADA business substitutability NOT asserted
- TYP_T current '00' NOT given guessed meaning
- SK/CZ coefficient name prefixes NOT used as jurisdiction truth
- grants/synonyms/dependencies not mislabeled as runtime roles without source.

Repository validation:
- python tools/validate_catalog.py
- python -m unittest discover -s tools -p 'test_*.py' -v
- create a domain-specific acceptance gate for skladove-karty following existing domain patterns
- SQL safety lint / read-only checks
- unresolved/duplicate/evidence-reference checks
- semantic-loss checks
- PR diff focused only on this domain/evidence/SQL/tooling required for the domain
- merge only with green CI and verify main after merge.

## 26. Requested repository actions for Codex
1. Read AGENTS.md, docs/mapping-standard.md, docs/publication-standard.md and this handoff.
2. Inspect an AGENT-READY reference domain (warehouse/vydajky) for canonical split/schema patterns.
3. Create feature branch.
4. Create catalog/master/skladove-karty/ canonical domain files, partitioning large registries as required by existing schemas.
5. Materialize all 169 fields with Oracle names, aliases, datatypes/null/default/comment, status/evidence.
6. Materialize constraints/indexes/relationships/value domains/temporal/mutations/flows/dependencies/DQ/DO NOT ASSUME/playbooks/backlog/revisions/oracle entities.
7. Create evidence manifest(s) under evidence/manifests/; retain only required SNAPSHOT_CRITICAL files under evidence/snapshots/ with checksum rules.
8. Create canonical diagnostic SQL under sql/diagnostic/skladove-karty/ and SQL registry entries.
9. Add domain-specific acceptance gate/tests.
10. Run validators/tests/lints and resolve only engineering/schema consistency issues. If a semantic question appears, return HANDOFF BLOCKED rather than guessing.
11. Open focused PR. Do not generate/commit DOCX/PDF/viewer yet.
12. After green review/merge, verify main.

## 27. Change / revision note
Initial canonical materialization of the Product Master domain from evidence-first MC mapping closure completed 2026-09-15.
Breaking change: false (new domain; no prior canonical Product Master contract exists in main).
Future changes to grain, identity, canonical alias, JOIN key, business meaning, source-of-truth or temporal semantics require explicit revalidation and revision history.

## 28. Handoff decision
READY FOR CODEX HANDOFF

Semantic mapping is closed for the declared Product Master scope. Codex owns repository materialization/validation only and must not add business meaning beyond this handoff and cited evidence.


## 29. Post-closure MC revalidation 2026-09-16 — STAV 8 / Ukončený predaj forecast reset

### Evidence delta
Approved new MC B2 evidence: `PM-12A — end of sale forecast reset current source.xlsx`, extracted from current `ALL_SOURCE` / `ALL_TRIGGERS` / `ALL_OBJECTS`. This delta supersedes the earlier unresolved defect description for the lock interaction.

### Confirmed current MC flow
1. `MC.T_SKLAD_KARTA_STAV_AFTER_MC` is an enabled row trigger on `MC.SKLAD_KARTA`, `AFTER UPDATE OF STAV`. Replication sessions return early through `C_Session.GetReplikacia`.
2. On the transition `:OLD.STAV <> 8 AND :NEW.STAV = 8`, the trigger calls `MCCARTER_PLAN.MC_UKONCENY_PREDAJ_SK(:NEW.ID)`.
3. `MC.MCCARTER_PLAN.MC_UKONCENY_PREDAJ_SK` computes the current week-period code and updates future/current forecast rows in `OBCH_PL_O` for the SKU. It sets `PLAN_POCET2 = 0` and simultaneously replaces `POZN` with text beginning `Ukončený predaj`, including the current date and original planned quantity. Scope is `OBCH_PL_L.TYP_PLANU in (OPTyp_Prognoza, OPTyp_PrognPartn)`, matching `KOD_ID`, from the current week-period forward.
4. `MC.T_OBCH_PL_LOCK_MC` is an enabled row trigger on `MC.OBCH_PL_O`, `AFTER INSERT OR UPDATE OF PLAN_POCET2`. For ordinary updates it still prevents a changed `PLAN_POCET2` on a locked row where `BITAND(:NEW.STAV,2)=2`.
5. The current MC trigger contains a dedicated exception before the lock error:
   - if `POZN` changed and `:NEW.POZN LIKE '%Ukončený predaj%'`, the trigger executes `NULL` and does not raise the lock error.
6. Therefore the system-driven STAV=8 flow can zero `PLAN_POCET2` even in the locked operative period, while the normal lock remains active for ordinary/user changes. Existing forecast-transfer exceptions based on `(+%)` and `(-%)` notes remain unchanged. Insert-time protection also remains unchanged.

### Change localization
Current MC object timestamps from PM-12A localize the deployed change to the lock trigger:
- `MC.T_OBCH_PL_LOCK_MC` LAST_DDL_TIME = `2026-09-16 09:39:59`.
- `MC.T_SKLAD_KARTA_STAV_AFTER_MC` LAST_DDL_TIME = `2026-08-16 10:28:27`.
- `MC.MCCARTER_PLAN` package body LAST_DDL_TIME = `2026-08-16 10:35:33`.

This proves the current MC fix was implemented in `T_OBCH_PL_LOCK_MC`; the STAV=8 trigger and `MC_UKONCENY_PREDAJ_SK` procedure were not changed as part of this deployment. TEST/MCCZ source visible in the same export is auxiliary only and must not be treated as MC authority.

### Resolved defect / canonical status
Status: `POTVRDENÉ — VYRIEŠENÉ` for MC as of 2026-09-16.

Old defect: the STAV=8 procedure attempted to zero future `OBCH_PL_O.PLAN_POCET2`, but `T_OBCH_PL_LOCK_MC` interpreted the system update like an ordinary edit and raised the locked-period error.

Resolved behavior: `T_OBCH_PL_LOCK_MC` now recognizes the specific system update by the simultaneous change of `POZN` to the `Ukončený predaj` marker and bypasses only that lock guard. Standard lock behavior remains in place for other changes.

### Mutation Matrix delta
`SKLAD_KARTA.STAV: !=8 -> 8` -> `T_SKLAD_KARTA_STAV_AFTER_MC` -> replication guard -> `MCCARTER_PLAN.MC_UKONCENY_PREDAJ_SK(SK.ID)` -> `OBCH_PL_O.PLAN_POCET2=0` + `POZN='Ukončený predaj ... (pôvodne: ...)'` -> `T_OBCH_PL_LOCK_MC` detects the dedicated note marker -> lock bypass only for this system flow -> update succeeds.

### DO NOT ASSUME delta
- Do not describe the new mechanism as a global lock bypass. The bypass is conditional on the simultaneous note mutation matching `Ukončený predaj`.
- Do not infer that `STAV` lock is removed; ordinary `PLAN_POCET2` updates on locked rows are still rejected.
- Do not remove the `POZN` mutation from the procedure contract: it is now part of the executable bypass contract.
- Do not generalize TEST/MCCZ behavior to MC without separate validation.

### Codex acceptance delta
Materialize this flow as confirmed B2 evidence in the Product Master mutation/source-flow contract. Add an acceptance assertion that the STAV=8 system flow has an explicit `T_OBCH_PL_LOCK_MC` exception, while the generic `BITAND(STAV,2)=2` lock guard remains documented for ordinary updates. Record this as a non-breaking semantic revision dated 2026-09-16.

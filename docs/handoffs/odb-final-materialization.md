# ODB final materialization — 2026-09-15 evidence

Continuation of f0737962666243de40c8bf211fc877f567f713dd on the existing
feat/sales-obchodne-pripady-v1.2 branch, incorporating current main
8230ccd8fd177f1a4edd9eaae35f3ea86a569283 without resetting either branch.

All 13 supplied SHA256SUMS entries verified; nine raw XLSX workbooks and two
negative audits read offline. The supplied directory was already extracted.
No new Oracle export or database execution occurred. MC remains authoritative.

## Materialization

- OBJ_ODB_L/O: 79/44 fields; raw defaults, comments, datatype/precision/scale.
- Constraints: 85/45 (130 total), including 26/8 FK, 1/1 PK, 2/0 UNIQUE,
  and 56/36 CHECK, preserving raw expressions and dictionary states.
- Indexes: 21/13 (34 total). Physical X_OBJODBO_XML35 spelling reconciled with
  the original stable ID; full domain-index expression stays nonblocking.
- 50 triggers and three package spec/body pairs; D_OBJ_ODB_L_B is the approved
  additive supporting direct writer. 50 flows, 18 preserved grouped mutations
  and six source-proven package/table mutation records; 12 relationships.
- Exact-node offline BFS: 55 logical / 58 graph seeds. Inbound 285 nodes,
  673 edges, max node depth 3, 581 direct. Outbound 477 nodes, 2515 edges,
  max node depth 4, 889 direct. Cyclic/back edge traversal depth can reach 5;
  this is distinct from shortest node depth and is not truncated.
- MC lexical source references: 4515 occurrences / 145 source objects /
  595 normalized members (300 L, 59 L_B, 236 O). Occurrences 2629/185/1701.
  Exact source text and member spelling remain separate from normalization.
- 71 grants / 9 synonyms are ACCESS CAPABILITY only.
- ALL_JOBS and ALL_SCHEDULER_JOBS direct-name audits both zero, within their
  explicit predicates. Wrappers, programs/chains, dynamic/external runtime
  remain outside the proven scope.
- Blocking backlog zero; nine original nonblocking gaps preserved. The seven
  Phase A blocking entries remain in retained snapshot history.
- Existing VYD ODB IDs and approved business semantics/SQL remain unchanged.

## Verification before PR

Validator: PASS, 438 YAML documents, unresolved references 0, duplicate global
IDs 0. Full unittest discovery: 113 tests passed without skips or failures,
including ODB acceptance, SQL safety and publication tests. All four publication
families pass deterministic generation checks. Re-running final materialization
from the read-only bundle reproduces canonical/evidence files byte-for-byte.

DOCX was rendered with LibreOffice for visual review; PDF was rendered separately.
All pages reviewed in contact sheets, with long PDF table rows split at existing
newlines to avoid page overflow. Publications preserve complete business values
and SQL; large graph/API/entity registries are explicitly indexed summaries.
The manifest records canonical input digest and exact artifact SHA-256 values.

Maturity is AGENT-READY, documentation version 1.2, breaking_change=false.
Exhaustive means supplied source-visible static MC closure, never all runtime.
CI and merge remain separate remote gates; this report does not predeclare them.

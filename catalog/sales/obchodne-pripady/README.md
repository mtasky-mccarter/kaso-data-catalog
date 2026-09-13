# Obchodné prípady — engineering scaffold

Phase A update (2026-09-13): the handoff is received and retained in
`docs/handoffs/odb-phase-a.txt`. Its target is DIAGNOSTIC-GRADE, version 1.2,
breaking_change=false; publication and merge remain forbidden. Referenced source
files are still missing. See `docs/handoffs/odb-phase-a-intake.md` and updated
`backlog.yaml` for current blockers. The sections below describe the original
scaffold baseline; statements about an absent handoff are superseded by this update.

HANDOFF BLOCKED. This is a DISCOVERY scaffold, not an approved v1.2 domain contract.
All files use existing schema v1.0 record kinds. No schema changes are required.
`HANDOFF BLOCKED` is explanatory text; machine status remains `DATA GAP` /
`TREBA OVERIŤ`, maturity `DISCOVERY`, and backlog `blocking: true`.

`records: []` and zero summary values mean zero materialized records, NOT a
verified empty Oracle population, complete inventory, or absence of dependencies.
Optional business attributes are omitted rather than filled with invented meanings.
No source NULLs have been imported. Future parsers must preserve source null, raw
literal strings, leading zeroes and Oracle spelling without guessing aliases.

## A. Proposed and implemented tree

```text
catalog/sales/obchodne-pripady/
  README.md
  contract.yaml
  object-obj_odb_l.yaml
  fields-obj_odb_l.yaml
  object-obj_odb_o.yaml
  fields-obj_odb_o.yaml
  constraints.yaml
  indexes.yaml
  relationships.yaml
  value-domains.yaml
  flows.yaml
  mutations.yaml
  temporal.yaml
  data-quality.yaml
  do-not-assume.yaml
  playbooks.yaml
  backlog.yaml
  revisions.yaml
  oracle-entities.yaml
  sql-registry.yaml
  dependencies.yaml
  dependency-direct-edges.yaml
  dependency-closure-edges.yaml
  dependency-closure-nodes.yaml
  api-references.yaml
evidence/manifests/odb/
  README.md
sql/diagnostic/obchodne-pripady/
  README.md
tools/
  odb_scaffold.py
  test_odb_acceptance.py
  test_odb_sql_safety.py
  generate_odb_publication.py
  test_odb_publication.py
```

Stable engineering prefix: `odb`; domain slug: `obchodne-pripady`.
Domain ID: `odb.contract.obchodne_pripady`; object IDs: `mc.object.obj_odb_l`
and `mc.object.obj_odb_o`. These are proposed IDs on the feature branch.
Schema version `1.0` is distinct from the requested documentation version `1.2`.
Revisions remain empty until an approved revision and breaking-change decision arrive.

## B. Main audit and differences from VYD/CP

Baseline: `a4b78cba678cfd605ebc7440025f5f8edd2635c0` (main inspected 2026-09-13).
`catalog/sales/` contains only `.gitkeep` at that baseline: no canonical ODB contract.
The mapping standard references the human-readable obchodné prípady v1.2 document;
that reference does not supply its content or constitute a materialization handoff.

Existing VYD technical boundary records must remain untouched:

| Oracle name | Existing boundary ID |
| --- | --- |
| MC.OBJ_ODB_L | `vyd.oracle.f1dfff357c6da5d31924380f` |
| MC.OBJ_ODB_O | `vyd.oracle.c05d6994b969d9ce00ed3039` |

Source: `catalog/warehouse/vydajky/oracle-entities.yaml` at baseline. Both are
TABLE references, `TECHNICKY ZNÁME`, `boundary_only: true`, with VYD evidence.
Only those existing technical names/type and user-requested scope are reflected
in object shells. No field inventory, business meaning or roles are copied.
The new objects deliberately remain `TREBA OVERIŤ` with no claimed accepted evidence.
Handoff must reconcile existing boundary/field IDs before changing any cross-domain refs.

- Same contract/object/field/register organization as VYD/CP; two requested objects.
- VYD uses separate direct edges, closure edges and closure nodes; CP keeps closure
  in `dependency-closure.yaml` with kind `dependency-edges`. ODB follows the VYD
  split without inventing a new closure kind. Nodes and edges are not interchangeable.
- API uses existing `api-references`. Split into `api-references-partNN.yaml` only
  when actual approved volume requires it; no invented packages, caller counts or hits.
- VYD/CP have populated accepted evidence, production acceptance assertions and
  canonical SQL. ODB has explicit blocking gaps and empty registers.
- No accepted evidence manifest is fabricated. Proposed manifest filenames below
  are not claims that source exports exist.
- ODB tests guard the scaffold phase only. They must be replaced/extended by
  handoff-derived expected counts and semantic-loss assertions at materialization.
- The publication entrypoint intentionally exits 2 without output, including
  `--check`; it is a reserved interface, not an implemented document renderer.
  ODB is not registered in `generate_publication.py all` until publication is approved.
- `odb_scaffold.py` reuses the strict YAML loader and bundle validator; no raw XLSX
  parser is guessed before actual worksheets, columns and null conventions arrive.

## C. Required input files

Exact source filenames and tab layouts must come from the handoff. Logical inputs:

1. `READY FOR CODEX HANDOFF` package with all fields required by AGENTS.md and
   mapping-standard section 18; requested target maturity and revision decision.
2. Approved `KASO Data Catalog - Technical & Diagnostic Reference - obchodné prípady v1.2`
   source document, plus explicit approved record/semantic mapping and evidence links.
3. Complete MC physical exports for both objects: object types, columns/ordinals,
   datatype/null/default/comment, constraints with ordered columns and validation
   states, indexes with ordered columns/expressions. Include completeness counts.
4. Approved JOIN/cardinality/fan-out/identity tests and value/DQ profiles with
   snapshot dates; approved aliases, grain, temporal and source-of-truth rules.
5. Approved source extracts and interpretation for flows/mutations; dependency
   direct edges, closure edges and unique nodes with direction/depth; API member
   references with caller identity, raw member, hit lines and counts.
6. Approved synonym/grant/job/cross-schema and external-runtime boundaries;
   reconciliation map to existing VYD/CP IDs, without automatic role inference.
7. Evidence inventory: exact filenames, evidence class, review/approval, source
   query/client, snapshot date, retention, checksums and retained critical snapshots.
8. Approved standalone read-only `.sql` files and registry metadata: bind parameters,
   result grain, fan-out risk, proves/does-not-prove, compatibility, playbook linkage.
9. Expected record counts and lossless acceptance assertions; blocking/nonblocking
   backlog, DO NOT ASSUME, revision note, breaking-change flag, publication scope.

Proposed evidence manifest names after approval: `accepted.yaml`, `columns.yaml`,
`physical.yaml`, `profiles.yaml`, `source.yaml`, `dependencies.yaml`, `closure.yaml`,
`api-references.yaml`, `boundaries.yaml`. Use `kind: evidence-manifest` and stable
`odb.evidence.*` IDs. Actual files/splits/classes follow supplied evidence, not this list.

## D. HANDOFF BLOCKED

Seven machine-readable blocking entries in `backlog.yaml` cover handoff, physical
metadata, semantics, source/dependencies/API, evidence, diagnostics and acceptance.
No supplied package closes them. Unavailable exports are not marked nonblocking.
Production materialization, semantic acceptance and publication remain blocked.
Scaffold preparation itself is authorized and can be reviewed independently.

## Validation and next engineering step

```sh
python tools/validate_catalog.py catalog/sales/obchodne-pripady
python -m unittest discover -s tools -p 'test_odb_*.py' -v
```

The first command checks schema/IDs/refs. The tests verify that unapproved material
and publication cannot silently enter this scaffold. Neither is semantic acceptance.
After approved input arrives, add format-specific parsing, preserve raw values and
stable IDs, materialize records, replace empty-registry assertions with approved
counts, and apply CP/VYD SELECT-only safety plus SQL/registry coverage checks.
Do not infer side-effect freedom of called functions from the SELECT keyword alone.
Server version remains unknown unless separately evidenced.

Before merge run the full repository validator and unittest suite in a complete
checkout. When publication is implemented, route committed outputs through
`tools/generate_publication.py obchodne-pripady`, read version from approved revisions,
and use `generated/obchodne-pripady/KASO Data Catalog - Technical & Diagnostic Reference - obchodné prípady v<version>`
for matching DOCX/PDF/manifest files. Verify provenance, SHA-256 and deterministic output.

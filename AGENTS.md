# KASO Data Catalog — Repository Rules

This repository is the canonical machine-readable source of truth for the KASO Data Catalog. Generated DOCX/PDF/viewer outputs are publications, not the authority.

## Evidence-first
- Do not invent Oracle objects, columns, datatypes, JOIN keys, FKs, lookup meanings, flags, formulas, lifecycle semantics or writer/reader/caller roles.
- Slovak production `OWNER=MC` is authoritative for the MC contract. MCCZ, TEST and TESTCZ require separate validation.
- Oracle comments are technical clues, not business truth.
- POTVRDENÉ facts require accepted evidence and must not rely only on evidence class E.
- A/B/B2/C/D/E evidence classes retain the meaning defined by the Mapping Standard.

## Read-only database work
- Mapping and diagnostic SQL must be read-only.
- SQL Navigator 5.5.4.847 is the declared client. Oracle server version is unknown unless separately evidenced.
- Prefer conservative Oracle syntax and ALL_* dictionary views defined by the Mapping Standard.
- Never generate production DML/DDL or data-changing PL/SQL as a catalog diagnostic action.

## Canonical structure
- `main` is the canonical accepted catalog state. Feature branches and pull requests are proposed changes.
- Domain contracts live under `catalog/<domain>/...`.
- Canonical evidence manifests live under `evidence/manifests/`; do not place competing YAML manifests directly under `evidence/`.
- Retained SNAPSHOT_CRITICAL evidence lives under `evidence/snapshots/` and must satisfy checksum rules.
- Canonical read-only SQL lives under `sql/diagnostic/` or `sql/mapping-packs/`.
- Generated publications/viewers live under `generated/` and must not be edited as the source of truth.
- JSON Schemas live under `schema/`; synthetic fixtures under `examples/schema-smoke-test/`.

## Contract semantics
- Preserve Oracle names exactly. Canonical aliases are English ASCII `snake_case`.
- Preserve RID/code values as text when leading zeroes are possible.
- Preserve source null as YAML `null`; do not substitute a display label.
- Separate RAW CURRENT, STORED SNAPSHOT, DERIVED CURRENT, TRANSITION STAMP, LAST UPDATE, SELECTIVE HISTORY and DATA GAP.
- Grant/synonym means access capability, not runtime flow.
- Compile-time dependency means dependency only until source proves reader/writer/caller behavior.
- Runtime or dynamic SQL outside Oracle-visible source is an explicit system boundary, not something to infer.

## Responsibility split
- ChatGPT / mapping orchestrator owns semantic mapping, evidence interpretation, blocking-backlog closure and the decision that a mapping is ready for engineering materialization.
- Codex / catalog engineer owns repository changes, parsing, machine-readable materialization, consistency checks, dependency graph tooling, lint, tests, PRs and generated artifacts.
- Codex must not create or upgrade business meaning, source-of-truth claims, JOIN correctness or writer/reader/caller roles without evidence already approved in the handoff.

## READY FOR CODEX HANDOFF
Codex should perform production catalog materialization only after ChatGPT supplies a `READY FOR CODEX HANDOFF` package. The handoff must identify at least:
- domain and Oracle objects;
- target maturity and authoritative environment;
- canonical repository path and existing canonical references;
- approved evidence / Mapping Packs;
- confirmed semantic contract, critical JOIN/fan-out rules and temporal/source-of-truth rules;
- mutation/dependency boundaries and DO NOT ASSUME rules;
- blocking backlog and non-blocking gaps;
- canonical SQL to materialize;
- requested repository/publication actions;
- acceptance tests / expected counts;
- breaking-change flag and revision note.

If required evidence is missing, the handoff conflicts with `main`, or business meaning is ambiguous, do not guess. Return the specific item as `HANDOFF BLOCKED` for ChatGPT/business review.

## Codex engineering workflow
1. Read this `AGENTS.md`, `docs/mapping-standard.md`, the handoff package and the existing domain contract in `main`.
2. Work on a feature branch; do not bypass review by silently changing canonical `main`.
3. Materialize only approved facts into catalog YAML, evidence manifests and canonical SQL.
4. Preserve stable IDs and revision/change-management rules; mark breaking changes explicitly.
5. Run the validator, generic tests, relevant domain acceptance gate and SQL safety lint.
6. Check unresolved references, duplicate IDs, evidence requirements and semantic-loss assertions.
7. Prepare a focused PR containing only intended changes and explicit system/domain boundaries.
8. Merge only with green CI and a clean diff; verify the `main` workflow after merge.
9. Generate DOCX/PDF/viewer outputs only from the canonical layer when a generator exists.

## Change management
- Do not silently overwrite a confirmed fact. Revalidate conflicts and record revisions.
- Changes to canonical alias, grain, JOIN key or business meaning are breaking changes unless proven otherwise.
- Population observations carry snapshot dates.
- Deprecated/unsafe fields remain traceable and are marked rather than erased.

## Validation
Before merging a catalog change:
1. Run `python tools/validate_catalog.py`.
2. Run `python -m unittest discover -s tools -p 'test_*.py' -v`.
3. For a real mapped domain, pass its domain-specific acceptance gate in addition to generic schema tests.
4. Keep blocking backlog empty before claiming AGENT-READY.
5. Confirm the PR diff contains only intended schema/catalog/evidence/SQL/tooling changes.
6. After merge, confirm the resulting `main` workflow is green.

Structural validation never substitutes for Oracle/business evidence. Tests guard lossless representation and repository invariants; they do not manufacture business truth.
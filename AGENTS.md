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
- Generated publications/viewers live under `generated/<publication-slug>/` and must not be edited as the source of truth.
- JSON Schemas live under `schema/`; synthetic fixtures under `examples/schema-smoke-test/`.

## Generated publication naming and layout
- Follow `docs/publication-standard.md` for every committed DOCX/PDF/viewer publication.
- Every document family gets one stable version-independent ASCII kebab-case folder directly under `generated/`, for example `generated/cestovne-prikazy/` or `generated/vydajky/`.
- Do not commit generated DOCX, PDF or publication manifest files directly under the root `generated/` directory.
- Technical & Diagnostic Reference filenames must use exactly: `KASO Data Catalog - Technical & Diagnostic Reference - <subject_sk> v<documentation_version>` plus the appropriate extension.
- `<subject_sk>` is the approved Slovak human-readable document subject and preserves Slovak diacritics.
- `<documentation_version>` comes from the current approved canonical domain revision/documentation version. Do not invent a separate publication version.
- DOCX, PDF and `.manifest.yaml` for the same publication use the same basename and live in the same publication folder.
- Manifest artifact paths must reference the exact repository-relative generated paths and their SHA-256 values.
- For committed canonical publications use `python tools/generate_publication.py <publication-slug>` or `python tools/generate_publication.py all`. Domain-specific generators are implementation details and may emit temporary intermediate filenames only.

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

## Codex Lean Execution v3
`docs/codex-execution-standard-v3.md` is the normative engineering-context optimization for Codex work. It changes how context is loaded and validated; it does not weaken the Mapping Standard or evidence requirements.

Core rules:
- Repository state is persistent memory; the chat prompt is a command, not a duplicate specification.
- Required first reads are this `AGENTS.md`, the approved machine-readable handoff, the existing target domain contract, and the nearest applicable nested `AGENTS.md` if present.
- Read `docs/mapping-standard.md` in full only when the task changes semantic mapping rules, record semantics, or the handoff is missing/ambiguous. Otherwise use the handoff as the approved semantic boundary.
- Read `docs/publication-standard.md` only when publication work is enabled by the handoff or a publication test fails.
- After handoff integrity passes, do not rediscover approved counts, paths, IDs or invariants by broad repository search. Search only to resolve a conflict, missing reference or failed validation.
- Raw XLSX/source/dependency evidence should be processed by deterministic tooling where available. Do not stream whole raw datasets or giant generated YAML registries into model context when a parser/summary can answer the engineering question.
- Start with domain-scoped tests and compact summaries. Run the full repository validator/regression only after domain gates are green and again only if subsequent changes could invalidate the final result.
- For successful commands retain only exit status and concise summary. Inspect full logs/patches only for failures or semantically relevant diffs.
- Start review with changed filenames and `git diff --stat`; read full patches only for files that require inspection.
- Do not inspect unrelated domains unless a declared cross-domain reference fails or the handoff explicitly requests comparison.
- A committed milestone is a context boundary. Prefer a fresh Codex thread for the next substantial phase, using repository state plus a short resume prompt, instead of carrying a long prior tool-call history.

Canonical handoff template: `docs/handoffs/codex-handoff.template.yaml`.
Validate a completed handoff with:
`python tools/check_codex_handoff.py <handoff.yaml> --summary`.

## READY FOR CODEX HANDOFF
Codex should perform production catalog materialization only after ChatGPT supplies a `READY FOR CODEX HANDOFF` package. Prefer a machine-readable YAML handoff derived from `docs/handoffs/codex-handoff.template.yaml`; prose may accompany it but must not be the only authoritative engineering instruction.

The handoff must identify at least:
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
1. Read this `AGENTS.md`, the approved machine-readable handoff, the existing target domain contract, and any nearer nested `AGENTS.md`. Apply the v3 context-loading rules above instead of automatically reading every long standard.
2. Validate the handoff and evidence integrity before materialization. Treat a validated handoff as the semantic boundary; do not redo discovery that ChatGPT already closed.
3. Work on a feature branch; do not bypass review by silently changing canonical `main`.
4. Materialize only approved facts into catalog YAML, evidence manifests and canonical SQL. Prefer deterministic parsers/materializers for large evidence bundles and dependency graphs.
5. Preserve stable IDs and revision/change-management rules; mark breaking changes explicitly.
6. Run domain parser/acceptance/SQL-safety tests first. Inspect only failing details until the domain gate is green.
7. Check unresolved references, duplicate IDs, evidence requirements and semantic-loss assertions using compact machine summaries where available.
8. Run the full repository validator/unittest suite and publication `--check` only after the domain gate is green and the intended diff is stable.
9. Prepare a focused PR containing only intended changes and explicit system/domain boundaries. Review filenames/stat first, then only relevant full patches.
10. Merge only with green CI and a clean diff; verify the `main` workflow after merge.
11. Generate DOCX/PDF/viewer outputs only from the canonical layer when the handoff enables publication, and enforce the generated publication naming/layout standard.

## Change management
- Do not silently overwrite a confirmed fact. Revalidate conflicts and record revisions.
- Changes to canonical alias, grain, JOIN key or business meaning are breaking changes unless proven otherwise.
- Population observations carry snapshot dates.
- Deprecated/unsafe fields remain traceable and are marked rather than erased.
- Publication folder/filename normalization alone is a repository/publication change, not a semantic contract change.

## Validation
Before merging a catalog change:
1. Run `python tools/validate_catalog.py`.
2. Run `python -m unittest discover -s tools -p 'test_*.py' -v`.
3. For a real mapped domain, pass its domain-specific acceptance gate in addition to generic schema tests.
4. Keep blocking backlog empty before claiming AGENT-READY.
5. Confirm the PR diff contains only intended schema/catalog/evidence/SQL/tooling/publication changes.
6. For publication changes, run `python tools/generate_publication.py all --check` and verify folder/filename rules.
7. After merge, confirm the resulting `main` workflow is green.

Structural validation never substitutes for Oracle/business evidence. Tests guard lossless representation and repository invariants; they do not manufacture business truth.

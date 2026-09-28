# Codex Lean Execution v4

Normative replacement for the v3 execution workflow. Evidence and Mapping Standard requirements remain unchanged.

**REPOSITORY STATE IS MEMORY. THE HANDOFF IS A DELTA CONTRACT. THE CHAT PROMPT IS ONLY A COMMAND.**

## Intake and canonical inheritance

New substantial handoffs use schema `2.0` and `READY_FOR_CODEX_HANDOFF`. Modes are CREATE_DOMAIN, UPDATE_DOMAIN, EVIDENCE_REFRESH, PUBLICATION_ONLY, CLOSURE and REPOSITORY_GOVERNANCE. Historical v1 handoffs remain valid and must not be rewritten.

Run `python tools/check_codex_handoff.py <path> --plan` from a checkout containing the declared base commit. The checker validates the schema, exact base commit, canonical contract/revision refs at that commit, targeted changed-record paths, checksummed approved inputs and approved evidence/delta IDs. Missing Git history is a blocking intake error, not permission to assume inheritance. `--summary` is a compact diagnostic alternative.

The plan contains mode, base, affected paths, input paths, changed refs, materializer commands, affected tests, publication action, final gates and stop conditions. Commands are data for review; the checker never executes handoff commands. Repository actions and stop conditions constrain execution.

UPDATE_DOMAIN / EVIDENCE_REFRESH / PUBLICATION_ONLY inherit unchanged grain, identity, source-of-truth, relationships, temporal/mutation rules, DO NOT ASSUME and boundaries through `canonical_base`. Do not copy these arrays into the handoff. `delta.record_paths` identifies only the base registries required to validate changed IDs. New IDs live in the approved structured delta input. The approved delta ID and evidence refs must resolve in checksummed inputs. `target` is optional unless a target changes; `backlog_delta.blocking_count` is the resulting blocking count, not an arithmetic increment.

CREATE_DOMAIN references one approved structured materialization package, its checksums, expected invariants, target maturity, output paths and tests. Its deterministic materializer is mandatory. Semantic records are supplied once in the package, not repeated in prose or materializer source. Verify checksums, parse and materialize programmatically; inspect raw XLSX/CSV/source rows only on an exception. Do not manually emit hundreds of repetitive records when a deterministic transform exists.

REPOSITORY_GOVERNANCE scopes tooling and rules without pretending to inherit a domain contract. CLOSURE requires INITIAL/REGENERATE publication or an explicit user-approved canonical deferral. Structural checks do not grant semantic approval.

## No rediscovery and context budget

Read root AGENTS and the nearest routing AGENTS, then the plan. Do not load the full handoff merely because it is available. After successful intake, do not broadly search known facts, read unrelated domains/reference examples, reopen raw Oracle evidence, manually inspect every registry, re-derive protected counts or reinterpret comments/source. Targeted retrieval is permitted only for a failed test, missing ref/path, explicit conflict or inability to represent the approved delta losslessly. Stop with the exact blocker if semantic review is required.

Retain successful command name, exit status, counts and a concise summary. Redirect full logs to local scratch files. On failure retrieve only the failing test and relevant file/range. Do not print successful large logs, full YAML registries, ALL_SOURCE dumps, dependency registries, generated document text or giant diffs. Start review with `git diff --name-only` and `git diff --stat`.

## Validation ladder

1. Parser/materializer self-check and checksum verification.
2. Affected domain acceptance tests.
3. Affected SQL-safety tests.
4. Affected publication tests.
5. Compact unresolved-ref, duplicate-ID and evidence summary.
6. Once stable: `python tools/validate_catalog.py`.
7. Once stable: `python -m unittest discover -s tools -p 'test_*.py' -v`.
8. `python tools/check_publication_governance.py --base <base-sha>` and the required deterministic publication check.

Use `python tools/plan_change_validation.py --base origin/main --head HEAD`. It derives affected domains/tests, SQL/evidence impact and publication checks from Git paths. Unknown scope and shared tooling conservatively select full validation. Affected publication paths select `python tools/generate_publication.py all --check`; documentation-only execution-rule changes can skip regeneration. The cheap publication integrity gate always runs. A required final full regression is not replaced by scoped tests. Do not rerun expensive gates after every edit; rerun only if subsequent edits can invalidate them. CI remains the independent final acceptance environment.

## Publication governance

See `docs/publication-standard.md`. Approved closure normally means AGENT-READY and publication in the same delivery. The canonical YAML/SQL remains authoritative. Explicit user-approved deferral is the only exception; it must be recorded canonically with evidence and a reason.

New revisions classify changes as BREAKING_SEMANTIC, NON_BREAKING_SEMANTIC, EVIDENCE_PROFILE_REFRESH, PUBLICATION_ONLY or TOOLING_ONLY, and publication impact as NONE, INITIAL or REGENERATE. NONE needs an explicit reason. Breaking semantic changes advance approved contract_version. Publication-visible changes advance approved documentation_version, generate DOCX/PDF/manifest in the same PR, and preserve historical files.

Default QA is deterministic: expected artifacts/manifests, hashes, canonical digest/input inventory, sections and field/SQL completeness, Unicode, DOCX/PDF integrity, page geometry and repeatable regeneration. Retain domain content assertions and automated geometry checks; expand them when the renderer changes. Visual QA samples title, normal table, wide table, SQL and final/revision pages. Never render or review hundreds of pages merely due to document size. Widen only for an automated failure or a visible defect.

## Context boundaries and domain routing

A validated committed materialization, mapping closure or publication merge is a hard context boundary. Start the next substantial/unrelated phase in a fresh task; do not carry old chat as repository memory. A typical next command is:

> Continue from main. Apply handoff <path>. Follow AGENTS.md / Codex Lean Execution v4. Do not rediscover canonical semantics. Finish branch -> tests -> PR -> green CI -> verify main after authorized merge.

Do not create an extra task merely to finish the current milestone. A short domain-local AGENTS may contain only canonical/evidence/SQL paths, publication slug, materializer/test commands, stable acceptance counts and explicit boundaries. Do not duplicate semantic prose.

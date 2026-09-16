# Codex Lean Execution Standard v3

## Purpose

This standard reduces Codex context/token consumption without weakening KASO Data Catalog evidence, semantic, validation or change-management rules. `docs/mapping-standard.md` remains the semantic mapping authority. This document governs engineering execution after `READY FOR CODEX HANDOFF`.

Principle: **repository state is memory; the prompt is a command**.

## 1. Context loading

### Always read
1. root `AGENTS.md`;
2. the approved machine-readable handoff;
3. the existing target domain contract, if it exists;
4. the nearest applicable nested `AGENTS.md`, if present.

### Read only when relevant
- `docs/mapping-standard.md`: semantic-rule changes, schema/record-semantics changes, or ambiguous/incomplete handoff.
- `docs/publication-standard.md`: publication enabled by handoff or a publication test fails.
- unrelated domain contracts: only when an explicit cross-domain reference fails or the handoff names them.

Do not broadly reread the repository to rediscover facts already supplied by an integrity-validated handoff.

## 2. Machine-readable handoff

Use `docs/handoffs/codex-handoff.template.yaml` as the default handoff shape.

The handoff is an engineering contract, not a replacement for evidence. It must identify the approved evidence and semantic boundaries that ChatGPT has already closed.

Validate before work:

```sh
python tools/check_codex_handoff.py docs/handoffs/<domain>/handoff.yaml --summary
```

If required fields or referenced local paths are missing, stop with `HANDOFF BLOCKED`; do not infer replacements.

## 3. Evidence processing

Large XLSX/source/dependency inputs are data-processing inputs, not conversational reading material.

Preferred order:
1. verify checksums/integrity;
2. run deterministic parser/materializer;
3. inspect compact counts and exception reports;
4. inspect individual raw rows only when a validation conflict requires it.

Do not stream whole XLSX exports, source dumps, dependency closures or generated multi-megabyte YAML registries into model context when tooling can answer the question.

For dependency closure, prefer reproducible graph tooling over LLM traversal.

## 4. No rediscovery

After handoff integrity passes:
- do not re-search approved counts, IDs, paths, maturity, revision or environment;
- do not compare against unrelated benchmark domains unless a failing reference requires it;
- do not reinterpret business semantics from Oracle names/comments/source;
- do not rerun Oracle discovery solely to confirm already accepted evidence.

A conflict is different from rediscovery. If raw evidence contradicts a POTVRDENÉ assertion, stop and report the exact conflict.

## 5. Validation ladder

During implementation, use the cheapest sufficient gate first.

1. parser/materializer self-checks;
2. domain acceptance tests;
3. domain SQL-safety tests;
4. domain publication tests if publication is enabled;
5. unresolved-reference / duplicate-ID / evidence-integrity summaries;
6. `python tools/validate_catalog.py`;
7. `python -m unittest discover -s tools -p 'test_*.py' -v`;
8. `python tools/generate_publication.py all --check` only when publication changes can affect repository-wide generated artifacts.

Run full repository regression when the intended diff is stable. Re-run it only after changes that can invalidate the final result.

## 6. Output discipline

Successful commands: retain exit code plus compact summary.

Failed commands: inspect only the failing test/error context first; widen only as needed.

Diff review:
1. changed filenames;
2. `git diff --stat`;
3. full patches only for semantically relevant or suspicious files.

Do not print large successful logs, generated registries or complete evidence datasets into the agent context.

## 7. Thread/context boundaries

A committed, validated milestone is a context boundary.

For a substantial next phase, prefer a fresh Codex thread that starts from repository state and a short resume command. Do not carry a long history of prior exploratory tool calls merely for continuity.

Examples of substantial boundaries:
- scaffold -> approved materialization;
- DIAGNOSTIC-GRADE -> final dependency hardening;
- merged canonical contract -> later unrelated change.

This is not a requirement to split one coherent engineering task into many prompts. One short prompt may still request branch -> materialize -> validate -> PR -> merge when the handoff is complete.

## 8. Preferred prompt shape

A normal final Codex prompt should be short:

```text
Continue from main commit <sha>.
Materialize the approved KASO handoff at <handoff-path>.
Follow AGENTS.md and Codex Lean Execution v3.
Use supplied evidence programmatically; do not rediscover semantics.
Run domain gates first, then final repository regression.
If evidence conflicts with the handoff, return HANDOFF BLOCKED.
Otherwise finish branch -> PR -> green CI -> merge -> verify main.
```

Stable rules belong in the repository or handoff, not repeated in chat.

## 9. Domain-local AGENTS.md

For mature domains, a short nested `AGENTS.md` is encouraged when it saves repeated discovery. It may contain:
- canonical paths;
- evidence/manifests path;
- SQL path;
- publication slug;
- domain-specific test commands;
- stable acceptance invariants;
- explicit cross-domain ID rules.

It must not introduce new business meaning or contradict root rules/handoff.

## 10. Safety and semantic invariants

Lean execution never weakens these rules:
- MC authority and environment separation;
- evidence-first/no guessing;
- read-only Oracle diagnostics;
- status/evidence requirements;
- stable IDs and change management;
- dependency/access role distinctions;
- blocking backlog = 0 before AGENT-READY;
- publication generated only from canonical YAML/SQL;
- merge only with green CI and clean intended diff.

## 11. Acceptance for v3 process

A Codex run follows v3 when:
- handoff is machine-readable and validated;
- context reads are scoped to the task;
- bulk evidence is parsed programmatically when tooling exists;
- approved facts are not broadly rediscovered;
- domain tests precede full regression;
- successful logs/diffs are summarized;
- final full regression and CI remain mandatory;
- semantic conflicts still stop the handoff.

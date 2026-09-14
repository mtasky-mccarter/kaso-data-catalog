# KASO Data Catalog

This repository is the canonical machine-readable KASO Data Catalog. It holds evidence-backed object mappings and supporting repository tools. Slovak production Oracle owner MC is authoritative; MCCZ, TEST and TESTCZ require separate validation.

Read [AGENTS.md](AGENTS.md) for repository rules, evidence handling, ChatGPT/Codex responsibility split, `READY FOR CODEX HANDOFF`, and data preservation requirements. All database work used to build the catalog is read-only. The Oracle server version is unknown; canonical Oracle SQL must remain compatible with SQL Navigator 5.5.4.847 unless separately validated.

Generated human-readable publications follow [docs/publication-standard.md](docs/publication-standard.md). Each publication family lives in its own `generated/<publication-slug>/` folder and Technical & Diagnostic Reference files use the human-readable basename `KASO Data Catalog - Technical & Diagnostic Reference - <subject_sk> v<documentation_version>`.

## Repository structure

```text
AGENTS.md                     Repository, Codex and handoff rules
README.md                     Purpose and structure
docs/
  mapping-standard.md         Repository transcription of the mapping standard
  publication-standard.md     Generated publication naming/layout contract
  machine-readable-schema-v1.0.md
                              Schema model and conventions
catalog/
  transport/                  Transport catalog objects
  sales/                      Sales catalog objects
  warehouse/                  Warehouse catalog objects
  master/                     Master data catalog objects
  lookup/                     Lookup and reference catalog objects
evidence/
  manifests/                  Canonical evidence manifests and checksums
  snapshots/                  Retained SNAPSHOT_CRITICAL source files
sql/
  mapping-packs/              Read-only mapping SQL packs
  diagnostic/                 Read-only diagnostic SQL
tools/                        Parsing, validation and artifact tooling
generated/
  <publication-slug>/         Generated DOCX/PDF/viewer publication family, not canonical truth
schema/                       JSON Schema definitions for catalog record kinds
examples/schema-smoke-test/   Synthetic validation bundle
```

Schema v1.0 defines 22 JSON Schema record kinds, with synthetic fixtures and validator tests covering structure, global IDs, cross-file references, evidence requirements, retained evidence checksums, polymorphic relationships, dependency edges and source API references. GitHub Actions validates pull requests and `main`.

`CESTOVNE_PR_L` + `CESTOVNE_PR_O` v1.1 is the first production machine-readable AGENT-READY acceptance benchmark and is already merged into `main`. Evidence manifests belong under `evidence/manifests/`; top-level YAML files directly under `evidence/` are intentionally rejected by repository-layout tests.

## Working model

The target pipeline is:

```text
Oracle evidence
  -> ChatGPT semantic mapping and closure
  -> READY FOR CODEX HANDOFF
  -> Codex repository/build/validate engineering
  -> reviewed PR + green CI
  -> canonical GitHub main
  -> generated DOCX/PDF/viewer + SQL/agent context
```

ChatGPT owns evidence interpretation and semantic closure. Codex owns engineering materialization, validation, repository changes and generated artifacts. Codex must not infer missing business meaning. A future KASO Catalog Viewer should remain a read-only presentation layer generated from the canonical catalog, never a second source of truth.

For canonical publication output, use `python tools/generate_publication.py <publication-slug>` or `python tools/generate_publication.py all`; use `--check` in validation workflows.
Dokumentácia: [Nákupné objednávky](generated/nakupne-objednavky/) — Technical & Diagnostic Reference v1.0 (DOCX, PDF a manifest).

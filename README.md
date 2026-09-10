# KASO Data Catalog

This repository is the canonical machine-readable KASO Data Catalog. It holds evidence-backed object mappings and supporting repository tools. Slovak production Oracle owner MC is authoritative; MCCZ, TEST and TESTCZ require separate validation.

Read [AGENTS.md](AGENTS.md) for repository rules, evidence handling, responsibilities and data preservation requirements. All database work used to build the catalog is read-only. The Oracle server version is unknown; canonical Oracle SQL must remain compatible with SQL Navigator 5.5.4.847 unless separately validated.

## Repository structure

```text
AGENTS.md                     Repository and agent rules
README.md                     Purpose and structure
docs/
  mapping-standard.md         Machine-readable repository transcription of the mapping standard
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
generated/                    Generated publications, not canonical truth
schema/                       JSON Schema definitions for catalog record kinds
examples/schema-smoke-test/   Synthetic validation bundle
```

Schema v1.0 currently defines 22 JSON Schema record kinds, with synthetic fixtures and validator tests covering structure, global IDs, cross-file references, evidence requirements, retained evidence checksums, polymorphic relationships, dependency edges and source API references. GitHub Actions validates pull requests and `main`; branch pushes are not redundantly validated when the same change is already covered by a pull-request run.

The real `CESTOVNE_PR_L` + `CESTOVNE_PR_O` v1.1 migration is maintained as the production acceptance pilot on top of this schema. Evidence manifests belong under `evidence/manifests/`; top-level YAML files directly under `evidence/` are intentionally rejected by repository-layout tests to avoid competing sources of truth.

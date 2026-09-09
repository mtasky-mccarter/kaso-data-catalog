# KASO Data Catalog

This repository is the canonical machine-readable KASO Data Catalog. It will hold evidence-backed object mappings and supporting repository tools. Slovak production Oracle owner MC is authoritative; MCCZ, TEST and TESTCZ require separate validation.

Read [AGENTS.md](AGENTS.md) for repository rules, evidence handling, responsibilities and data preservation requirements. All database work is read-only. The Oracle server version is unknown; SQL must be compatible with SQL Navigator 5.5.4.847.

## Repository structure

```text
AGENTS.md                     Repository and agent rules
README.md                     Purpose and structure
docs/
  mapping-standard.md         Placeholder for the authoritative standard
catalog/
  transport/                  Transport catalog objects
  sales/                      Sales catalog objects
  warehouse/                  Warehouse catalog objects
  master/                     Master data catalog objects
  lookup/                     Lookup and reference catalog objects
evidence/
  manifests/                  Evidence manifests and checksums
  snapshots/                  Retained SNAPSHOT_CRITICAL source files
sql/
  mapping-packs/              Read-only mapping SQL packs
  diagnostic/                 Read-only diagnostic SQL
tools/                        Parsing, validation and artifact tooling
generated/                    Generated publications, not canonical truth
```

Empty directories are tracked with `.gitkeep` files. This bootstrap contains no object YAML schemas, migrated objects or raw production data. The authoritative Mapping Method & Agent-Ready Standard v2.1 will be migrated next; schema design remains a subsequent phase.

# KASO machine-readable catalog schema v1.0

## Purpose and authority

Canonical catalog records are UTF-8 YAML, so the same reviewed records can be version-controlled, referenced by stable IDs, validated, compared and used to generate publications. JSON Schema Draft 2020-12 defines their structure. The Mapping Method & Agent-Ready Standard v2.1 remains unchanged in [mapping-standard.md](mapping-standard.md); repository operating rules remain in [AGENTS.md](../AGENTS.md).

This schema introduces no KASO business facts. The example in `examples/schema-smoke-test/` is entirely synthetic: its object, owner, field, relationship and evidence names do not describe production. It demonstrates a format, not an accepted mapping. Nothing in validation connects to Oracle or executes SQL.

## Contract bundles and documents

A contract bundle groups a domain contract with one or more physical Oracle objects and their component registries. A contract is not restricted to a single table. `object_refs` identifies its object records, `component_refs` identifies component registry IDs, and `boundary_refs` identifies records describing boundaries (for example dependencies with `runtime_boundary: true`). Shared objects and records may be referenced from multiple contracts instead of being copied.

Each YAML file contains exactly one document with `schema_version: "1.0"` and `kind`. Single-record documents use their named ID, such as `contract_id`. Registry documents have their own `id` plus a `records` list; each member has its own named stable ID. Empty registries are permitted during discovery. Extra properties are rejected, including an invented confidence score or an embedded SQL query body.

| Kind / schema filename stem | Document identity | Record identity / content |
| --- | --- | --- |
| `contract` | `contract_id` | Domain, scope, authority, maturity, object/component/boundary/evidence references, limitations |
| `object` | `object_id` | Exact physical object name, environment and owner, grain, identities, field registry, authority/temporal summaries |
| `fields` | `id` | `field_id`; document also requires `object_ref` |
| `constraints` | `id` | `constraint_id` |
| `indexes` | `id` | `index_id` |
| `relationships` | `id` | `relationship_id` |
| `value-domains` | `id` | `value_domain_id` |
| `temporal` | `id` | `temporal_rule_id` |
| `mutations` | `id` | `mutation_id` |
| `flows` | `id` | `flow_id` |
| `dependencies` | `id` | `dependency_id` |
| `data-quality` | `id` | `dq_id` |
| `do-not-assume` | `id` | `rule_id` |
| `playbooks` | `id` | `playbook_id` |
| `sql-registry` | `id` | `sql_id` |
| `backlog` | `id` | `backlog_id` |
| `revisions` | `id` | `revision_id` |
| `evidence-manifest` | `evidence_id` | One separate manifest per evidence item |

These 18 document schemas share definitions in `schema/common.schema.json`. Required keys are specified by each schema's `required` list; supported optional fields need not be invented to fill a template. Nullable business definitions and summaries allow technical knowledge without an asserted business meaning. For example, a `TECHNICKY ZNÁME` field can have `business_definition_sk: null`.

A field registry belongs to one object. `object.field_registry_ref` references the registry ID; references to individual fields use `field_id`. Identity references can address constraint or field records. Constraint records carry raw type and enabled/validated states. Index entries carry a position and exactly one of `field_ref` or `expression_raw`, allowing function-based indexes without inventing a physical field.

## Stable IDs and references

IDs must match `[A-Za-z][A-Za-z0-9_.:-]*`. Allocate them once and retain them through title, translation or display wording changes. The synthetic example uses IDs such as `synthetic.object.001`; its title does not determine its identity. Canonical aliases are English ASCII snake_case; the regex enforces spelling shape, while review establishes the English meaning.

IDs are globally unique within the entire catalog validation scope, including registry IDs and individual record IDs. Duplicate IDs across files fail. All `*_ref` and `*_refs` values are record IDs, not filenames. Nullable references can be `null`; populated references must resolve within the input scope. This includes object, field, relationship, SQL, flow, boundary, dependency, constraint, lookup, replacement, authoritative-source and evidence links. Pass all referenced bundles/manifests together when validating shared contracts.

`sql_file`, `source_file` and `repository_path` are file locators, not record references. Repository paths use relative forward-slash paths with ASCII letters, digits, underscores, dots and hyphens, without traversal segments. Use `source_file` to preserve an original filename when an approved retained file needs a repository-safe name. SQL and retained evidence paths are resolved from the repository root.

## Source value preservation

Preserve Oracle object names, owners, field names, `datatype_raw`, `default_raw` and `oracle_comment` exactly as evidenced, including case and significant whitespace. For example, `VARCHAR2(16)` stays `VARCHAR2(16)`; it is not inferred or rewritten into another datatype. Physical identifiers have no English/ASCII alias restriction. Slovak business definitions remain UTF-8 Slovak text.

YAML `null` is distinct from the source string `"NULL"`. Both are supported and neither is converted to the other. Empty strings are also preserved in raw default/comment values. For raw observed values, omission means no value was supplied, while `raw_value: null` represents an actual source null. Quote RID, codes and other text identifiers, especially values like `"000012"`. The validator never writes back to YAML or normalizes source-derived strings.

The loader accepts a JSON-compatible YAML subset: string mapping keys, no duplicate keys, no aliases/merge keys, finite numeric values, and lowercase `true`/`false` booleans. Ambiguous YAML integer forms such as unquoted `000012` are rejected rather than silently converted. Dates remain strings and are validated as ISO dates. Timestamps require a date, time and explicit timezone; leap-second timestamps are not supported. Quote any source value that must remain text.

## Status, maturity and evidence

The catalog status enum is exactly:

- POTVRDENÉ
- TECHNICKY ZNÁME
- ODVODENÉ
- TREBA OVERIŤ
- DATA GAP
- NEPOUŽÍVAŤ
- DEPENDENCY ONLY

Maturity is `DISCOVERY`, `CORE MAPPED`, `DIAGNOSTIC-GRADE`, `EXHAUSTIVE DEPENDENCY-GRADE` or `AGENT-READY`. `DISCOVERY` is the requested initial schema state, not a change to the Mapping Standard. Schema acceptance is not an Agent-Ready closure audit and does not authorize promotion of maturity or business meaning.

Evidence references must resolve to existing `evidence-manifest` records, not just any record with a matching ID. Evidence classes are A, B, B2, C, D and E. **E is hypothesis/backlog material and must never be the sole support for a POTVRDENÉ canonical fact.** Unverified material uses `TREBA OVERIŤ` or `DATA GAP`; an E reference does not create a technical or business proof.

Every record with `status: POTVRDENÉ` must have at least one valid evidence reference, and at least one resolved manifest must have a class other than E. Missing references, references to non-manifest records, or class-E-only support fail validation. This checks the existence and class of support, not whether its contents prove the claim. Accepted evidence and business review remain necessary.

Dependency roles include CORE DOMAIN, DIRECT WRITER, API WRITER, READER, CALLER, DEPENDENCY ONLY and ACCESS CAPABILITY. Writer/reader/caller classifications require non-E evidence; a dependency-only status cannot be combined with these asserted roles. Review must establish whether the cited evidence proves the role. Source visibility, depth and runtime boundary are recorded separately.

## Relationships, temporal rules and source flows

Relationships can be `DIRECT`, `CONDITIONAL` or `POLYMORPHIC`. Direct/conditional records identify destination object and field references; conditional records require `condition_sk`. Field reference lists are ordered to represent multi-column joins.

A polymorphic record uses `selector_field_refs` and two or more `targets`, instead of a single destination. Each target requires `to_object_ref`, `to_field_refs`, `selector_condition_sk`, `status` and `evidence_refs`. Each target also supports its own `validation_summary_sk`, cardinality, fanout risk, safe usage and orphan/duplicate test summaries. Routing logic is stored separately from successful live JOIN validation. A selector or prefix alone does not prove that a target JOIN succeeds. Schema validation never interprets routing as proof.

The temporal enum distinguishes `RAW CURRENT`, `STORED SNAPSHOT`, `DERIVED CURRENT`, `TRANSITION STAMP`, `LAST UPDATE`, `SELECTIVE HISTORY` and `DATA GAP`. Fields may carry a classification; temporal-rule records describe events, writers/sources, rollback behavior, reconstructability and history limitations for one or more scope records. Unknown temporal knowledge can be marked `DATA GAP`; no timeline is reconstructed by inference.

Mutations record target/writer references, conditions, watched fields, bypass/session behavior, calls, direct mutations, side effects, exceptions and business/diagnostic descriptions. Reusable flow records use ordered `calls` entries (`callee_ref`, `sequence`, optional condition); `direct_mutations`, `side_effects` and `exceptions` contain descriptions and optional scope references. These are source descriptions, never executable production writes.

Value-domain records support source-confirmed constants without an observed live value: `raw_value`, `observed_count` and `snapshot_date` can be omitted when no live observation exists. `observed_live: false` does not disprove a source constant. Observed counts are snapshots rather than permanent business facts.

## Separate SQL registry

Executable read-only SQL lives in separate `.sql` files. YAML stores registry metadata and an ID; playbooks and evidence manifests refer to that ID. No canonical SQL query-body property is accepted in the registry.

Every SQL registry entry requires a repository-relative `.sql` path and compatibility metadata:

```json
{
  "sql_client": "SQL Navigator 5.5.4.847",
  "oracle_server_version": null,
  "read_only": true
}
```

`null` explicitly means the server version is unknown. The validator checks the registry structure and that the referenced file exists. It does not execute SQL, prove its read-only behavior or certify server compatibility. SQL review must follow the Mapping Standard's conservative compatibility rules. Input parameters carry a name, required flag and optional description/raw datatype. Query purpose, result grain, fanout warnings, what a query proves and what it does not prove remain separate metadata.

## Evidence retention

Manifests remain separate from canonical business contracts and from the retained raw files they describe. They record evidence class, Mapping Pack, environment/owner, times, client, query reference, source file, summary, supported records, review state and limitations. `result_summary_sk` provides prose; optional `result_summary` provides a structured summary with named observations and raw scalar values, units and optional scope references.

- `TRANSIENT`: raw retention is not required.
- `REPRODUCIBLE`: raw retention is not required; `query_ref` and structured `result_summary` can record how the evidence can be reproduced and what was observed. Review must establish reproducibility.
- `SNAPSHOT_CRITICAL`: a 64-character hexadecimal SHA-256, `raw_retained: true` and a `repository_path` under `evidence/snapshots/` are mandatory. The validator also checks that the retained file exists and matches the checksum.

For any manifest declaring raw retention, the validator requires an existing repository file; a supplied checksum is checked. Before deleting a transient original of SNAPSHOT_CRITICAL evidence, the retained copy, checksum and completed commit must satisfy AGENTS.md. The validator checks file/hash state, not whether the commit/deletion handoff is safe. Retention classes are repository operating rules and are not added to the Mapping Standard.

`.gitignore` excludes ordinary XLS/XLSX exports case-insensitively while allowing approved retained snapshots under `evidence/snapshots/**`. This exception does not approve their content automatically. Common secret/local patterns remain ignored even inside snapshots. YAML, JSON, SQL and Markdown catalog files are not ignored by extension.

## Revisions, breaking changes and publications

Changes to canonical alias, grain, JOIN key or business meaning are breaking changes. Record `breaking_change: true`, the affected stable IDs, contract version, date, change/reason and evidence in a revision entry, and review the diff explicitly. Do not silently overwrite confirmed facts; conflicts become backlog/revalidation work according to the Mapping Standard. Backlog status is restricted to `TREBA OVERIŤ` or `DATA GAP` and records blocking state, question, proposed validation and closure condition.

`schema_version` identifies the schema format; `contract_version` in revisions identifies the contract revision. The validator does not infer breaking changes by comparing historical commits and does not enforce a version-bump policy automatically.

Generated DOCX and other publications will later be produced by reading canonical YAML records and resolving their references. Generators may render titles, tables, relationships and evidence provenance into `generated/`. They must never become canonical source of truth or be used to silently replace reviewed YAML. No DOCX generator or pilot object migration is introduced here.

ChatGPT is responsible for analytical and semantic decisions. Codex handles parsing, schema validation, repository engineering, references, dependency graphs, diffs and artifact generation. Codex must not promote business meanings without accepted evidence; the user/business owner provides process authority under the Mapping Standard.

## Validation and development

Use Python 3.10 or later. The minimal development dependencies are pinned in `requirements-dev.txt`: PyYAML for parsing, jsonschema for Draft 2020-12 validation, and referencing for offline schema resolution. The standard-library unittest runner requires no test framework. The validator's timestamp checker uses the Python standard library, avoiding optional format packages.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/validate_catalog.py examples/schema-smoke-test
.venv/bin/python -m unittest discover -s tools -p 'test_*.py' -v
```

Without positional paths, the validator scans `catalog/`, `evidence/manifests/` and `examples/`. Explicit paths may be YAML files or directories. Include all referenced records in one invocation. Empty explicit scopes, nonexistent paths, invalid YAML and unknown document kinds fail rather than being silently skipped.

Validation has two layers:

1. JSON Schema checks each document's structure, types, required IDs, enums, supported keys and conditional snapshot/relationship/evidence requirements. All 19 schemas are themselves checked against Draft 2020-12. Schema identifiers are offline logical names under `schemas.example.invalid`; they are not hosting endpoints and the validator never fetches them.
2. `tools/validate_catalog.py` performs catalog-level cross-file checks: global ID uniqueness, reference resolution, manifest target checks for evidence links, non-E support for confirmed facts and classified dependency roles, SQL file existence, and retained evidence path/checksum checks. JSON Schema alone does not implement cross-file referential integrity.

Tests use only the synthetic bundle and synthetic in-memory/temporary variants. They cover every document kind, a complete contract → object → fields → relationship → evidence chain, invalid enums, missing/duplicate IDs, unresolved references, malformed manifests/fixtures, snapshot failures, illegal backlog states, invalid polymorphic routing, preservation of source values and confirmed facts without valid evidence.

A passing result establishes structural/reference consistency, not business truth, JOIN correctness, evidence acceptance, SQL safety, complete referential target typing or Agent-Ready maturity. In particular, generic scope/source references may address different record kinds; existence is checked, but domain-specific suitability and field-to-object ownership require review. This is deliberate schema engineering scope, not an automatic semantic approval workflow.

Implementation references: [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-core) and [jsonschema's offline referencing API](https://python-jsonschema.readthedocs.io/en/stable/referencing/).

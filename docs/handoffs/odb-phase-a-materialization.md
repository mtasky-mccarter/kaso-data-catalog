# ODB Phase A materialization — 2026-09-15

Document-backed materialization on `feat/sales-obchodne-pripady-v1.2`, based on
intake commit `2bdf1f1feb903e265f3a501ca4193ca8b039d936`. No reset or main merge.
Approved v1.2 semantic contract; schema v1.0; MC authoritative;
DIAGNOSTIC-GRADE maximum. Publication remains blocked.

## Materialized inventory

| Surface | Count / scope |
| --- | --- |
| OBJ_ODB_L fields | 79 |
| OBJ_ODB_O fields | 44 |
| Trigger inventory and approved flow summaries | 50: 17 L, 33 O; no imported raw bodies |
| Mutation matrix | 18; grouped writer text preserved, no wildcard expansion |
| Relationships | 12; conditional VYD trace and fan-out/history limits preserved |
| Constraints | 33: 29 L, 4 O; O FK names and full raw CHECK expressions remain open |
| Indexes | 34; XML domain expression remains the approved non-blocking gap |
| Value domains | 10 FLAGS_S[20] codes, preserved as strings |
| Temporal rules | 13, including raw/current, derived, stored snapshot, selective history and master gaps |
| DQ observations | 16; document-reported snapshot, not fresh Oracle execution |
| DO NOT ASSUME / approved contract rules | 144 |
| Oracle entity boundaries | 110; existing external IDs reused where fields already exist |
| Source-reference dependencies | 123 links from the 94-object document inventory; DEPENDENCY ONLY |
| Playbooks / diagnostic SQL | 8 / 20 SELECT files |
| Evidence manifests | 1 accepted D manifest; no fabricated raw A/B/B2 manifests |
| Backlog | 7 claim-specific blocking entries; 9 original non-blocking gaps retained |

The preserved original DOCX checksum is
`815e78b939389326badebc567d02411359a0a2f1784fb2c1b39dab6324edbd95`.
The retained JSON extraction is independently checksum-pinned by the materializer.
`intake-integrity.json` preserves the earlier successful 41-file checksum audit.
At materialization time the original source bundle was no longer available at
`/Users/martintasky/Desktop/odb_phase_a_source_bundle/`. Raw XLSX contents were
not imported or certified from checksums alone. Supporting references were not
promoted to competing semantic authority.

## Remaining HANDOFF BLOCKED claims

- L empty default/comment cells: source NULL versus omitted document value;
  affected field IDs are explicitly scoped. OBJ_H01..H06B are still absent.
- O raw defaults/comments: scoped to the 44 field records.
- Exact names of the eight O foreign-key constraints: scoped to their fields.
- Complete raw CHECK expressions: scoped to the three CHECK identities;
  existing schema stores their documented explanations in companion rules.
- Full trigger/package raw source details, call chains, watched fields,
  exceptions and session branches beyond approved summaries: scoped to flows.
- Raw dependency/API anchors and closure: scoped to the corresponding registries.
  Document DML-reference counts are not runtime counts; closure is not exhaustive.
- Publication: explicitly blocked by the Phase A instruction.

The unavailable raw claims do not suppress the other approved document facts.
Empty closure/API registers are unmaterialized inputs, never verified zero.

## Reconciliation and repository checks

VYD boundary IDs `vyd.oracle.f1dfff357c6da5d31924380f` and
`vyd.oracle.c05d6994b969d9ce00ed3039` remain unchanged and are reconciled with
`mc.object.obj_odb_l` and `mc.object.obj_odb_o`. VYD/CP canonical files, schema
files and all existing generated publications are byte-identical to the intake
baseline. Supplementary external field boundaries do not introduce master
business meaning.

Main inspected at `8230ccd8fd177f1a4edd9eaae35f3ea86a569283`: `catalog/sales/`
contains only `.gitkeep`, with no canonical ODB contract. Main was not modified.

## Validation

- `python tools/validate_catalog.py`: PASS, 133 YAML documents; zero unresolved
  references and zero duplicate global IDs; retained-file checks passed.
- `python -m unittest discover -s tools -p 'test_*.py' -v`: 84 tests,
  OK with 2 explicit skips; no test failures.
- ODB acceptance: 7 passed; ODB SQL safety: 1 passed; ODB publication gate:
  2 passed (exit 2 without output for blocked publication).
- Repeated materializer run: domain YAML is byte-identical (idempotent).
- SQL comparison: every character except whitespace matches its approved source
  SELECT; no Oracle queries were executed.

The two skipped tests are the existing CP/VYD deterministic publication checks.
Even their `--check` path generates temporary DOCX/PDF. To obey the user's ban,
the full discovery command ran with a task-local `sitecustomize` guard that
raises `unittest.SkipTest` only when subprocess launches
`tools/generate_publication.py`. It does not intercept the ODB fail-closed
entrypoint. Existing committed publication checksum/layout tests still ran.
No DOCX/PDF was created. These two generator checks remain unexecuted in this run.

## Remote write authorization

The initial single GitHub tree request exceeded the automatic review limit of
200,000 bytes and was rejected without a returned tree/commit SHA. The user then
explicitly approved splitting the write into smaller, separately reviewed tree
steps and creating one commit on `feat/sales-obchodne-pripady-v1.2`. Every step
retains the preceding tree; the final commit has the original intake commit as
its sole parent. No main merge or force update is authorized.

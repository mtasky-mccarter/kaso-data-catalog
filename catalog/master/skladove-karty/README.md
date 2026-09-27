# Product Master / skladové karty

Canonical MC / OWNER=MC contract: `pm.contract.skladove_karty.1_0`.
Declared scope: EXHAUSTIVE DEPENDENCY-GRADE / AGENT-READY.

The approved semantic handoff and byte-level package inventory are retained in
`docs/handoffs/skladove-karty/`. All 166 supplied artifacts have checksum manifests.
Critical physical, population, incident and deployed-source snapshots are retained
under `evidence/snapshots/skladove-karty/`. Other supplied raw exports remain external
reproducible evidence, with their actual checksums and source filenames recorded.

Root fields preserve the 169 supplied metadata rows, including original Oracle
comments and source nulls. All 169 root canonical aliases now exactly match the
approved 2026-09-17 naming dictionary retained in
`evidence/snapshots/skladove-karty/aliases-v1/`. Its 40 TECHNICAL_NEUTRAL entries do not
expand unresolved acronyms or introduce business meaning. All other field
properties are unchanged. Historical field-level notes about the 2026-09-16
null-alias decision are superseded for root fields by revision
`pm.revision.1_0_aliases_20260917`; satellite aliases remain deferred.
Oracle comments alone do not establish business meaning.

The 2026-09-16 non-breaking revision records the resolved STAV=8 forecast reset:
simultaneous PLAN_POCET2 and POZN mutation, the dedicated Ukončený predaj exception,
and retained ordinary BITAND(STAV,2)=2 protection. The original defect remains in
revision history. All seven approved non-blocking gaps remain open.

Dependency rows, source contexts, lexical API references and source-proven direct
writers are separate records. Source contexts may include partial source windows,
comments and literals; a text hit is not a runtime role. Source text stored in the
catalog is evidence, not executable diagnostic SQL.

The 25 diagnostics are read-only and document grain, fan-out and interpretation
limits. They were checked offline; they were not executed against Oracle. BOM
diagnostics preserve the executable prefix heuristic, component weight, DU split,
token branches and stored provenance. RF reconciliation deliberately preserves
the captured footer's legacy lifecycle/name-prefix behavior while measuring the
flag-12 difference; it does not repair production data or report SQL.

Reproduce from the supplied package (install `requirements-dev.txt` first):

```sh
python tools/materialize_pm.py /path/to/KASO_skladove_karty_codex_package_2026-09-16
python tools/materialize_pm_sql.py
python tools/check_codex_handoff.py docs/handoffs/skladove-karty/handoff.yaml --summary
python -m unittest discover -s tools -p 'test_pm*.py' -v
python tools/validate_catalog.py
python -m unittest discover -s tools -p 'test_*.py' -v
```

Publication version 1.0 is approved and derived from canonical revisions.
Generate DOCX/PDF/manifest with `python tools/generate_publication.py skladove-karty`
and verify with `python tools/generate_publication.py skladove-karty --check`.
Outputs live in `generated/skladove-karty/`; canonical YAML/SQL stays authoritative.
The original publication deferral is retained in revision/provenance history.

The retained CSV is the authoritative alias input; the duplicate XLSX is not
required for replay. The original delta MANIFEST and approval text are retained
byte-for-byte. Run `python tools/apply_pm_aliases.py` to replay only this naming
delta. The main materializer also reapplies it automatically.

# READY FOR CODEX HANDOFF — obchodní partneri

Mode: CREATE_DOMAIN
Base commit: `e7743fc70b3367411be6f5463aacb13483f60d02`
Canonical target: `catalog/master/obchodni-partneri/`
Target maturity: AGENT-READY
Blocking backlog: 0

Use `handoff.yaml` as the v2 delta contract. The approved semantic and physical records live once in `evidence/snapshots/obchodni-partneri/materialization-package.yaml`. All retained Mapping Pack XLSX inputs are under `evidence/snapshots/obchodni-partneri/raw/` and are individually checksummed in both `MANIFEST.csv` and the handoff `approved_inputs`.

Do not rediscover semantics. Build a deterministic `tools/materialize_obchodni_partneri.py` that consumes the structured package, verifies raw evidence checksums, writes canonical YAML/SQL/evidence manifests, and runs the validation ladder from Codex Lean Execution v4.

Publication is intentionally not part of this CREATE_DOMAIN intake. Do not invent `documentation_version`; use a later approved CLOSURE delta.

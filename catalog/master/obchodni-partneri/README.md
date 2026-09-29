# Obchodní partneri — canonical MC master

`contract.yaml` is the entry point. The approved structured package is retained at
`evidence/snapshots/obchodni-partneri/materialization-package.yaml` and pinned by
`docs/handoffs/obchodni-partneri/handoff.yaml`. It includes the bulk current lookup
value snapshots; these are evidence, not historical lookup-label contracts.

Run the deterministic materializer from the repository root:

```
python tools/materialize_obchodni_partneri.py evidence/snapshots/obchodni-partneri/materialization-package.yaml
python tools/materialize_obchodni_partneri.py evidence/snapshots/obchodni-partneri/materialization-package.yaml --check
python -m unittest discover -s tools -p 'test_op_*.py' -v
```

The materializer verifies every approved input and manifest size/hash without
parsing raw XLSX. It normalizes the approved records to existing catalog schemas.
Where a schema has no separate field for source metadata, the complete approved
record is preserved as JSON in its description/limitations field. No new Oracle
meaning is derived. Profile descriptions retain exact snapshot values/dates;
boundary descriptions retain their original BOUNDARY tag. Index validity remains
`oracle_status_raw`, separate from technical mapping status.

`oracle-entities.yaml` holds boundary-only identities needed by references. It is
not a full mapping of those objects. Dictionary dependency nodes are not evidence
of source execution. An unknown writer object type leaves `writer_ref` null and
retains the approved source name/role in the mutation description. Trigger
watched fields never imply that every watched field is itself mutated.

The seven SQL files are copied verbatim from the approved package. Synthetic SQL
regressions verify row preservation and intended boundaries; they are not live
Oracle validation or a claim about the unknown server version.

Raw filenames remain unchanged under `raw/`. Byte-identical `retained/` copies
provide ASCII paths required by the existing canonical evidence path schema.
The manifest remains provenance, not an evidence-class record.

Publication is explicitly deferred by the user in the initial revision. There is
no documentation_version and no partner publication in this delivery. Future
publication requires the separately approved CLOSURE delta. MIESTA_DODANIA,
KONTAKTY and PARTNER_BANKY remain separate future mappings.

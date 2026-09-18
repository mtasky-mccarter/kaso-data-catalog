"""Apply the approved naming-only delta; never infer meaning from aliases/comments."""
import csv
import hashlib
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = Path('catalog/master/skladove-karty')
DELTA = Path('evidence/snapshots/skladove-karty/aliases-v1')
CSV_NAME = 'SKLAD_KARTA_canonical_aliases_v1.0.csv'
CSV_SHA256 = '28a802e0db9b060a2bfdea94f9125166dc910dcb909ec18370761ab39227b9a0'
REVISION = 'pm.revision.1_0_aliases_20260917'


def load_dictionary(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != CSV_SHA256:
        raise ValueError('Alias dictionary checksum does not match approved v1.0')
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def apply_records(records, rows):
    """Validate everything before changing only canonical_alias, in place."""
    if len(records) != 169 or len(rows) != 169:
        raise ValueError('Expected exactly 169 root fields and aliases')
    mapping = {r['oracle_name']: r for r in rows}
    if len(mapping) != 169 or set(mapping) != {r['oracle_name'] for r in records}:
        raise ValueError('Alias dictionary must cover root names exactly once')
    aliases = [r['canonical_alias'] for r in rows]
    if len(set(aliases)) != 169 or any(not re.fullmatch(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)*', a) for a in aliases):
        raise ValueError('Aliases must be unique ASCII snake_case')
    for field in records:
        row = mapping[field['oracle_name']]
        if int(row['ordinal_position']) != field['ordinal_position']:
            raise ValueError('Physical ordinal mismatch')
        if row['alias_basis'] not in {'APPROVED_TRANSLATION', 'TECHNICAL_NEUTRAL'}:
            raise ValueError('Unknown alias basis')
        if field.get('canonical_alias') not in (None, row['canonical_alias']):
            raise ValueError('Refusing to replace an existing different alias')
    for field in records:
        field['canonical_alias'] = mapping[field['oracle_name']]['canonical_alias']


def apply(root=ROOT):
    def read(path):
        return yaml.safe_load((root / path).read_text())
    def write(path, data):
        (root / path).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=110), encoding='utf-8')
    fields = read(DOMAIN / 'fields-sklad_karta.yaml')
    apply_records(fields['records'], load_dictionary(root / DELTA / CSV_NAME))
    write(DOMAIN / 'fields-sklad_karta.yaml', fields)
    contract = read(DOMAIN / 'contract.yaml')
    old = 'Canonical aliases remain null by explicit user decision on 2026-09-16; dictionary approval deferred.'
    new = 'All 169 MC.SKLAD_KARTA canonical aliases approved on 2026-09-17; naming layer only. Satellite aliases remain deferred.'
    contract['limitations_sk'] = [new if s == old else s for s in contract['limitations_sk']]
    write(DOMAIN / 'contract.yaml', contract)
    revisions = read(DOMAIN / 'revisions.yaml')
    if not any(r['revision_id'] == REVISION for r in revisions['records']):
        revisions['records'].append(dict(
            revision_id=REVISION, contract_version='1.0', date='2026-09-17', breaking_change=False,
            changed_record_refs=[r['field_id'] for r in fields['records']],
            change_sk='Approved naming-only delta: populate all 169 MC.SKLAD_KARTA canonical_alias values from the retained CSV. TECHNICAL_NEUTRAL does not expand unresolved acronyms or close semantic gaps. Supersedes the historical 2026-09-16 null-alias deferral for root fields only.',
            reason_sk='Non-breaking additive completion of previously null aliases: no existing alias renamed or removed; stable IDs, physical names and every other field property are unchanged. Definitions, status, evidence, temporal rules, lookup meanings and all seven backlog items retain their prior meaning.',
            evidence_refs=['pm.evidence.alias_dictionary_v1', 'pm.evidence.alias_approval_v1']))
    write(DOMAIN / 'revisions.yaml', revisions)
    counts_path = Path('docs/handoffs/skladove-karty/materialization-counts.json')
    if (root / counts_path).exists():
        import json
        counts = json.loads((root / counts_path).read_text())
        counts['null_root_aliases'] = 0
        counts['evidence_manifests'] = len(list((root / 'evidence/manifests/skladove-karty').glob('*.yaml')))
        (root / counts_path).write_text(json.dumps(counts, indent=2) + '\n')
    print('PASS: 169 approved aliases applied; all other field properties preserved.')


if __name__ == '__main__':
    apply()

"""Replay the approved publication-only metadata delta after base materialization."""
from pathlib import Path
import yaml

REVISION_ID = 'pm.revision.1_0_publication_20260923'
DOMAIN = Path('catalog/master/skladove-karty')


def approve_publication(root):
    def read(path): return yaml.safe_load((root/path).read_text())
    def write(path, data):
        (root/path).write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False,width=110),encoding='utf-8')
    revisions = read(DOMAIN/'revisions.yaml')
    if not any(r['revision_id']==REVISION_ID for r in revisions['records']):
        revisions['records'].append(dict(revision_id=REVISION_ID,contract_version='1.0',date='2026-09-23',breaking_change=False,
            changed_record_refs=['pm.contract.skladove_karty.1_0'],
            change_sk='Publication of the closed MC Product Master mapping explicitly approved for documentation version 1.0. DOCX/PDF are derived from canonical YAML/SQL. Historical publication deferral remains preserved in preceding revisions and original handoff evidence.',
            reason_sk='Publication/repository delta only; no field, status, JOIN, temporal, DQ, mutation, backlog or boundary semantics changed.',
            evidence_refs=['pm.evidence.publication_approval_20260923']))
    write(DOMAIN/'revisions.yaml',revisions)
    contract=read(DOMAIN/'contract.yaml')
    contract['limitations_sk']=[('Publication approved for version 1.0 on 2026-09-23; canonical YAML/SQL remains authoritative.' if x=='No publication/documentation version created.' else x) for x in contract['limitations_sk']]
    write(DOMAIN/'contract.yaml',contract)
    path=Path('docs/handoffs/skladove-karty/handoff.yaml'); hand=read(path)
    hand['target']['documentation_version']='1.0'
    hand['publication'].update(enabled=True,slug='skladove-karty',subject_sk='skladové karty',output_dir='generated/skladove-karty/',generator_command='python tools/generate_publication.py skladove-karty')
    decision='2026-09-23 user approved derived Product Master publication version 1.0; historical deferral superseded without reopening mapping.'
    if decision not in hand['engineering_decisions']:hand['engineering_decisions'].append(decision)
    write(path,hand)

#!/usr/bin/env python3
"""Apply only the checksummed, approved OP publication metadata delta."""
import argparse
import copy
import json
from pathlib import Path
from materialize_obchodni_partneri import ROOT, DOMAIN, dump, digest
from validate_catalog import load_yaml

HANDOFF = Path('docs/handoffs/obchodni-partneri/publication-closure-20260930.yaml')
DELTA = Path('evidence/source-extracts/op/publication-delta-20260930.json')
APPROVAL = Path('evidence/snapshots/obchodni-partneri/publication-approval-20260930.yaml')

def approved_delta(root):
    for entry in load_yaml(root/HANDOFF)['approved_inputs']:
        path = (root/entry['path']).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != entry['sha256']:
            raise ValueError('Approved input checksum mismatch: '+entry['path'])
    return json.loads((root/DELTA).read_text())

def project(root, contract=None, revisions=None):
    delta = approved_delta(root)
    contract = copy.deepcopy(contract if contract is not None else load_yaml(root/DOMAIN/'contract.yaml'))
    revisions = copy.deepcopy(revisions if revisions is not None else load_yaml(root/DOMAIN/'revisions.yaml'))
    if contract['contract_id'] != delta['contract_ref']:
        raise ValueError('Unexpected contract')
    revision = delta['revision']
    matches = [r for r in revisions['records'] if r['revision_id'] == revision['revision_id']]
    if matches and matches != [revision]:
        raise ValueError('Existing publication revision differs from approval')
    limits = contract['limitations_sk']
    for old in delta['contract_update']['limitations_remove_exact']:
        if old in limits:
            limits.remove(old)
        elif not matches:
            raise ValueError('Expected original publication limitation missing')
    for new in delta['contract_update']['limitations_add']:
        if new not in limits:
            limits.append(new)
    if not matches:
        revisions['records'].append(revision)
    evidence_id = revision['evidence_refs'][0]
    evidence = dict(schema_version='1.0',kind='evidence-manifest',evidence_id=evidence_id,
        evidence_class='D',environment='MC',oracle_owner='MC',snapshot_date=revision['date'],
        retention_class='SNAPSHOT_CRITICAL',raw_retained=True,repository_path=str(APPROVAL),
        sha256=digest(root/APPROVAL),supports_record_refs=[delta['contract_ref'],revision['revision_id']],
        review_status='APPROVED',result_summary_sk=revision['reason_sk'])
    return {str(DOMAIN/'contract.yaml'):contract,str(DOMAIN/'revisions.yaml'):revisions,
            'evidence/manifests/obchodni-partneri/'+evidence_id+'.yaml':evidence}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('delta',type=Path)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    if args.delta.resolve() != ROOT/DELTA:
        raise ValueError('Unexpected delta path')
    for relative, value in project(ROOT).items():
        path = ROOT/relative
        content = dump(value).encode()
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                raise ValueError('Metadata drift: '+relative)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(content)
    print('PASS: approved publication metadata; semantic registries unchanged')

if __name__ == '__main__':
    main()

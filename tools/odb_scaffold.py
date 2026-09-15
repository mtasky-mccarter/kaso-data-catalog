"""Strict offline reader for the ODB scaffold; does not interpret evidence."""
from pathlib import Path

from validate_catalog import load_yaml, validate_bundle

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = Path('catalog/sales/obchodne-pripady')


def read_scaffold(root=ROOT):
    paths = sorted((root / DOMAIN).glob('*.yaml'))
    if not paths:
        raise ValueError('HANDOFF BLOCKED: ODB scaffold is missing')
    documents = {p.relative_to(root).as_posix(): load_yaml(p) for p in paths}
    # Validate global references, including immutable VYD boundary IDs.
    all_documents = dict(documents)
    for directory in ('catalog', 'evidence/manifests'):
        for p in (root / directory).rglob('*.yaml'):
            key=p.relative_to(root).as_posix()
            if key not in all_documents:
                all_documents[key]=load_yaml(p)
    errors = validate_bundle(all_documents, root=root)
    if errors:
        raise ValueError('\n'.join(errors))
    return {Path(p).name: doc for p, doc in documents.items()}


def publication_blockers(root=ROOT):
    documents = read_scaffold(root)
    reasons = [r['question_sk'] for r in documents['backlog.yaml']['records'] if r['blocking']]
    # This phase implements a scaffold only. Removing backlog entries cannot
    # silently turn it into an approved production generator.
    reasons.append('HANDOFF BLOCKED: publication remains explicitly blocked for Phase A')
    return reasons

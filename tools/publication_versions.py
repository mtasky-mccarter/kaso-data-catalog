"""Approved canonical versions; the historical fallback never invents a version."""
import re
from pathlib import Path
import yaml

VERSION_RE = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)$')
CLASSIFICATIONS = ['BREAKING_SEMANTIC', 'NON_BREAKING_SEMANTIC', 'EVIDENCE_PROFILE_REFRESH', 'PUBLICATION_ONLY', 'TOOLING_ONLY']

def version_key(value):
    if not isinstance(value, str) or not VERSION_RE.fullmatch(value):
        raise ValueError(f'Expected approved x.y version, got {value!r}')
    return tuple(map(int, value.split('.')))

def resolve_versions(root, revisions_path):
    records = yaml.safe_load((Path(root) / revisions_path).read_text())['records']
    contract = max((r['contract_version'] for r in records), key=version_key)
    explicit = [r['documentation_version'] for r in records if r.get('documentation_version') is not None]
    if explicit:
        keys = [version_key(v) for v in explicit]
        if keys != sorted(keys):
            raise ValueError('documentation_version must not regress in revision order')
    return contract, explicit[-1] if explicit else contract, bool(explicit)

#!/usr/bin/env python3
"""Replay the checksummed approved CoA delta against its exact canonical base."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'evidence/source-extracts/pur/coa-delta-20260929.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def materialize(check=False):
    handoff = yaml.safe_load((ROOT / 'docs/handoffs/nakupne-objednavky/coa-20260929.yaml').read_text())
    for item in handoff['approved_inputs']:
        assert digest((ROOT / item['path']).read_bytes()) == item['sha256'], item['path']
    package = json.loads((ROOT / PACKAGE).read_text())
    base = package['base_commit']
    outputs = []
    for op in package['operations']:
        target = ROOT / op['path']
        assert target.resolve().is_relative_to(ROOT)
        raw = subprocess.run(['git', 'show', base + ':' + op['path']], cwd=ROOT, capture_output=True)
        before = raw.stdout if raw.returncode == 0 else None
        assert (digest(before) if before is not None else None) == op['base_sha256'], op['path']
        if 'text' in op:
            content = op['text'].encode()
        elif 'append_records' in op:
            # Retain historical records byte-for-byte, including quoted code strings.
            content = before.rstrip(b'\n') + b'\n' + yaml.safe_dump(
                op['append_records'], allow_unicode=True, sort_keys=False, width=110).encode()
        else:
            doc = op.get('document') or yaml.safe_load(before)
            for patch in op.get('update_records', []):
                matches = [r for r in doc['records'] if r.get(patch['id_key']) == patch['id']]
                assert len(matches) == 1, patch['id']
                matches[0].update(patch['set'])
            content = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=110).encode()
        if target.exists():
            assert target.read_bytes() in (before, content), 'Unexpected local change: ' + op['path']
        if check:
            assert target.exists() and target.read_bytes() == content, op['path']
        outputs.append((target, content))
    if not check:
        for target, content in outputs:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    print(f'PASS: {len(outputs)} CoA delta outputs; approved input hashes and base preimages verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    materialize(parser.parse_args().check)

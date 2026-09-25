#!/usr/bin/env python3
"""Fail closed on missing/stale publications and on loss of version history."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import yaml
from publication_integrity import check_document
from generate_publication import PUBLICATIONS, publication_basename
from publication_versions import resolve_versions, version_key, CLASSIFICATIONS

ROOT = Path(__file__).resolve().parents[1]
# Existing canonical user-approved deferral, pinned before v4. It cannot be
# extended by editing a historical handoff. Future deferrals belong in revisions.
LEGACY_DEFERRALS = {'catalog/master/skladove-karty': (
    'docs/handoffs/skladove-karty/handoff.yaml',
    '6d0fd451e199c1364b7a7725686fa395e8d1f53371cae0e862cc30fc44b5319c')}

def git(root, *args):
    return subprocess.run(['git',*args],cwd=root,check=True,capture_output=True,text=True).stdout

def load(path): return yaml.safe_load(path.read_text())

def current_deferral(root, directory, records):
    deferral = records[-1].get('publication_deferral') if records else None
    if deferral:
        if deferral.get('approved_by')!='user' or not deferral.get('reason') or not deferral.get('evidence_refs'): return False
        manifests={load(p).get('evidence_id'):load(p) for p in (root/'evidence/manifests').rglob('*.yaml')}
        return all(ref in manifests and manifests[ref].get('raw_retained') and
                   (root/manifests[ref]['repository_path']).is_file() and
                   hashlib.sha256((root/manifests[ref]['repository_path']).read_bytes()).hexdigest()==manifests[ref]['sha256']
                   for ref in deferral['evidence_refs'])
    entry=LEGACY_DEFERRALS.get(directory)
    if not entry:return False
    p=root/entry[0]
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry[1]:return False
    hand=load(p)
    return hand['publication']['enabled'] is False and hand['target']['documentation_version'] is None

def generator_digest(root, config):
    path=root/config['generator'];spec=importlib.util.spec_from_file_location('publication_audit_'+path.stem,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.canonical_digest(root)

def audit(root, publications=None):
    root=Path(root); publications=PUBLICATIONS if publications is None else publications;errors=[]
    registered={str(Path(c['revisions']).parent):s for s,c in publications.items()}
    for p in (root/'catalog').rglob('contract.yaml'):
        c=load(p);directory=p.parent.relative_to(root).as_posix()
        if c.get('maturity')=='AGENT-READY' and directory not in registered:
            revisions=p.parent/'revisions.yaml'
            if not revisions.exists() or not current_deferral(root,directory,load(revisions)['records']):
                errors.append('Closed domain has no registered publication or approved deferral: '+directory)
    for p in (root/'generated').glob('*/*.manifest.yaml'):
        if p.parent.name not in publications:errors.append('Published family has no registration: '+p.parent.name)
        try:
            manifest=load(p);base=p.name.removesuffix('.manifest.yaml')
            expected={str(p.parent.relative_to(root)/(base+ext)) for ext in ('.docx','.pdf')}
            if {a['path'] for a in manifest['artifacts']}!=expected:errors.append('Wrong artifact family: '+str(p))
            for a in manifest['artifacts']:
                target=(root/a['path']).resolve()
                if target.parent!=p.parent.resolve():raise ValueError('Artifact escapes publication directory')
                if hashlib.sha256(target.read_bytes()).hexdigest()!=a['sha256']:errors.append('Artifact hash mismatch: '+a['path'])
                errors.extend(a['path']+': '+e for e in check_document(target))
        except Exception as exc:errors.append(f'Invalid manifest/artifact {p}: {exc}')
    for slug,config in publications.items():
        try:
            contract,doc,explicit=resolve_versions(root,config['revisions'])
            p=root/'generated'/slug/(publication_basename(config,doc)+'.manifest.yaml')
            m=load(p)
            if m.get('contract_version')!=contract or (explicit and m.get('documentation_version')!=doc):errors.append('Wrong canonical version: '+slug)
            if m.get('publication_slug')!=slug or m.get('publication_title')!=publication_basename(config,doc):errors.append('Wrong publication identity: '+slug)
            digest,inputs=generator_digest(root,config)
            if m.get('canonical_input_sha256')!=digest or m.get('canonical_inputs')!=inputs:errors.append('Stale canonical input digest: '+slug)
        except Exception as exc:errors.append(f'Publication {slug}: {exc}')
    return errors

def transition_errors(root, base, publications=None):
    publications=PUBLICATIONS if publications is None else publications;errors=[]
    changes=git(root,'diff','--name-status','--no-renames',base,'HEAD').splitlines()
    changed=[]
    for line in changes:
        status,path=line.split('\t',1);changed.append(path)
        if path.startswith('generated/') and status!='A':errors.append('Versioned publication history cannot be overwritten/removed: '+path)
    for path in sorted((root/'catalog').rglob('revisions.yaml')):
        relative=path.relative_to(root).as_posix();directory=path.parent.relative_to(root).as_posix()
        config=next((c for c in publications.values() if c['revisions']==relative),None)
        related=[p for p in changed if p.startswith(directory+'/')]
        if config:
            slug=next(s for s,c in publications.items() if c==config)
            related.extend(p for p in changed if p.startswith(('sql/diagnostic/'+slug+'/', 'evidence/manifests/'+slug+'/', 'evidence/snapshots/'+slug+'/')))
            try:
                oldfiles=git(root,'ls-tree','-r','--name-only',base,'generated').splitlines()
                slug=next(s for s,c in publications.items() if c==config)
                for mf in oldfiles:
                    if mf.startswith('generated/'+slug+'/') and mf.endswith('.manifest.yaml'):
                        m=yaml.safe_load(git(root,'show',base+':'+mf))
                        related.extend(p for p in changed if p in m.get('canonical_inputs',[]))
            except subprocess.CalledProcessError as exc:errors.append(str(exc))
        if not related:continue
        current=load(path)['records']
        try: previous=yaml.safe_load(git(root,'show',base+':'+relative))['records']
        except subprocess.CalledProcessError:previous=[]
        if current[:len(previous)]!=previous:errors.append('Historical revisions changed: '+relative);continue
        added=current[len(previous):]
        if not added:errors.append('Canonical change requires additive revision: '+directory);continue
        for r in added:
            if r.get('change_classification') not in CLASSIFICATIONS:errors.append('Missing change classification: '+r['revision_id'])
            if r.get('publication_impact') not in ('NONE','INITIAL','REGENERATE'):errors.append('Missing publication impact: '+r['revision_id'])
            if r.get('publication_impact')=='NONE' and not r.get('publication_no_impact_reason'):errors.append('NONE requires explicit no-impact reason: '+r['revision_id'])
            if r.get('publication_impact') in ('INITIAL','REGENERATE') and not r.get('documentation_version'):errors.append('Visible change requires approved documentation_version: '+r['revision_id'])
            if r.get('change_classification')=='BREAKING_SEMANTIC' and previous and version_key(r['contract_version'])<=max(version_key(x['contract_version']) for x in previous):errors.append('Breaking change must advance contract_version')
        if config:
            # A new canonical revision on a published domain exits the legacy fallback.
            if not current[-1].get('documentation_version'):errors.append('Next published-domain revision requires explicit documentation_version: '+directory)
            if any(r.get('publication_impact') in ('INITIAL','REGENERATE') for r in added) and previous:
                old_doc=next((r['documentation_version'] for r in reversed(previous) if r.get('documentation_version')),max((r['contract_version'] for r in previous),key=version_key))
                if version_key(current[-1].get('documentation_version',old_doc))<=version_key(old_doc):errors.append('Publication-visible change must advance documentation_version: '+directory)
    return errors

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--base');args=p.parse_args()
    errors=audit(args.root)
    if args.base:
        try:errors+=transition_errors(args.root,args.base)
        except (subprocess.CalledProcessError,ValueError) as exc:errors.append('Cannot verify change history: '+str(exc))
    print(json.dumps({'status':'FAIL' if errors else 'PASS','publication_families':len(PUBLICATIONS),'errors':errors},ensure_ascii=False))
    return bool(errors)

if __name__=='__main__':raise SystemExit(main())

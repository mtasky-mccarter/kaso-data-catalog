"""Version 2 delta intake: targeted base-commit inheritance, never semantic inference."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FINAL = ['python tools/validate_catalog.py', "python -m unittest discover -s tools -p 'test_*.py' -v", 'python tools/check_publication_governance.py', 'python tools/generate_publication.py all --check']

def safe_path(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError(f'Unsafe repository path: {relative}')
    result = (root / p).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes repository: {relative}')
    return result

def ids(value):
    found = set()
    if isinstance(value, dict):
        for k, v in value.items():
            if (k == 'id' or k.endswith('_id')) and isinstance(v, str): found.add(v)
            found.update(ids(v))
    elif isinstance(value, list):
        for v in value: found.update(ids(v))
    return found

def at_base(root, base, relative):
    safe_path(root, relative)
    result = subprocess.run(['git', 'show', f'{base}:{relative}'], cwd=root, capture_output=True, text=True)
    if result.returncode: raise ValueError(f'Missing canonical base path: {relative}')
    return yaml.safe_load(result.stdout)

def validate_lean(data, root=None):
    root = Path(root or ROOT)
    schema = json.loads((ROOT / 'schema/codex-handoff-v2.schema.json').read_text())
    errors = [f"{'.'.join(map(str,e.path))}: {e.message}" for e in Draft202012Validator(schema).iter_errors(data)]
    if errors: return errors, []
    if re.search(r'<[^>]+>', json.dumps(data)): errors.append('Unresolved template placeholder')
    base_maturity = None
    mode = data['mode']; delta = data['delta']; pub = data['publication']; base = data['repository']['base_commit']
    try:
        subprocess.run(['git','cat-file','-e',base+'^{commit}'],cwd=root,check=True,capture_output=True)
        if mode != 'REPOSITORY_GOVERNANCE':
            canonical = data['scope']['canonical_path']
            safe_path(root,canonical)
            if not canonical.startswith('catalog/'): raise ValueError('canonical_path must be under catalog/')
        if mode not in ('CREATE_DOMAIN','REPOSITORY_GOVERNANCE'):
            inherited = data['canonical_base']
            contract = at_base(root,base,canonical.rstrip('/')+'/contract.yaml')
            base_maturity = contract.get('maturity')
            revisions = at_base(root,base,canonical.rstrip('/')+'/revisions.yaml')
            if contract['contract_id'] != inherited['contract_ref']: errors.append('canonical contract_ref does not match base')
            if inherited['revision_ref'] not in ids(revisions): errors.append('canonical revision_ref missing at base')
            if contract['authoritative_environment'] != data['scope']['authoritative_environment']: errors.append('Authoritative environment conflicts with base')
        approved_ids = set()
        for item in data['approved_inputs']:
            p = safe_path(root,item['path']); content=p.read_bytes()
            if hashlib.sha256(content).hexdigest()!=item['sha256']: errors.append('Checksum mismatch: '+item['path'])
            if p.suffix in ('.yaml','.yml','.json'): approved_ids.update(ids(yaml.safe_load(content)))
        for ref in delta['approved_evidence_refs']+delta['approved_delta_refs']:
            if ref not in approved_ids: errors.append('Approved reference missing from checksummed inputs: '+ref)
        if mode=='CREATE_DOMAIN':
            exists = subprocess.run(['git','cat-file','-e',base+':'+canonical.rstrip('/')+'/contract.yaml'],cwd=root,capture_output=True).returncode == 0
            if exists: errors.append('CREATE_DOMAIN cannot replace an existing canonical domain')
            package=data['materialization_package']
            if package['path'] not in {i['path'] for i in data['approved_inputs']}: errors.append('Materialization package must be checksummed in approved_inputs')
            if not data['execution']['materializer_commands']: errors.append('CREATE_DOMAIN requires deterministic materializer command')
        if mode not in ('CREATE_DOMAIN','REPOSITORY_GOVERNANCE'):
            known=set(approved_ids)
            for path in data['delta']['record_paths']:
                known.update(ids(at_base(root,base,path)))
            for ref in delta['changed_record_refs']:
                if ref not in known: errors.append('Changed record missing from targeted base/package records: '+ref)
        for path in data['repository_actions']['create_or_update']+data['repository_actions']['preserve']+data['repository_actions']['forbidden']:
            safe_path(root,path)
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as exc:
        errors.append('Canonical intake failed: '+str(exc))
    if data.get('target',{}).get('maturity',base_maturity)=='AGENT-READY' and data['backlog_delta']['blocking_count']!=0:
        errors.append('AGENT-READY requires zero resulting blocking items')
    if mode=='CLOSURE' and pub['impact'] not in ('INITIAL','REGENERATE') and not pub.get('deferral'):
        errors.append('CLOSURE requires publication or explicit user-approved canonical deferral')
    if pub['impact']!='NONE' and not pub.get('documentation_version'): errors.append('Publication requires approved documentation_version')
    if pub.get('deferral') and pub['deferral']['evidence_ref'] not in delta['approved_evidence_refs']:
        errors.append('Deferral requires approved user evidence reference')
    if delta['classification']=='BREAKING_SEMANTIC' and not data.get('target',{}).get('contract_version'):
        errors.append('BREAKING_SEMANTIC requires approved contract_version')
    if mode in ('PUBLICATION_ONLY','REPOSITORY_GOVERNANCE') and delta['semantic_change']:
        errors.append('This mode cannot authorize semantic changes')
    if mode != 'REPOSITORY_GOVERNANCE':
        for key in ('approved_delta_refs','approved_evidence_refs'):
            if not delta[key]: errors.append('Delta completeness requires '+key)
        if not data['approved_inputs']: errors.append('Checksummed approved inputs are required')
    if mode in ('UPDATE_DOMAIN','EVIDENCE_REFRESH') and not delta['changed_record_refs']:
        errors.append('Changed record refs are required for a domain delta')
    if pub.get('deferral') and pub['deferral']['canonical_revision_ref'] != delta['revision_id']:
        errors.append('Deferral must be recorded in the approved delta revision')
    if delta['semantic_change'] != (delta['classification'] in ('BREAKING_SEMANTIC','NON_BREAKING_SEMANTIC')):
        errors.append('semantic_change conflicts with classification')
    return errors, []

def execution_plan(data):
    if data.get('schema_version')!='2.0':
        return {'mode':'LEGACY_HANDOFF','base_sha':data['repository']['base_commit'],'domain':data['scope']['domain'],
                'affected_canonical_paths':[data['scope']['canonical_path']], 'evidence_paths':[], 'changed_record_refs':[],
                'materializer_commands':[], 'domain_tests':data.get('acceptance',{}).get('required_domain_tests',[]),
                'publication_action':data.get('publication',{}),'final_validation_commands':FINAL,
                'stop_conditions':['Legacy handoff: use its approved scope; do not infer missing delta intent.']}
    return {'mode':data['mode'],'base_sha':data['repository']['base_commit'],'domain':data['scope']['domain'],
            'affected_canonical_paths':data['repository_actions']['create_or_update'],
            'evidence_paths':[i['path'] for i in data['approved_inputs']],
            'changed_record_refs':data['delta']['changed_record_refs'],
            'materializer_commands':data['execution']['materializer_commands'],
            'domain_tests':data['execution']['domain_tests'], 'sql_tests':data['execution']['sql_tests'],
            'publication_tests':data['execution']['publication_tests'], 'publication_action':data['publication'],
            'final_validation_commands':[c+' --base '+data['repository']['base_commit'] if c=='python tools/check_publication_governance.py' else c for c in FINAL],'stop_conditions':data['stop_conditions']}

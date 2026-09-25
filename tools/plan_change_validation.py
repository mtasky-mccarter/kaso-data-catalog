#!/usr/bin/env python3
"""Conservative deterministic validation routing from a Git diff."""
import argparse
import json
import subprocess
from pathlib import Path
from generate_publication import PUBLICATIONS

ROOT=Path(__file__).resolve().parents[1]
ROUTES={
 'skladove-karty':('catalog/master/skladove-karty/','pm'),
 'obchodne-pripady':('catalog/sales/obchodne-pripady/','odb'),
 'nakupne-objednavky':('catalog/purchasing/','pur'),
 'cestovne-prikazy':('catalog/transport/cestovne-prikazy/','cp'),
 'vydajky':('catalog/warehouse/vydajky/','vyd'),
}

def plan(paths, root=ROOT):
    paths=sorted(set(paths)); affected=set();unknown=False
    for path in paths:
        matched=False
        for slug,(canonical,prefix) in ROUTES.items():
            if path.startswith((canonical,'sql/diagnostic/'+slug+'/','evidence/manifests/'+slug+'/','evidence/snapshots/'+slug+'/','generated/'+slug+'/','docs/handoffs/'+slug+'/')) or Path(path).name.startswith(('test_'+prefix+'_','generate_'+prefix+'_','materialize_'+prefix)):
                affected.add(slug);matched=True
        if path.startswith(('catalog/','sql/','evidence/','generated/')) and not matched:unknown=True
    tooling=any(p.startswith(('tools/','schema/','.github/workflows/')) or p in ('requirements-dev.txt','docs/publication-standard.md') for p in paths)
    publication=tooling or unknown or any(p.startswith(('catalog/','sql/','evidence/','generated/','docs/handoffs/')) for p in paths)
    tests=[]
    for slug in sorted(affected):
        prefix=ROUTES[slug][1]
        tests += [f'python -m unittest discover -s tools -p {p.name} -v' for p in sorted((root/'tools').glob('test_'+prefix+'_*.py'))]
    return {'affected_domains':sorted(affected),'domain_tests':tests,'sql_safety_affected':unknown or tooling or any(p.startswith('sql/') for p in paths),
            'evidence_validation_affected':unknown or tooling or any(p.startswith('evidence/') for p in paths),
            'publication_affected':publication,'repository_wide_publication_check':publication,
            'publication_commands':['python tools/generate_publication.py all --check'] if publication else [],
            'final_validation_commands':['python tools/validate_catalog.py',"python -m unittest discover -s tools -p 'test_*.py' -v",'python tools/check_publication_governance.py'],
            'unknown_scope_requires_full_validation':unknown}

def main():
    p=argparse.ArgumentParser();p.add_argument('--base',default='origin/main');p.add_argument('--head',default='HEAD');p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--github-output',type=Path);args=p.parse_args()
    result=subprocess.run(['git','diff','--name-only','--no-renames',args.base,args.head],cwd=args.root,check=True,capture_output=True,text=True)
    data=plan(result.stdout.splitlines(),args.root);print(json.dumps(data,separators=(',',':')))
    if args.github_output:
        with args.github_output.open('a') as f:f.write('publication_check='+str(data['repository_wide_publication_check']).lower()+'\n')

if __name__=='__main__':main()

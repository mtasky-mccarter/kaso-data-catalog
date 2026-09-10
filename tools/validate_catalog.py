#!/usr/bin/env python3
"""Offline structural and reference validation; never executes SQL or promotes facts."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
FORMATS = FormatChecker()


@FORMATS.checks('date-time', raises=ValueError)
def timestamp_format(value):
    # jsonschema's date-time checker otherwise needs an optional extra package.
    if not isinstance(value, str):
        return True
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)', value):
        return False
    datetime.fromisoformat(value.upper().replace('Z', '+00:00'))
    return True


class CatalogLoader(yaml.SafeLoader):
    """JSON-compatible YAML: no aliases, duplicate keys or ambiguous identifiers."""

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise ValueError('YAML aliases are not supported; use stable record references')
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ValueError('Mapping keys must be strings')
            if key in result:
                raise ValueError(f'Duplicate YAML key: {key}')
            result[key] = self.construct_object(value_node, deep=deep)
        return result


CatalogLoader.yaml_implicit_resolvers = {
    key: [(tag, regex) for tag, regex in resolvers
          if tag not in ('tag:yaml.org,2002:timestamp', 'tag:yaml.org,2002:bool')]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
CatalogLoader.add_implicit_resolver(
    'tag:yaml.org,2002:bool', re.compile(r'^(?:true|false)$'), list('tf'))


def strict_integer(loader, node):
    raw = node.value
    if not re.fullmatch(r'-?(?:0|[1-9][0-9]*)', raw):
        raise ValueError(f'Quote numeric-looking identifiers or use decimal integers: {raw}')
    return int(raw)


CatalogLoader.add_constructor('tag:yaml.org,2002:int', strict_integer)


def json_value(value):
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if isinstance(value, list):
        for item in value:
            json_value(item)
        return
    if isinstance(value, dict) and all(isinstance(k, str) for k in value):
        for item in value.values():
            json_value(item)
        return
    raise ValueError('YAML must contain JSON-compatible values (no dates as objects, sets or NaN)')


def load_yaml(path):
    value = yaml.load(Path(path).read_text(encoding='utf-8'), Loader=CatalogLoader)
    json_value(value)
    return value


def validators():
    schemas = [json.loads(p.read_text(encoding='utf-8'))
               for p in sorted((ROOT / 'schema').glob('*.schema.json'))]
    registry = Registry()
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(schema['$id'], Resource.from_contents(schema))
    return {
        s['properties']['kind']['const']: Draft202012Validator(
            s, registry=registry, format_checker=FORMATS)
        for s in schemas if 'properties' in s
    }


def validate_document(document, checks=None):
    checks = checks if checks is not None else validators()
    if not isinstance(document, dict):
        return ['document must be a mapping']
    kind = document.get('kind')
    if not isinstance(kind, str) or kind not in checks:
        return [f'unknown or missing kind: {kind!r}']
    return [f'{"/".join(map(str, e.absolute_path)) or "<root>"}: {e.message}'
            for e in sorted(checks[kind].iter_errors(document), key=lambda e: str(e.absolute_path))]


def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def validate_bundle(documents, root=ROOT):
    """documents is a mapping of display paths to parsed documents."""
    errors = []
    checks = validators()
    for path, doc in documents.items():
        errors.extend(f'{path}: {message}' for message in validate_document(doc, checks))
    if errors:
        return errors
    ids = {}
    for path, doc in documents.items():
        for record in walk(doc):
            for key, value in record.items():
                if key == 'id' or key.endswith('_id'):
                    if value in ids:
                        errors.append(f'{path}: duplicate ID {value}')
                    else:
                        ids[value] = (path, record)
    for path, doc in documents.items():
        for record in walk(doc):
            for key, value in record.items():
                targets = value if key.endswith('_refs') else [value] if key.endswith('_ref') else []
                for target in targets:
                    if target is not None and target not in ids:
                        errors.append(f'{path}: unresolved {key}: {target}')
            evidence = record.get('evidence_refs', [])
            for target in evidence + record.get('related_evidence_refs', []):
                if target in ids and ids[target][1].get('kind') != 'evidence-manifest':
                    errors.append(f'{path}: evidence reference is not a manifest: {target}')
            proved = record.get('status') == 'POTVRDENÉ'
            classified_role = record.get('role') in (
                'DIRECT WRITER', 'API WRITER', 'INDIRECT WRITER',
                'TRIGGER SIDE EFFECT', 'READER', 'CALLER')
            if proved or classified_role:
                if not any(e in ids and ids[e][1].get('kind') == 'evidence-manifest'
                           and ids[e][1].get('evidence_class') != 'E' for e in evidence):
                    errors.append(f'{path}: confirmed facts and writer/reader/caller roles require non-E evidence')
            if 'sql_file' in record:
                file = (root / record['sql_file']).resolve()
                if not file.is_relative_to(root.resolve()) or not file.is_file():
                    errors.append(f'{path}: SQL file missing or outside repository: {record["sql_file"]}')
        if doc['kind'] == 'evidence-manifest' and doc['raw_retained']:
            rel = doc.get('repository_path')
            if not rel:
                errors.append(f'{path}: raw_retained requires repository_path')
            else:
                file = (root / rel).resolve()
                if not file.is_relative_to(root.resolve()) or not file.is_file():
                    errors.append(f'{path}: retained evidence file missing or outside repository: {rel}')
                elif doc.get('sha256') and hashlib.sha256(file.read_bytes()).hexdigest() != doc['sha256'].lower():
                    errors.append(f'{path}: retained evidence SHA-256 mismatch')
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', type=Path,
                        help='YAML files/directories; include all referenced records together')
    args = parser.parse_args(argv)
    paths = args.paths or [ROOT / 'catalog', ROOT / 'evidence/manifests', ROOT / 'examples']
    files = set()
    for path in paths:
        if not path.exists():
            parser.error(f'path does not exist: {path}')
        if path.is_dir():
            files.update(p for p in path.rglob('*') if p.suffix.lower() in ('.yaml', '.yml'))
        elif path.suffix.lower() in ('.yaml', '.yml'):
            files.add(path)
        else:
            parser.error(f'not a YAML file: {path}')
    if not files:
        parser.error('no YAML files found')
    documents = {}
    errors = []
    for path in sorted(files):
        try:
            documents[str(path)] = load_yaml(path)
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            errors.append(f'{path}: {exc}')
    errors.extend(validate_bundle(documents))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f'PASS: {len(documents)} YAML documents; structure, IDs, references and retained files checked')
    return 0


if __name__ == '__main__':
    sys.exit(main())

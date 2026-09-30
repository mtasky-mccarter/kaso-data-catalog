"""Publication closure fidelity, authorization, preservation and document integrity."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import yaml
from pypdf import PdfReader
import materialize_obchodni_partneri as initial
import materialize_op_publication as metadata
from generate_op_publication import model, blocks, decoded, value_text, canonical_digest
from publication_integrity import check_document

ROOT=initial.ROOT
BASE='KASO Data Catalog - Technical & Diagnostic Reference - obchodní partneri v1.0'
DIR=ROOT/'generated/obchodni-partneri'
def normalized(value):
    return re.sub(r'\s+','',str(value).replace('\u200b',''))
def leaves(value):
    if isinstance(value,dict):
        for child in value.values(): yield from leaves(child)
    elif isinstance(value,list):
        for child in value: yield from leaves(child)
    else: yield value

class OPPublication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=model(ROOT)
        with ZipFile(DIR/(BASE+'.docx')) as archive:
            cls.xml=ET.fromstring(archive.read('word/document.xml'))
        cls.docx=normalized(''.join(cls.xml.itertext()))
        cls.pdf=normalized('\n'.join('\n'.join(line for line in p.extract_text().splitlines()
            if not line.startswith('mtasky-mccarter/kaso-data-catalog | main |') and not line.isdigit())
            for p in PdfReader(DIR/(BASE+'.pdf')).pages))

    def test_complete_fields_and_all_sql_in_both_outputs(self):
        fields=self.data['docs']['fields.yaml']['records']
        self.assertEqual(87,len(fields))
        self.assertEqual(7,len(self.data['sql']))
        for text in (self.docx,self.pdf):
            for leaf in leaves(fields):
                self.assertTrue(normalized(value_text(leaf)) in text,str(leaf))
            for sql in self.data['sql'].values():
                self.assertTrue(normalized(sql) in text, "SQL text incomplete after removing page furniture")

    def test_semantic_rules_and_uncertainty_preserved(self):
        for name in ['relationships.yaml','flows.yaml','mutations.yaml','temporal.yaml',
                     'boundaries.yaml','data-quality.yaml','backlog.yaml','do-not-assume.yaml','revisions.yaml']:
            for leaf in leaves(decoded(self.data['docs'][name]['records'])):
                for text in (self.docx,self.pdf):
                    self.assertTrue(normalized(value_text(leaf)) in text,(name,str(leaf)))
        headings=[b[2] for b in blocks(self.data) if b[0]=='heading' and b[1]==1]
        self.assertEqual(21,len(headings))
        for heading in headings:
            self.assertIn(normalized(heading),self.pdf)

    def test_manifest_and_integrity(self):
        manifest=yaml.safe_load((DIR/(BASE+'.manifest.yaml')).read_text())
        self.assertEqual('1.0',manifest['documentation_version'])
        self.assertEqual('1.0',manifest['contract_version'])
        self.assertEqual('obchodni-partneri',manifest['publication_slug'])
        digest,paths=canonical_digest(ROOT)
        self.assertEqual(digest,manifest['canonical_input_sha256'])
        self.assertEqual(paths,manifest['canonical_inputs'])
        for artifact in manifest['artifacts']:
            path=ROOT/artifact['path']
            self.assertEqual(DIR,path.parent)
            self.assertEqual(artifact['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual([],check_document(path))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        for table in self.xml.findall('.//w:tbl',ns):
            widths=[int(c.attrib['{'+ns['w']+'}w']) for c in table.findall('./w:tblGrid/w:gridCol',ns)]
            self.assertLessEqual(sum(widths),15140)
            self.assertTrue(table.findall('.//w:tblHeader',ns))

    def test_metadata_exact_delta_and_initial_history(self):
        delta=metadata.approved_delta(ROOT)
        before=yaml.safe_load(subprocess.check_output(['git','show',
            '5a8cca22f90003510b5d45442dca71088b80ea15:catalog/master/obchodni-partneri/revisions.yaml'],cwd=ROOT))
        after=self.data['docs']['revisions.yaml']
        self.assertEqual(before['records'],after['records'][:-1])
        self.assertEqual(delta['revision'],after['records'][-1])
        for path,value in metadata.project(ROOT).items():
            self.assertEqual(value,yaml.safe_load((ROOT/path).read_text()))
        self.assertEqual(metadata.project(ROOT),metadata.project(ROOT))

    def test_original_materializer_preserves_closure_and_rejects_unknown_revision(self):
        package=yaml.safe_load((ROOT/initial.INPUT).read_text())
        docs,files=initial.project(package,ROOT)
        initial.preserve_closure(ROOT,docs,files)
        for path in metadata.project(ROOT):
            self.assertEqual((ROOT/path).read_bytes(),files[path].encode())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for rel in [metadata.HANDOFF,metadata.DELTA,metadata.APPROVAL,*map(Path,metadata.project(ROOT))]:
                (root/rel).parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/rel,root/rel)
            rev=root/initial.DOMAIN/'revisions.yaml'
            value=yaml.safe_load(rev.read_text())
            value['records'].append(dict(revision_id='op.revision.future'))
            rev.write_text(yaml.safe_dump(value))
            docs,files=initial.project(package,ROOT)
            with self.assertRaisesRegex(ValueError,'Later revision'):
                initial.preserve_closure(root,docs,files)
            (root/metadata.DELTA).write_text('{}')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                metadata.approved_delta(root)

if __name__=='__main__': unittest.main()

"""Product Master publication identity, semantic fidelity and deterministic output."""
import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import unicodedata
import yaml
from reportlab.pdfbase.ttfonts import TTFont
from generate_publication import PUBLICATIONS, current_version, publication_basename
from generate_pm_publication import FONT_DIR, blocks, model, value_text, canonical_digest

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'generated/skladove-karty'
BASE='KASO Data Catalog - Technical & Diagnostic Reference - skladové karty v1.0'
def normalized(text):return re.sub(r'\s+','',unicodedata.normalize('NFC',str(text)).replace('\u200b',''))

class ProductMasterPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=model(ROOT)
        cls.manifest=yaml.safe_load((DIR/(BASE+'.manifest.yaml')).read_text())
        with ZipFile(DIR/(BASE+'.docx')) as z:
            cls.xml=ET.fromstring(z.read('word/document.xml'))
        cls.text=normalized(''.join(cls.xml.itertext()))

    def test_registration_revision_identity_and_hashes(self):
        config=PUBLICATIONS['skladove-karty']
        self.assertEqual('skladové karty',config['subject_sk'])
        self.assertEqual('catalog/master/skladove-karty/revisions.yaml',config['revisions'])
        self.assertEqual('1.0',current_version(ROOT,config))
        self.assertEqual(BASE,publication_basename(config,'1.0'))
        m=self.manifest
        self.assertEqual('pm.contract.skladove_karty.1_0',m['contract_ref'])
        self.assertEqual('1.0',m['contract_version'])
        self.assertEqual('skladove-karty',m['publication_slug'])
        self.assertEqual(BASE,m['publication_title'])
        digest,paths=canonical_digest(ROOT)
        self.assertEqual(digest,m['canonical_input_sha256']);self.assertEqual(paths,m['canonical_inputs'])
        expected={f'generated/skladove-karty/{BASE}{ext}' for ext in ['.docx','.pdf']}
        self.assertEqual(expected,{r['path'] for r in m['artifacts']})
        for a in m['artifacts']:
            p=ROOT/a['path'];self.assertTrue(p.is_file());self.assertEqual(p.parent,DIR)
            self.assertEqual(a['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
        self.assertFalse(any(p.name.startswith('skladove-karty') for p in (ROOT/'generated').iterdir() if p.is_file()))

    def test_complete_root_fields_and_sql_are_present(self):
        fields=self.data['docs']['fields-sklad_karta.yaml']['records']
        self.assertEqual(169,len(fields));self.assertEqual(169,len({r['canonical_alias'] for r in fields}))
        def leaves(value):
            if isinstance(value,dict):
                for v in value.values():yield from leaves(v)
            elif isinstance(value,list):
                for v in value:yield from leaves(v)
            else:yield value
        for value in leaves([{k:v for k,v in r.items() if k!='field_id'} for r in fields]):self.assertIn(normalized(value_text(value)),self.text,str(value))
        self.assertEqual(25,len(self.data['sql']))
        for sql in self.data['sql'].values():self.assertIn(normalized(sql),self.text)

    def test_core_semantic_records_and_uncertainty_are_preserved(self):
        for name in ['flows.yaml','mutations.yaml','temporal.yaml','data-quality.yaml','backlog.yaml','playbooks.yaml','revisions.yaml','do-not-assume.yaml']:
            for r in self.data['docs'][name]['records']:
                for key,value in r.items():self.assertIn(normalized(value_text(value)),self.text,(name,key))
        for status in ['TREBA OVERIŤ','DATA GAP','DEPENDENCY ONLY','TECHNICKY ZNÁME','POTVRDENÉ — VYRIEŠENÉ']:
            self.assertIn(normalized(status),self.text)
        self.assertIn(normalized('BITAND(NEW.STAV,2)=2'),self.text)
        self.assertIn(normalized('Not a global lock bypass'),self.text)
        backlog=self.data['docs']['backlog.yaml']['records'];self.assertEqual(7,len(backlog));self.assertFalse(any(r['blocking'] for r in backlog))

    def test_headings_toc_and_classified_inputs(self):
        b=blocks(self.data);titles=[x[2] for x in b if x[0]=='heading' and x[1]==1]
        self.assertEqual(17,len(titles));self.assertEqual(17,len(set(titles)))
        for title in titles:self.assertIn(normalized(title),self.text)
        for path in self.data['inputs']:self.assertIn(normalized(path),self.text)
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        styles=[e.attrib.get('{'+ns['w']+'}val') for e in self.xml.findall('.//w:pStyle',ns)]
        self.assertIn('Title',styles);self.assertIn('Heading1',styles)
        self.assertTrue(self.xml.findall('.//w:tblHeader',ns))

    def test_publication_gate_and_historical_revision(self):
        hand=yaml.safe_load((ROOT/'docs/handoffs/skladove-karty/handoff.yaml').read_text())
        self.assertTrue(hand['publication']['enabled']);self.assertEqual('1.0',hand['target']['documentation_version'])
        revs=self.data['docs']['revisions.yaml']['records']
        self.assertTrue(any('publications deferred' in r['change_sk'] for r in revs))
        current=next(r for r in revs if r['revision_id']=='pm.revision.1_0_publication_20260923')
        self.assertFalse(current['breaking_change'])
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'docs/handoffs/skladove-karty/handoff.yaml';p.parent.mkdir(parents=True)
            hand['publication']['enabled']=False;p.write_text(yaml.safe_dump(hand))
            with self.assertRaisesRegex(ValueError,'not approved'):model(root)

    def test_pdf_fonts_cover_rendered_characters(self):
        chars=set(str(blocks(self.data)))
        for path in FONT_DIR.glob('*.ttf'):
            f=TTFont(path.stem,path)
            self.assertEqual([],sorted(c for c in chars if ord(c)>32 and ord(c) not in f.face.charToGlyph))

    def test_publication_is_deterministically_current(self):
        subprocess.run([sys.executable,str(ROOT/'tools/generate_publication.py'),'skladove-karty','--check'],cwd=ROOT,check=True)

if __name__=='__main__':unittest.main()

"""Cheap structural/Unicode/page sanity without rendering document pages."""
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from pypdf import PdfReader

def check_document(path):
    errors=[]
    if path.suffix=='.docx':
        with ZipFile(path) as z:
            if z.testzip():errors.append('Corrupt DOCX ZIP')
            document=ET.fromstring(z.read('word/document.xml'))
            if '\ufffd' in ''.join(document.itertext()):errors.append('Replacement Unicode character in DOCX')
            ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            if not document.findall('.//w:p',ns):errors.append('Empty DOCX')
            for size in document.findall('.//w:pgSz',ns):
                if any(int(size.get('{'+ns['w']+'}'+k,'0'))<=0 for k in ('w','h')):errors.append('Invalid DOCX page geometry')
    else:
        reader=PdfReader(path,strict=True)
        if not reader.pages:errors.append('Empty PDF')
        for i,page in enumerate(reader.pages,1):
            if not (0<float(page.mediabox.width)<14400 and 0<float(page.mediabox.height)<14400):errors.append(f'Invalid PDF page geometry: {i}')
            text=page.extract_text()
            if '\ufffd' in text:errors.append(f'Replacement Unicode character in PDF page {i}')
            if page.get_contents() is None:errors.append(f'Missing PDF page content: {i}')
    return errors

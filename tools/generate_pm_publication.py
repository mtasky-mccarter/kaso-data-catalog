#!/usr/bin/env python3
"""Product Master reference publication from canonical YAML and SQL only.

Both renderers consume the same ordered blocks. Shared record properties are
factored out once per registry; every remaining property is printed per record.
No business definitions, formulas or population counts are maintained here.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import textwrap
from itertools import groupby
from datetime import datetime, timezone
from pathlib import Path

import unicodedata
import yaml
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, TableStyle,
)

from generate_cp_publication import normalize_docx

REPOSITORY = "mtasky-mccarter/kaso-data-catalog"
DOMAIN = Path("catalog/master/skladove-karty")
SQL_DIR = Path("sql/diagnostic/skladove-karty")
EVIDENCE = Path("evidence/manifests/skladove-karty")
# An intermediate name required by the existing publication orchestrator.
BASENAME = "skladove-karty-v1.0"
FIXED_TIME = datetime(2000, 1, 1, tzinfo=timezone.utc)
FONT_DIR = Path(__file__).resolve().parent / "fonts/liberation"

# Presentation labels only. Values and all semantic prose come from YAML.
LABELS = {
    "business_definition_sk": "Význam", "limitations_sk": "Obmedzenia",
    "evidence_refs": "Dôkazy", "related_evidence_refs": "Súvisiace dôkazy",
    "status": "Status", "canonical_alias": "Alias", "datatype_raw": "Datatype",
    "nullable": "Nullable", "default_raw": "Default", "oracle_comment": "Oracle comment",
    "ordinal_position": "Poradie", "scope_refs": "Scope", "scope_ref": "Scope",
    "condition_sk": "Podmienka", "fanout_risk": "Fan out riziko",
    "safe_usage_sk": "Bezpečné použitie", "classification": "Klasifikácia",
    "transition_or_event_sk": "Udalosť alebo pravidlo", "history_limitations_sk": "Limity histórie",
    "reconstructable": "Rekonštruovateľné", "result_grain_sk": "Grain výsledku",
    "proves_sk": "Dokazuje", "does_not_prove_sk": "Nedokazuje",
    "question_sk": "Otvorená otázka", "reason_sk": "Dôvod", "blocking": "Blokujúce",
    "change_sk": "Zmena", "breaking_change": "Breaking change", "snapshot_date": "Snapshot",
    "statement_sk": "Pravidlo", "consequence_sk": "Dôsledok", "event_sk": "Udalosť",
    "business_effect_sk": "Business efekt", "diagnostic_meaning_sk": "Diagnostický význam",
    "direct_mutations_sk": "Priama mutácia", "writer_role": "Rola zapisovateľa",
    "first_sql_ref": "Prvá diagnostika", "symptom_sk": "Symptóm", "next_step_sk": "Ďalší krok",
    "fanout_warning_sk": "Fan out a obmedzenia", "input_parameters": "Vstupné parametre",
    "business_label_sk": "Business label", "raw_value": "Raw hodnota", "source_ref": "Zdroj",
    "target_ref": "Cieľ", "role": "Rola", "hit_lines": "Riadky zdroja", "hit_count": "Počet výskytov",
}


def label(key):
    return LABELS.get(key, key.replace("_", " "))


def value_text(value):
    """Keep null, booleans and code strings visibly distinct; never invent meaning."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        value = unicodedata.normalize("NFC", value)
        return json.dumps(value, ensure_ascii=False) if value.isdigit() and value.startswith("0") else value
    if isinstance(value, list):
        return "[]" if not value else "\n".join(value_text(v) for v in value)
    if isinstance(value, dict):
        return "{}" if not value else "\n".join(f"{label(k)}: {value_text(v)}" for k, v in value.items())
    return str(value)


def canonical_paths(root):
    return (sorted((root / DOMAIN).glob("*.yaml"))
            + sorted((root / SQL_DIR).glob("*.sql"))
            + sorted((root / EVIDENCE).glob("*.yaml")))


def canonical_digest(root):
    digest = hashlib.sha256()
    paths = canonical_paths(root)
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), [p.relative_to(root).as_posix() for p in paths]


def model(root):
    handoff = yaml.safe_load((root / "docs/handoffs/skladove-karty/handoff.yaml").read_text())
    if handoff["publication"]["enabled"] is not True or handoff["target"]["documentation_version"] != "1.0":
        raise ValueError("Product Master publication is not approved for version 1.0")
    docs = {p.name: yaml.safe_load(p.read_text()) for p in sorted((root / DOMAIN).glob("*.yaml"))}
    evidence = {p.name: yaml.safe_load(p.read_text()) for p in sorted((root / EVIDENCE).glob("*.yaml"))}
    if docs["contract.yaml"]["maturity"] != "AGENT-READY" or any(r["blocking"] for r in docs["backlog.yaml"]["records"]):
        raise ValueError("Product Master readiness gate failed")
    registry = docs["sql-registry.yaml"]["records"]
    sql = {}
    for row in registry:
        path = (root / row["sql_file"]).resolve()
        if path.parent != (root / SQL_DIR).resolve() or path.suffix != ".sql":
            raise ValueError(f"SQL cesta mimo skladových kariet: {path}")
        sql[row["sql_id"]] = path.read_text()
    if {r["sql_file"] for r in registry} != {p.relative_to(root).as_posix() for p in (root / SQL_DIR).glob("*.sql")}:
        raise ValueError("SQL register nepokrýva kanonické SQL skladových kariet")
    versions = {r["contract_version"] for r in docs["revisions.yaml"]["records"]}
    version = max(versions, key=lambda v: tuple(int(n) for n in v.split(".")))
    digest, inputs = canonical_digest(root)
    return {"docs": docs, "evidence": evidence, "sql": sql, "version": version,
            "subject": "skladové karty", "digest": digest, "inputs": inputs}


def registry_parts(records):
    """Factor identical values, without truncation or lossy summarization."""
    if not records:
        return {}, []
    common = {k: v for k, v in records[0].items()
              if len(records) > 1 and all(k in r and r[k] == v for r in records)}
    return common, [{k: v for k, v in r.items() if k not in common} for r in records]


def blocks(data):
    """Human-readable core reference plus explicitly scoped technical summaries."""
    from collections import Counter
    docs = data['docs']; out = []; consumed = set()
    def heading(title, level=1): out.append(('heading',level,title))
    def paragraph(text): out.append(('paragraph',str(text)))
    def table(headers, rows, widths):
        if rows: out.append(('table',headers,rows,widths))
    def properties(row):
        for k,v in row.items(): paragraph(f'{label(k)}: {value_text(v)}')
    def source(name):
        consumed.add(name)
        paragraph('Kanonický zdroj: '+str(DOMAIN/name))
        return docs[name]
    def narrative(name,title):
        heading(title,2); document=source(name)
        for row in document.get('records',[document]):
            identity=next((v for k,v in row.items() if k.endswith('_id')),document.get('id',title))
            heading(str(identity),3)
            properties(row)
    def dense(name,title):
        heading(title,2); records=source(name).get('records',[])
        common,rows=registry_parts(records)
        if common:
            paragraph('Spoločné vlastnosti nasledujúcich záznamov');properties(common)
        values=[]
        if name.startswith('fields-'):
            records=docs[name]['records']
            field_rows=[]
            for row in records:
                identity=f"{row['ordinal_position']}  {row['oracle_name']}\nAlias: {value_text(row.get('canonical_alias'))}"
                technical=f"{row['datatype_raw']}\nNullable: {value_text(row['nullable'])}\nDefault: {value_text(row.get('default_raw'))}"
                details=f"{row['status']}\nVýznam: {value_text(row.get('business_definition_sk'))}\nOracle comment: {value_text(row.get('oracle_comment'))}"
                extra={k:v for k,v in row.items() if k not in common and k not in ('field_id','oracle_name','ordinal_position','canonical_alias','datatype_raw','nullable','default_raw','status','business_definition_sk','oracle_comment')}
                if extra:details+='\n'+'; '.join(f'{label(k)}: {value_text(v).replace(chr(10),chr(32))}' for k,v in extra.items())
                field_rows.append([identity,technical,details])
            table(['Pole a alias','Typ nullable a default','Status význam komentár a pôvod'],field_rows,[60,45,162])
            return
        for row in rows:
            ids={k:v for k,v in row.items() if k.endswith('_id') or k in ('oracle_name','ordinal_position')}
            if 'oracle_name' in row: ids={k:v for k,v in ids.items() if not k.endswith('_id')}
            detail={k:v for k,v in row.items() if k not in ids and not (k.endswith('_id') and 'oracle_name' in row)}
            values.append(['; '.join(value_text(v) for k,v in ids.items()), '; '.join(f'{label(k)}: {value_text(v).replace(chr(10), chr(32))}' for k,v in detail.items())])
        table(['Identita','Kanonické vlastnosti'],values,[62,205])

    heading('1 Účel rozsah a orientácia')
    contract=source('contract.yaml')
    paragraph(contract['purpose_sk'])
    paragraph('Referencia skladových kariet slúži na bezpečné čítanie aktuálneho mastera, interpretáciu jeho satelitov a diagnostiku. Kanonické YAML a SQL sú autoritou; dokument je ich odvodená publikácia.')
    properties({k:v for k,v in contract.items() if k not in ('component_refs','object_refs','schema_version','kind')})
    paragraph('Hodnota null označuje kanonicky chýbajúcu hodnotu. Oracle comments sú technické komentáre, nie samostatná business autorita. Statusy TREBA OVERIŤ, DATA GAP, DEPENDENCY ONLY a TECHNICKY ZNÁME sa nemenia publikovaním.')
    paragraph('Úplný inventár root polí a diagnostické SQL sú nižšie. Rozsiahle Oracle entity, raw source windows, inbound FK a lexikálne API referencie sú uvedené prehľadovo s presnými zdrojmi; ich úplné záznamy ostávajú v kanonickom katalógu, ktorý je zahrnutý v kontrolnom súčte publikácie.')

    heading('2 Identita grain a schválené významové pravidlá')
    rules=source('do-not-assume.yaml')['records']
    consolidated=[r for r in rules if r['rule_id'].startswith('pm.rule.handoff_section_')]
    for row in consolidated:
        heading(row['rule_id'],2);properties(row)

    heading('3 Fyzické objekty a úplný root inventár')
    for name in sorted(n for n in docs if n.startswith('object-')):
        d=source(name);heading(d['oracle_name'],2)
        properties({k:v for k,v in d.items() if k not in ('schema_version','kind')})
    paragraph('Nasledujúci root inventár obsahuje všetky vlastnosti 169 kanonických polí. Historická poznámka o null aliasoch z 2026-09-16 je pre root nahradená schválenou alias revíziou z 2026-09-17; nie je aktuálnou medzerou.')
    dense('fields-sklad_karta.yaml','MC SKLAD KARTA všetkých 169 polí')

    heading('4 Satelity a referenčné polia')
    for name in sorted(n for n in docs if n.startswith('fields-') and n!='fields-sklad_karta.yaml'):
        dense(name,name[7:-5].upper().replace('_',' '))

    heading('5 Constraints indexy a väzby')
    dense('constraints.yaml','PK UQ FK CHECK metadata')
    dense('indexes.yaml','Indexy a ich stĺpce')
    narrative('relationships.yaml','Schválené JOIN kontrakty a kardinalita')

    heading('6 Dátované hodnotové domény')
    paragraph('Pozorované počty a hodnoty sú snapshoty k uvedenému dátumu; nepredstavujú trvalé invarianty ani aktuálny refresh MC.')
    dense('value-domains.yaml','Hodnoty stavy a profily')
    heading('7 Časový model a zdroje pravdy')
    narrative('temporal.yaml','RAW CURRENT a selektívna história')
    heading('8 Zdrojové toky a Mutation Matrix')
    paragraph('Ukončenie predaja STAV 8 je na MC od 2026-09-16 POTVRDENÉ — VYRIEŠENÉ. Aktuálny kontrakt rozlišuje dedikovanú výnimku pre zmenenú poznámku a bežnú ochranu uzamknutého forecastu; nejde o globálny bypass.')
    narrative('flows.yaml','Triggery volania a vedľajšie efekty')
    narrative('mutations.yaml','Mutation Matrix')
    heading('9 Závislosti API a systémové hranice')
    deps=source('dependencies.yaml')['records']
    roles=Counter(r['role'] for r in deps)
    table(['Klasifikácia','Počet kanonických záznamov'],[[k,str(v)] for k,v in sorted(roles.items())],[175,92])
    paragraph('Počet záznamov nie je počet runtime vykonaní. Statická závislosť ani grant alebo synonymum nedokazuje runtime čítanie, zápis alebo volanie.')
    for row in deps:
        if row['role'] not in ('DEPENDENCY ONLY','ACCESS CAPABILITY'):
            heading(row['dependency_id'],3);properties(row)
    for prefix,title in [('api-references-','Lexikálne API referencie'),('source-references-','Zdrojové kontexty')]:
        heading(title,2)
        rows=[]
        for name in sorted(n for n in docs if n.startswith(prefix)):
            d=source(name); records=d.get('records',[])
            rows.append([d.get('id',name),str(len(records)),str(DOMAIN/name)])
        table(['Register','Záznamy','Úplný kanonický zdroj'],rows,[95,25,147])
    for name,title in [('relationships-inbound.yaml','Inbound FK povrch'),('oracle-entities.yaml','Oracle objekty a hranice')]:
        heading(title,2);d=source(name);rows=d.get('records',[])
        paragraph(f'Úplný kanonický register: {len(rows)} záznamov. Registry sú technické metadáta a nie automatický dôkaz runtime role.')
        if name=='relationships-inbound.yaml': counts=Counter(r['from_object_ref'] for r in rows)
        else: counts=Counter(str(r.get('oracle_object_type','neuvedený typ')) for r in rows)
        table(['Skupina','Počet záznamov'],[[k,str(v)] for k,v in sorted(counts.items())],[217,50])
    heading('10 Kvalita údajov a známe nálezy')
    narrative('data-quality.yaml','Aktuálne DQ pravidlá a interpretácia')
    heading('11 DO NOT ASSUME')
    for row in rules:
        if row not in consolidated:
            heading(row['rule_id'],2);properties(row)
    heading('12 Diagnostické playbooky')
    narrative('playbooks.yaml','Vstupné diagnostické postupy')
    heading('13 Kanonické read only SQL')
    registry=source('sql-registry.yaml')['records']
    for row in registry:
        heading(row['title_sk'],2);properties(row)
        out.append(('code',data['sql'][row['sql_id']]))
    heading('14 Neblokujúci backlog')
    narrative('backlog.yaml','Zachované otvorené otázky')
    heading('15 Revízna história')
    paragraph('Historické revízie zachovávajú aj vtedajší odklad publikácie a starý vyriešený lock konflikt. Aktuálnu publikačnú autorizáciu zaznamenáva posledná publikačná revízia; kontrakt zostáva 1.0.')
    narrative('revisions.yaml','Všetky kanonické revízie')
    heading('16 Dôkazy a proveniencia')
    rows=[]
    for name,m in data['evidence'].items():
        rows.append([m['evidence_id'],value_text({k:m.get(k) for k in ['evidence_class','environment','snapshot_date','review_status']}),value_text({k:m.get(k) for k in ['source_file','repository_path','sha256','retention_class','raw_retained']})])
    table(['Dôkaz','Trieda prostredie a dátum','Zdroj retencia a SHA 256'],rows,[55,65,147])
    paragraph('Kompletné manifesty vrátane interpretačných obmedzení sú uvedené v registri kanonických vstupov. Proveniencia dokazuje pôvod publikácie, nie nový sémantický význam.')
    heading('17 Register kanonických vstupov')
    for path in data['inputs']:paragraph(path)
    missing=set(docs)-consumed
    if missing:raise ValueError('Unclassified canonical documents: '+str(sorted(missing)))
    return out


def soft_wrap(text):
    # Permit wrapping of long identifiers without altering visible characters.
    return text.replace("_", "_\u200b").replace(".", ".\u200b").replace("/", "/\u200b")


def add_field(paragraph, name):
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), name)
    paragraph._p.append(field)


def build_docx(data, output):
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21)
    sec.top_margin = sec.bottom_margin = Cm(1.5)
    sec.left_margin = sec.right_margin = Cm(1.5)
    for name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3"):
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
        for border in list(style.element.xpath("./w:pPr/w:pBdr")):
            border.getparent().remove(border)
    doc.styles["Normal"].font.size = Pt(9)
    doc.styles["Normal"].paragraph_format.space_after = Pt(4)
    for name, size in [("Title", 27), ("Heading 1", 17), ("Heading 2", 12), ("Heading 3", 10)]:
        doc.styles[name].font.size = Pt(size)
    header = sec.header.paragraphs[0]
    header.text = f"KASO Data Catalog  |  skladové karty {data['version']}"
    header.runs[0].font.size = Pt(8)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run(f"{REPOSITORY} | main | ")
    add_field(footer, "PAGE")
    for run in footer.runs:
        run.font.size = Pt(8)
    doc.add_paragraph("KASO Data Catalog", "Title")
    doc.add_paragraph("Technical & Diagnostic Reference", "Subtitle")
    doc.add_paragraph("Skladové karty", "Title")
    doc.add_paragraph(data["docs"]["contract.yaml"]["title_sk"], "Subtitle")
    doc.add_paragraph("Schválený MC kontrakt skladových kariet pre bezpečnú read-only diagnostiku.")
    for line in provenance(data):
        doc.add_paragraph(line)
    doc.add_page_break()
    doc.add_heading("Obsah", 1)
    for block in blocks(data):
        if block[0] == "heading" and block[1] == 1:
            doc.add_paragraph(block[2])
    for block in blocks(data):
        kind = block[0]
        if kind == "heading":
            follows_table = (block[1] == 1 and doc.paragraphs and not doc.paragraphs[-1].text)
            if follows_table:
                # Replace the table spacer and separate break with one heading break.
                spacer = doc.paragraphs[-1]._element
                spacer.getparent().remove(spacer)
            elif block[1] == 1:
                doc.add_page_break()
            heading = doc.add_heading(soft_wrap(block[2]), min(block[1], 3))
            if follows_table:
                heading.paragraph_format.page_break_before = True
        elif kind == "paragraph":
            doc.add_paragraph(soft_wrap(block[1]))
        elif kind == "code":
            for line in block[1].splitlines():
                for segment in textwrap.wrap(line, 130, replace_whitespace=False, drop_whitespace=False) or [""]:
                    p = doc.add_paragraph()
                    p.paragraph_format.space_after = Pt(0)
                    run = p.add_run(segment)
                    run.font.name = "Courier New"
                    run.font.size = Pt(8)
        else:
            _, headers, rows, widths = block
            table = doc.add_table(rows=1, cols=len(headers))
            table.autofit = False
            for col, width in zip(table.columns, widths):
                col.width = Cm(width / 10)
            borders = OxmlElement("w:tblBorders")
            for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
                tag = OxmlElement("w:" + edge)
                for key, value in (("val", "single"), ("sz", "4"), ("color", "D9D9D9")):
                    tag.set(qn("w:" + key), value)
                borders.append(tag)
            table._tbl.tblPr.append(borders)
            table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
            for n, values in enumerate([headers] + rows):
                row = table.rows[0] if n == 0 else table.add_row()
                for cell, value, width in zip(row.cells, values, widths):
                    cell.width = Cm(width / 10)
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    cell.text = soft_wrap(str(value))
                    pr = cell._tc.get_or_add_tcPr()
                    margins = OxmlElement("w:tcMar")
                    for side in ("top", "left", "bottom", "right"):
                        el = OxmlElement("w:" + side)
                        el.set(qn("w:w"), "65")
                        el.set(qn("w:type"), "dxa")
                        margins.append(el)
                    pr.append(margins)
                    fill = "1F4E78" if n == 0 else ("F2F6FA" if n % 2 == 0 else "FFFFFF")
                    shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), fill); pr.append(shd)
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.space_after = Pt(0)
                        for run in paragraph.runs:
                            run.font.size = Pt(8)
                            if n == 0:
                                run.font.bold = True
                                run.font.color.rgb = RGBColor(255, 255, 255)
            doc.add_paragraph()
    doc.core_properties.created = FIXED_TIME
    doc.core_properties.modified = FIXED_TIME
    doc.core_properties.author = REPOSITORY
    doc.core_properties.title = data["subject"]
    doc.save(output)
    normalize_docx(output)


def provenance(data):
    c = data["docs"]["contract.yaml"]
    return [f"Repository: {REPOSITORY}", "Canonical branch: main",
            f"Contract: {c['contract_id']} | version: {data['version']} | maturity: {c['maturity']}",
            f"Authoritative environment / owner: {c['authoritative_environment']} / {c['authoritative_owner']}",
            f"Canonical input SHA-256: {data['digest']}"]


def build_pdf(data, output):
    for name, filename in (("Pur", "LiberationSans-Regular.ttf"), ("PurBold", "LiberationSans-Bold.ttf"), ("PurCode", "LiberationSans-Regular.ttf")):
        pdfmetrics.registerFont(TTFont(name, FONT_DIR / filename))
    styles = {
        "body": ParagraphStyle("body", fontName="Pur", fontSize=9, leading=12, spaceAfter=4),
        "title": ParagraphStyle("title", fontName="PurBold", fontSize=26, leading=32, spaceAfter=16),
        "h1": ParagraphStyle("h1", fontName="PurBold", fontSize=17, leading=21, spaceAfter=9, keepWithNext=True),
        "h2": ParagraphStyle("h2", fontName="PurBold", fontSize=12, leading=15, spaceBefore=10, spaceAfter=6, keepWithNext=True),
        "h3": ParagraphStyle("h3", fontName="PurBold", fontSize=10, leading=13, spaceBefore=8, spaceAfter=4, keepWithNext=True),
        "cell": ParagraphStyle("cell", fontName="Pur", fontSize=8, leading=10),
        "head": ParagraphStyle("head", fontName="PurBold", fontSize=8, leading=11, textColor=colors.white),
        "code": ParagraphStyle("code", fontName="PurCode", fontSize=8, leading=10),
    }

    def p(text, style="body"):
        safe = html.escape(str(text)).replace("\n", "<br/>")
        return Paragraph(safe, styles[style])

    c = data["docs"]["contract.yaml"]
    story = [Spacer(1, 8 * mm), p("KASO Data Catalog", "title"), p("Technical & Diagnostic Reference", "h2"),
             p("Skladové karty", "title"), p(c["title_sk"], "h2"), p("Schválený MC kontrakt skladových kariet pre bezpečnú read-only diagnostiku."), Spacer(1, 6 * mm)]
    story.extend(p(line) for line in provenance(data))
    story.extend([PageBreak(), p("Obsah", "h1")])
    for block in blocks(data):
        if block[0] == "heading" and block[1] == 1:
            story.append(p(block[2]))
    for block in blocks(data):
        if block[0] == "heading":
            if block[1] == 1:
                story.append(PageBreak())
            story.append(p(block[2], "h" + str(block[1])))
        elif block[0] == "paragraph":
            story.append(p(block[1]))
        elif block[0] == "code":
            for line in block[1].splitlines():
                # Explicitly wrap long SQL lines; no content truncation.
                for segment in textwrap.wrap(line, 130, replace_whitespace=False, drop_whitespace=False) or [" "]:
                    story.append(Paragraph(html.escape(segment).replace(" ", "&#160;"), styles["code"]))
            story.append(Spacer(1, 4 * mm))
        else:
            _, headers, rows, widths = block
            cooked = [[p(v, "head") for v in headers]] + [[p(v, "cell") for v in row] for row in rows]
            table = LongTable(cooked, colWidths=[w * mm for w in widths], repeatRows=1, splitInRow=0, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#D9D9D9")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.extend([table, Spacer(1, 3 * mm)])

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Pur", 7)
        canvas.drawString(15 * mm, 9 * mm, REPOSITORY + " | main | skladové karty " + data["version"])
        canvas.drawRightString(282 * mm, 9 * mm, str(doc.page))
        canvas.restoreState()

    pdf = SimpleDocTemplate(str(output), pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=16 * mm, invariant=1, pageCompression=1,
                            title="Skladové karty", author=REPOSITORY)
    pdf.build(story, onFirstPage=footer, onLaterPages=footer)


def generate(root, output):
    data = model(root)
    output.mkdir(parents=True, exist_ok=True)
    docx = output / (BASENAME + ".docx")
    pdf = output / (BASENAME + ".pdf")
    manifest = output / (BASENAME + ".manifest.yaml")
    build_docx(data, docx)
    build_pdf(data, pdf)
    payload = {
        "publication_version": "1.0", "repository": REPOSITORY, "canonical_branch": "main",
        "contract_ref": data["docs"]["contract.yaml"]["contract_id"], "contract_version": data["version"],
        "generator": "tools/generate_pm_publication.py", "generator_version": "1.0",
        "generated_from": "kanonické YAML skladových kariet, read-only SQL a manifesty dôkazov skladových kariet",
        "canonical_input_sha256": data["digest"], "canonical_inputs": data["inputs"],
        "artifacts": [{"path": p.relative_to(root).as_posix() if p.is_relative_to(root) else p.name,
                       "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in (docx, pdf)],
    }
    manifest.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=110))
    return docx, pdf, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    for path in generate(args.root.resolve(), args.output_dir.resolve()):
        print(path)


if __name__ == "__main__":
    main()

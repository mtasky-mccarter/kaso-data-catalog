#!/usr/bin/env python3
"""Business Partner reference publication from canonical YAML and SQL only.

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
DOMAIN = Path("catalog/master/obchodni-partneri")
SQL_DIR = Path("sql/diagnostic/obchodni-partneri")
EVIDENCE = Path("evidence/manifests/obchodni-partneri")
# An intermediate name required by the existing publication orchestrator.
BASENAME = "obchodni-partneri-v1.0"
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


from publication_versions import resolve_versions


def model(root):
    from materialize_op_publication import approved_delta, project
    delta = approved_delta(root)
    docs = {p.name: yaml.safe_load(p.read_text()) for p in sorted((root / DOMAIN).glob("*.yaml"))}
    for relative, expected in project(root).items():
        if yaml.safe_load((root/relative).read_text()) != expected:
            raise ValueError("Publication metadata has not been materialized: " + relative)
    version, documentation_version, explicit = resolve_versions(root, DOMAIN / "revisions.yaml")
    if not explicit or documentation_version != delta['publication']['documentation_version']:
        raise ValueError("Explicit approved documentation version required")
    evidence = {p.name: yaml.safe_load(p.read_text()) for p in sorted((root / EVIDENCE).glob("*.yaml"))}
    registry = docs["sql-registry.yaml"]["records"]
    sql = {}
    for row in registry:
        path = (root / row["sql_file"]).resolve()
        if path.parent != (root / SQL_DIR).resolve() or path.suffix != ".sql":
            raise ValueError("SQL path outside approved domain")
        sql[row["sql_id"]] = path.read_text()
    if {r["sql_file"] for r in registry} != {p.relative_to(root).as_posix() for p in (root / SQL_DIR).glob("*.sql")}:
        raise ValueError("SQL registry coverage mismatch")
    digest, inputs = canonical_digest(root)
    return dict(docs=docs, evidence=evidence, sql=sql, version=version,
                documentation_version=documentation_version, subject="obchodní partneri", digest=digest, inputs=inputs)


def decoded(value):
    if isinstance(value, str) and value.startswith(("{", "[")):
        try:
            return decoded(json.loads(value))
        except ValueError:
            pass
    if isinstance(value, dict):
        return {k: decoded(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decoded(v) for v in value]
    return value


def blocks(data):
    """Render canonical properties; source-only JSON is decoded without interpretation."""
    from generate_pm_publication import registry_parts
    out = []
    def heading(text, level=1):
        out.append(("heading", level, text))
    def properties(record):
        for key, value in record.items():
            # Separate properties remain flowable, including long retained source metadata.
            out.append(("paragraph", label(key) + ": " + value_text(decoded(value))))
    def registry(filename, title):
        heading(title)
        document = data['docs'][filename]
        out.append(("paragraph", "Kanonický zdroj: " + str(DOMAIN / filename)))
        if 'records' not in document:
            properties(document)
            return
        common, records = registry_parts(document['records'])
        if common:
            heading("Spoločné vlastnosti záznamov", 2)
            properties(common)
        for record in records:
            identity = next((v for k, v in record.items() if k.endswith('_id')), filename)
            heading(str(identity), 2)
            properties(record)
    registry('contract.yaml', '1. Scope, autorita a hranice kontraktu')
    registry('object-obch_partneri.yaml', '2. Grain, identita a source of truth')
    heading('3. Úplný inventár polí')
    fields = data['docs']['fields.yaml']['records']
    out.append(('table', ['Poradie', 'Oracle pole', 'Datatype', 'Nullable', 'Alias', 'Status'],
        [[str(r['ordinal_position']), r['oracle_name'], r['datatype_raw'], value_text(r['nullable']),
          value_text(r['canonical_alias']), r['status']] for r in fields], [15, 55, 35, 18, 80, 64]))
    common, records = registry_parts(fields)
    heading('Spoločné vlastnosti polí', 2)
    properties(common)
    for record in records:
        heading(record['oracle_name'], 2)
        properties(record)
    registry('constraints.yaml', '4. Constraints')
    registry('indexes.yaml', '5. Indexy')
    registry('relationships.yaml', '6. JOINy, kardinality a fan-out')
    registry('value-domains.yaml', '7. Lookup enrichment a hodnotové domény')
    registry('temporal.yaml', '8. Temporal a historické obmedzenia')
    registry('api-contracts.yaml', '9. C_PARTNER API kontrakty')
    registry('flows.yaml', '10. Trigger flows')
    registry('mutations.yaml', '11. Mutation Matrix')
    registry('dependencies.yaml', '12. Závislosti a runtime hranice')
    registry('boundaries.yaml', '13. Samostatné budúce mappingy')
    registry('do-not-assume.yaml', '14. DO NOT ASSUME')
    registry('profiles.yaml', '15. Schválené profilové snapshoty')
    registry('data-quality.yaml', '16. Data quality')
    registry('backlog.yaml', '17. Neblokujúci backlog')
    heading('18. Diagnostické postupy a read-only SQL')
    out.append(('paragraph', 'Diagnostické vstupy sú uvedené podľa kanonického SQL registra. '
                'Samostatný register playbookov nie je súčasťou kontraktu; ďalšie diagnostické pravidlá sa neodvodzujú. '
                'Klient: SQL Navigator 5.5.4.847. Verzia Oracle servera nie je určená.'))
    for row in data['docs']['sql-registry.yaml']['records']:
        heading(row['title_sk'], 2)
        properties(row)
        out.append(('code', data['sql'][row['sql_id']]))
    heading('19. Technický index externých Oracle entít')
    out.append(('paragraph', 'Boundary-only technický index. Detail polí a dôkazových referencií: '
                + str(DOMAIN/'oracle-entities.yaml') + '. Index nemení maturity ani rozsah kontraktu.'))
    out.append(('table', ['Oracle owner', 'Oracle objekt', 'Typ', 'Source visible', 'Boundary only', 'Status'],
        [[r['oracle_owner'], r['oracle_name'], r['oracle_object_type'], value_text(r['source_visible']),
          value_text(r['boundary_only']), r['status']] for r in data['docs']['oracle-entities.yaml']['records']],
        [25, 115, 35, 22, 25, 45]))
    heading('20. Dôkazy a proveniencia')
    for record in data['evidence'].values():
        heading(record['evidence_id'], 2)
        properties(record)
    registry('revisions.yaml', '21. História revízií')
    expected = {'contract.yaml','object-obch_partneri.yaml','fields.yaml','constraints.yaml','indexes.yaml',
                'relationships.yaml','value-domains.yaml','temporal.yaml','api-contracts.yaml','flows.yaml',
                'mutations.yaml','dependencies.yaml','boundaries.yaml','do-not-assume.yaml','profiles.yaml',
                'data-quality.yaml','backlog.yaml','sql-registry.yaml','oracle-entities.yaml','revisions.yaml'}
    if set(data['docs']) != expected:
        raise ValueError('Unclassified canonical documents')
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
    header.text = f"KASO Data Catalog  |  obchodní partneri {data['documentation_version']}"
    header.runs[0].font.size = Pt(8)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run(f"{REPOSITORY} | main | ")
    add_field(footer, "PAGE")
    for run in footer.runs:
        run.font.size = Pt(8)
    doc.add_paragraph("KASO Data Catalog", "Title")
    doc.add_paragraph("Technical & Diagnostic Reference", "Subtitle")
    doc.add_paragraph("Obchodní partneri", "Title")
    doc.add_paragraph(data["docs"]["contract.yaml"]["title_sk"], "Subtitle")
    doc.add_paragraph("Schválený MC kontrakt obchodných partnerov pre bezpečnú read-only diagnostiku.")
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
            f"Documentation version: {data['documentation_version']}",
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
             p("Obchodní partneri", "title"), p(c["title_sk"], "h2"), p("Schválený MC kontrakt obchodných partnerov pre bezpečnú read-only diagnostiku."), Spacer(1, 6 * mm)]
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
        canvas.drawString(15 * mm, 9 * mm, REPOSITORY + " | main | obchodní partneri " + data["documentation_version"])
        canvas.drawRightString(282 * mm, 9 * mm, str(doc.page))
        canvas.restoreState()

    pdf = SimpleDocTemplate(str(output), pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=16 * mm, invariant=1, pageCompression=1,
                            title="Obchodní partneri", author=REPOSITORY)
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
        "publication_version": data["documentation_version"], "repository": REPOSITORY, "canonical_branch": "main",
        "contract_ref": data["docs"]["contract.yaml"]["contract_id"], "contract_version": data["version"],
        "generator": "tools/generate_op_publication.py", "generator_version": "1.0",
        "generated_from": "kanonické YAML obchodných partnerov, read-only SQL a manifesty dôkazov obchodných partnerov",
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

#!/usr/bin/env python3
"""Generate the CP v1.1 DOCX/PDF publication strictly from canonical YAML and SQL."""
from __future__ import annotations

import argparse
import hashlib
import io
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml
import reportlab
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

REPOSITORY = "mtasky-mccarter/kaso-data-catalog"
BRANCH = "main"
GENERATOR_VERSION = "1.0"
DOMAIN = Path("catalog/transport/cestovne-prikazy")
SQL_DIR = Path("sql/diagnostic/cestovne-prikazy")
BASENAME = "cestovne-prikazy-v1.1"
FIXED_TIME = datetime(2026, 9, 12, 0, 0, 0, tzinfo=timezone.utc)


def read_yaml(root: Path, name: str):
    return yaml.safe_load((root / DOMAIN / name).read_text(encoding="utf-8"))


def canonical_paths(root: Path):
    return sorted((root / DOMAIN).glob("*.yaml")) + sorted((root / SQL_DIR).glob("*.sql"))


def canonical_digest(root: Path):
    digest = hashlib.sha256()
    paths = canonical_paths(root)
    for path in paths:
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), [p.relative_to(root).as_posix() for p in paths]


def model(root: Path):
    names = [
        "contract.yaml", "fields-cestovne_pr_l.yaml", "fields-cestovne_pr_o.yaml",
        "constraints.yaml", "relationships.yaml", "value-domains.yaml", "flows.yaml",
        "mutations.yaml", "temporal.yaml", "data-quality.yaml", "do-not-assume.yaml",
        "playbooks.yaml", "sql-registry.yaml", "dependencies.yaml", "dependency-closure.yaml",
        "backlog.yaml", "revisions.yaml",
    ]
    data = {name: read_yaml(root, name) for name in names}
    data["sql_bodies"] = {
        row["sql_id"]: (root / row["sql_file"]).read_text(encoding="utf-8").rstrip()
        for row in data["sql-registry.yaml"]["records"]
    }
    data["canonical_sha256"], data["canonical_paths"] = canonical_digest(root)
    return data


def text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "ÁNO" if value else "NIE"
    if isinstance(value, list):
        return "; ".join(text(v) for v in value)
    return str(value)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def border_table(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = OxmlElement(f"w:{edge}")
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), "4")
        tag.set(qn("w:color"), "D9D9D9")
        borders.append(tag)
    tbl_pr.append(borders)


def docx_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    header = table.rows[0]
    header._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for i, value in enumerate(headers):
        cell = header.cells[i]
        cell.text = value
        shade(cell, "1F4E78")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(8)
    for row_index, values in enumerate(rows):
        body_row = table.add_row()
        body_row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        cells = body_row.cells
        for i, value in enumerate(values):
            cells[i].text = text(value)
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if row_index % 2:
                shade(cells[i], "F2F6FA")
            for paragraph in cells[i].paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs:
                    run.font.size = Pt(7.5)
        if widths:
            for i, width in enumerate(widths):
                cells[i].width = Cm(width)
    border_table(table)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_docx_field(paragraph, instruction):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = instruction
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, end])


def add_record_docx(doc, title, row, keys):
    doc.add_heading(title, level=3)
    rows = [(label, text(row.get(key))) for key, label in keys if row.get(key) not in (None, [], "")]
    docx_table(doc, ["Vlastnosť", "Canonical hodnota"], rows, [4.2, 20.0])


def normalize_docx(path: Path):
    with zipfile.ZipFile(path, "r") as source:
        parts = [(info.filename, source.read(info.filename)) for info in source.infolist()]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for name, payload in sorted(parts):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            target.writestr(info, payload)
    path.write_bytes(buffer.getvalue())


def build_docx(data, output: Path):
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    sec.top_margin = sec.bottom_margin = Cm(1.5)
    sec.left_margin = sec.right_margin = Cm(1.5)
    for style_name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3"):
        style = doc.styles[style_name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
    doc.styles["Normal"].font.size = Pt(9)
    doc.styles["Title"].font.size = Pt(24)
    doc.styles["Heading 1"].font.size = Pt(16)
    doc.styles["Heading 2"].font.size = Pt(12)
    doc.styles["Heading 3"].font.size = Pt(10)
    header = sec.header.paragraphs[0]
    header.text = f"{REPOSITORY}  |  canonical {BRANCH}"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header.runs[0].font.size = Pt(8)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Generated from canonical YAML and SQL  |  ")
    add_docx_field(footer, "PAGE")
    for run in footer.runs: run.font.size = Pt(8)

    contract = data["contract.yaml"]
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("KASO Data Catalog CESTOVNE PR L O v1.1")
    subtitle = doc.add_paragraph(style="Subtitle")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("Canonical human-readable publication")
    doc.add_paragraph(contract["purpose_sk"])
    docx_table(doc, ["Proveniencia", "Hodnota"], [
        ("Repository", REPOSITORY), ("Canonical branch", BRANCH),
        ("Contract", contract["contract_id"]), ("Contract version", "1.1"),
        ("Maturity", contract["maturity"]), ("Authoritative environment / owner", f"{contract['authoritative_environment']} / {contract['authoritative_owner']}"),
        ("Generated from", "Canonical machine-readable YAML and canonical read-only SQL"),
        ("Canonical input SHA-256", data["canonical_sha256"]),
    ], [5.0, 19.0])

    doc.add_heading("1 Contract scope", level=1)
    docx_table(doc, ["Vrstva", "Canonical obsah"], [
        ("Scope includes", contract["scope_includes"]), ("Scope excludes", contract["scope_excludes"]),
        ("Limitations", contract["limitations_sk"]), ("Boundary refs", contract["boundary_refs"]),
    ], [5.0, 19.0])

    doc.add_page_break()
    doc.add_heading("2 Physical field inventory", level=1)
    for object_name, filename in (("MC.CESTOVNE_PR_L", "fields-cestovne_pr_l.yaml"), ("MC.CESTOVNE_PR_O", "fields-cestovne_pr_o.yaml")):
        doc.add_heading(object_name, level=2)
        rows = []
        for field in data[filename]["records"]:
            rows.append((field["ordinal_position"], field["oracle_name"], field["datatype_raw"], "Y" if field["nullable"] else "N", field.get("canonical_alias"), field.get("business_definition_sk"), field["status"]))
        docx_table(doc, ["#", "Oracle field", "Datatype", "NULL", "Canonical alias", "Definition", "Status"], rows, [1.0, 3.3, 3.0, 1.0, 3.5, 10.2, 2.4])

    doc.add_heading("3 Constraints and relationships", level=1)
    constraints = data["constraints.yaml"]["records"]
    docx_table(doc, ["Constraint", "Object", "Type", "Columns", "Referenced object", "Status"], [
        (r["oracle_name"], r["object_ref"], r["constraint_type"], r.get("column_refs"), r.get("referenced_object_ref"), r["status"]) for r in constraints
    ], [4.0, 4.0, 2.0, 6.0, 5.0, 2.5])
    for row in data["relationships.yaml"]["records"]:
        add_record_docx(doc, row["relationship_id"], row, [
            ("relationship_type","Type"),("cardinality","Cardinality"),("validation_summary_sk","Validation"),
            ("fanout_risk","Fan-out"),("safe_usage_sk","Safe usage"),("snapshot_date","Snapshot"),("status","Status")])

    doc.add_heading("4 State and value domains", level=1)
    values = data["value-domains.yaml"]["records"]
    docx_table(doc, ["Scope", "Raw", "Canonical", "Label", "Observed", "Count", "Status"], [
        (r["scope_ref"], r["raw_value"], r.get("canonical_value"), r.get("business_label_sk"), r.get("observed_live"), r.get("observed_count"), r["status"]) for r in values
    ], [5.0, 2.0, 2.0, 5.0, 2.0, 2.0, 2.5])

    doc.add_heading("5 Trigger flows", level=1)
    flow_keys=[("event_sk","Event"),("condition_sk","Condition"),("watched_field_refs","Watched fields"),("session_or_bypass_sk","Session / bypass"),("business_effect_sk","Business effect"),("diagnostic_meaning_sk","Diagnostic meaning"),("calls","Calls"),("direct_mutations","Direct mutations"),("side_effects","Side effects"),("exceptions","Exceptions")]
    for row in data["flows.yaml"]["records"]: add_record_docx(doc,row["flow_id"],row,flow_keys)

    doc.add_heading("6 Mutation matrix", level=1)
    mut_keys=[("target_refs","Targets"),("writer_ref","Writer"),("writer_role","Writer role"),("event_sk","Event"),("condition_sk","Condition"),("session_or_bypass_sk","Session / bypass"),("direct_mutations_sk","Direct mutation"),("side_effects_sk","Side effects"),("diagnostic_meaning_sk","Diagnostic meaning"),("status","Status")]
    for row in data["mutations.yaml"]["records"]: add_record_docx(doc,row["mutation_id"],row,mut_keys)

    doc.add_heading("7 Temporal and data quality", level=1)
    for row in data["temporal.yaml"]["records"]:
        add_record_docx(doc,row["temporal_rule_id"],row,[("scope_refs","Scope"),("classification","Classification"),("transition_or_event_sk","Event"),("rollback_behavior_sk","Rollback"),("reconstructable","Reconstructable"),("history_limitations_sk","Limitations"),("status","Status")])
    doc.add_heading("Data quality snapshot", level=2)
    docx_table(doc,["ID","Observation","Snapshot","Blocking","Status","Interpretation limit"],[
        (r["dq_id"],r["observation_sk"],r.get("snapshot_date"),r["blocking"],r["status"],r.get("interpretation_limit_sk")) for r in data["data-quality.yaml"]["records"]
    ],[4.0,10.0,2.5,1.8,2.5,5.0])

    doc.add_heading("8 Do not assume", level=1)
    docx_table(doc,["Rule","Scope","Statement","Consequence"],[
        (r["rule_id"],r["scope_refs"],r["statement_sk"],r["consequence_sk"]) for r in data["do-not-assume.yaml"]["records"]
    ],[3.2,5.5,8.5,8.5])

    doc.add_heading("9 Diagnostic playbooks", level=1)
    docx_table(doc,["Symptom","First SQL","Proves","Does not prove","Next step","Flows / boundaries"],[
        (r["symptom_sk"],r["first_sql_ref"],r.get("proves_sk"),r.get("does_not_prove_sk"),r.get("next_step_sk"),list(r.get("flow_refs",[]))+list(r.get("dependency_or_boundary_refs",[]))) for r in data["playbooks.yaml"]["records"]
    ],[4.0,3.0,5.5,5.5,5.5,4.0])

    doc.add_heading("10 Canonical read-only SQL", level=1)
    for row in data["sql-registry.yaml"]["records"]:
        add_record_docx(doc,row["sql_id"],row,[("title_sk","Title"),("purpose_sk","Purpose"),("input_parameters","Bind inputs"),("result_grain_sk","Result grain"),("fanout_warning_sk","Fan-out / limit"),("proves_sk","Proves"),("does_not_prove_sk","Does not prove"),("sql_file","Canonical file")])
        code=doc.add_paragraph()
        code.style=doc.styles["Normal"]
        run=code.add_run(data["sql_bodies"][row["sql_id"]])
        run.font.name="Courier New"; run.font.size=Pt(7)

    doc.add_heading("11 Dependency and caller summary", level=1)
    closure=data["dependency-closure.yaml"]
    roles=Counter(r["role"] for r in data["dependencies.yaml"]["records"])
    docx_table(doc,["Metric","Canonical value"],[
        ("Direct inbound source-visible Oracle objects",107),
        ("Inbound dependency edges",closure["summary"]["inbound_count"]),
        ("Maximum inbound depth",closure["summary"]["max_inbound_depth"]),
        ("Outbound dependency edges",closure["summary"]["outbound_count"]),
        ("Maximum outbound depth",closure["summary"]["max_outbound_depth"]),
        ("Dependency role counts",[f"{k}: {v}" for k,v in sorted(roles.items())]),
    ],[8.0,16.0])

    doc.add_heading("12 Backlog and freeze revision", level=1)
    docx_table(doc,["Backlog","Status","Blocking","Question","Reason","Closure"],[
        (r["backlog_id"],r["status"],r["blocking"],r["question_sk"],r.get("reason_sk"),r.get("closure_condition_sk")) for r in data["backlog.yaml"]["records"]
    ],[3.5,2.5,1.5,7.0,6.0,6.0])
    doc.add_heading("Revision history",level=2)
    docx_table(doc,["Revision","Version","Date","Breaking","Change","Reason"],[
        (r["revision_id"],r["contract_version"],r["date"],r["breaking_change"],r["change_sk"],r.get("reason_sk")) for r in data["revisions.yaml"]["records"]
    ],[4.0,1.5,2.0,1.5,9.0,9.0])

    doc.core_properties.title = "KASO Data Catalog CESTOVNE PR L O v1.1"
    doc.core_properties.subject = "Canonical human-readable publication"
    doc.core_properties.author = REPOSITORY
    doc.core_properties.created = FIXED_TIME
    doc.core_properties.modified = FIXED_TIME
    output.parent.mkdir(parents=True,exist_ok=True)
    doc.save(output)
    normalize_docx(output)


def register_pdf_fonts():
    font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    regular = font_dir / "Vera.ttf"
    bold = font_dir / "VeraBd.ttf"
    if not regular.is_file() or not bold.is_file():
        raise RuntimeError("Pinned ReportLab Unicode fonts are unavailable")
    pdfmetrics.registerFont(TTFont("CPRegular", regular))
    pdfmetrics.registerFont(TTFont("CPBold", bold))


def pdf_table(rows,widths,header=True):
    cooked=[]
    for row in rows:
        cooked.append([Paragraph(text(v).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"),PDF_STYLES["cell"]) for v in row])
    table=Table(cooked,colWidths=[w*mm for w in widths],repeatRows=1 if header else 0,hAlign="LEFT")
    commands=[("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#D9D9D9")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]
    if header: commands += [("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1F4E78")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"CPBold")]
    for i in range(1 if header else 0,len(rows)):
        if i%2==0: commands.append(("BACKGROUND",(0,i),(-1,i),colors.HexColor("#F2F6FA")))
    table.setStyle(TableStyle(commands)); return table


def build_pdf(data,output:Path):
    global PDF_STYLES
    register_pdf_fonts()
    base=getSampleStyleSheet()
    PDF_STYLES={
        "title":ParagraphStyle("title",parent=base["Title"],fontName="CPBold",fontSize=22,leading=26,textColor=colors.black,spaceAfter=8),
        "h1":ParagraphStyle("h1",parent=base["Heading1"],fontName="CPBold",fontSize=15,leading=18,textColor=colors.black,spaceBefore=10,spaceAfter=6),
        "h2":ParagraphStyle("h2",parent=base["Heading2"],fontName="CPBold",fontSize=11,leading=14,textColor=colors.black,spaceBefore=8,spaceAfter=4),
        "body":ParagraphStyle("body",parent=base["BodyText"],fontName="CPRegular",fontSize=8.5,leading=11,textColor=colors.black),
        "cell":ParagraphStyle("cell",parent=base["BodyText"],fontName="CPRegular",fontSize=6.7,leading=8,textColor=colors.black,alignment=TA_LEFT),
        "code":ParagraphStyle("code",parent=base["Code"],fontName="Courier",fontSize=6.2,leading=7.4,textColor=colors.black),
    }
    def header_footer(canvas,doc):
        canvas.saveState(); canvas.setFont("CPRegular",7); canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(15*mm,10*mm,f"{REPOSITORY} | canonical {BRANCH}")
        canvas.drawRightString(282*mm,10*mm,f"Generated from canonical YAML and SQL | {doc.page}")
        canvas.restoreState()
    output.parent.mkdir(parents=True,exist_ok=True)
    pdf=SimpleDocTemplate(str(output),pagesize=landscape(A4),leftMargin=15*mm,rightMargin=15*mm,topMargin=14*mm,bottomMargin=16*mm,title="KASO Data Catalog CESTOVNE PR L O v1.1",author=REPOSITORY,invariant=1,pageCompression=1)
    story=[]
    contract=data["contract.yaml"]
    story += [Paragraph("KASO Data Catalog CESTOVNE PR L O v1.1",PDF_STYLES["title"]),Paragraph("Canonical human-readable publication",PDF_STYLES["h2"]),Paragraph(contract["purpose_sk"],PDF_STYLES["body"]),Spacer(1,4*mm)]
    story.append(pdf_table([["Proveniencia","Hodnota"],["Repository",REPOSITORY],["Canonical branch",BRANCH],["Contract",contract["contract_id"]],["Contract version","1.1"],["Maturity",contract["maturity"]],["Authoritative environment / owner",f"{contract['authoritative_environment']} / {contract['authoritative_owner']}"],["Generated from","Canonical machine-readable YAML and canonical read-only SQL"],["Canonical input SHA-256",data["canonical_sha256"]]],[45,215]))
    story += [PageBreak(),Paragraph("1 Contract scope",PDF_STYLES["h1"]),pdf_table([["Vrstva","Canonical obsah"],["Scope includes",contract["scope_includes"]],["Scope excludes",contract["scope_excludes"]],["Limitations",contract["limitations_sk"]],["Boundary refs",contract["boundary_refs"]]],[45,215])]
    story.append(Paragraph("2 Physical field inventory",PDF_STYLES["h1"]))
    for obj,fn in (("MC.CESTOVNE_PR_L","fields-cestovne_pr_l.yaml"),("MC.CESTOVNE_PR_O","fields-cestovne_pr_o.yaml")):
        story.append(Paragraph(obj,PDF_STYLES["h2"])); rows=[["#","Oracle field","Datatype","NULL","Canonical alias","Definition","Status"]]
        for f in data[fn]["records"]: rows.append([f["ordinal_position"],f["oracle_name"],f["datatype_raw"],"Y" if f["nullable"] else "N",f.get("canonical_alias"),f.get("business_definition_sk"),f["status"]])
        story.append(pdf_table(rows,[8,30,27,10,33,125,27]))
    story.append(PageBreak()); story.append(Paragraph("3 Constraints and relationships",PDF_STYLES["h1"]))
    rows=[["Constraint","Object","Type","Columns","Referenced object","Status"]]+[[r["oracle_name"],r["object_ref"],r["constraint_type"],r.get("column_refs"),r.get("referenced_object_ref"),r["status"]] for r in data["constraints.yaml"]["records"]]
    story.append(pdf_table(rows,[38,40,18,65,55,24]))
    for r in data["relationships.yaml"]["records"]:
        story.append(Paragraph(r["relationship_id"],PDF_STYLES["h2"])); story.append(pdf_table([["Vlastnosť","Canonical hodnota"],["Type",r["relationship_type"]],["Cardinality",r.get("cardinality")],["Validation",r.get("validation_summary_sk")],["Fan-out",r.get("fanout_risk")],["Safe usage",r.get("safe_usage_sk")],["Status",r["status"]]],[45,215]))
    story.append(PageBreak()); story.append(Paragraph("4 State and value domains",PDF_STYLES["h1"])); rows=[["Scope","Raw","Canonical","Label","Observed","Count","Status"]]+[[r["scope_ref"],r["raw_value"],r.get("canonical_value"),r.get("business_label_sk"),r.get("observed_live"),r.get("observed_count"),r["status"]] for r in data["value-domains.yaml"]["records"]]; story.append(pdf_table(rows,[55,18,20,62,20,20,25]))
    for section,filename,idkey,keys in [
        ("5 Trigger flows","flows.yaml","flow_id",[("event_sk","Event"),("condition_sk","Condition"),("watched_field_refs","Watched fields"),("session_or_bypass_sk","Session / bypass"),("business_effect_sk","Business effect"),("diagnostic_meaning_sk","Diagnostic meaning"),("calls","Calls"),("direct_mutations","Direct mutations"),("side_effects","Side effects"),("exceptions","Exceptions")]),
        ("6 Mutation matrix","mutations.yaml","mutation_id",[("target_refs","Targets"),("writer_ref","Writer"),("writer_role","Writer role"),("event_sk","Event"),("condition_sk","Condition"),("session_or_bypass_sk","Session / bypass"),("direct_mutations_sk","Direct mutation"),("side_effects_sk","Side effects"),("diagnostic_meaning_sk","Diagnostic meaning"),("status","Status")]),
        ("7 Temporal contract","temporal.yaml","temporal_rule_id",[("scope_refs","Scope"),("classification","Classification"),("transition_or_event_sk","Event"),("rollback_behavior_sk","Rollback"),("reconstructable","Reconstructable"),("history_limitations_sk","Limitations"),("status","Status")]),
    ]:
        story.append(PageBreak()); story.append(Paragraph(section,PDF_STYLES["h1"]))
        for r in data[filename]["records"]:
            story.append(Paragraph(r[idkey],PDF_STYLES["h2"])); rows=[["Vlastnosť","Canonical hodnota"]]+[[label,r.get(key)] for key,label in keys if r.get(key) not in (None,[],"")]; story.append(pdf_table(rows,[45,215]))
    story.append(Paragraph("Data quality snapshot",PDF_STYLES["h2"])); rows=[["ID","Observation","Snapshot","Blocking","Status","Interpretation limit"]]+[[r["dq_id"],r["observation_sk"],r.get("snapshot_date"),r["blocking"],r["status"],r.get("interpretation_limit_sk")] for r in data["data-quality.yaml"]["records"]]; story.append(pdf_table(rows,[35,92,20,16,22,75]))
    story.append(PageBreak()); story.append(Paragraph("8 Do not assume",PDF_STYLES["h1"])); rows=[["Rule","Scope","Statement","Consequence"]]+[[r["rule_id"],r["scope_refs"],r["statement_sk"],r["consequence_sk"]] for r in data["do-not-assume.yaml"]["records"]]; story.append(pdf_table(rows,[28,52,90,90]))
    story.append(Paragraph("9 Diagnostic playbooks",PDF_STYLES["h1"])); rows=[["Symptom","First SQL","Proves","Does not prove","Next step","Flows / boundaries"]]+[[r["symptom_sk"],r["first_sql_ref"],r.get("proves_sk"),r.get("does_not_prove_sk"),r.get("next_step_sk"),list(r.get("flow_refs",[]))+list(r.get("dependency_or_boundary_refs",[]))] for r in data["playbooks.yaml"]["records"]]; story.append(pdf_table(rows,[43,27,48,48,52,42]))
    story.append(PageBreak()); story.append(Paragraph("10 Canonical read-only SQL",PDF_STYLES["h1"]))
    for r in data["sql-registry.yaml"]["records"]:
        story.append(Paragraph(r["sql_id"],PDF_STYLES["h2"])); rows=[["Vlastnosť","Canonical hodnota"]]+[[label,r.get(key)] for key,label in [("title_sk","Title"),("purpose_sk","Purpose"),("input_parameters","Bind inputs"),("result_grain_sk","Result grain"),("fanout_warning_sk","Fan-out / limit"),("proves_sk","Proves"),("does_not_prove_sk","Does not prove"),("sql_file","Canonical file")]]; story.append(pdf_table(rows,[45,215])); story.append(Preformatted(data["sql_bodies"][r["sql_id"]],PDF_STYLES["code"],maxLineLength=150)); story.append(Spacer(1,3*mm))
    closure=data["dependency-closure.yaml"]; roles=Counter(r["role"] for r in data["dependencies.yaml"]["records"])
    story.append(PageBreak()); story.append(Paragraph("11 Dependency and caller summary",PDF_STYLES["h1"])); story.append(pdf_table([["Metric","Canonical value"],["Direct inbound source-visible Oracle objects",107],["Inbound dependency edges",closure["summary"]["inbound_count"]],["Maximum inbound depth",closure["summary"]["max_inbound_depth"]],["Outbound dependency edges",closure["summary"]["outbound_count"]],["Maximum outbound depth",closure["summary"]["max_outbound_depth"]],["Dependency role counts",[f"{k}: {v}" for k,v in sorted(roles.items())]],["Runtime boundary",contract["limitations_sk"]]],[75,185]))
    story.append(Paragraph("12 Backlog and freeze revision",PDF_STYLES["h1"])); rows=[["Backlog","Status","Blocking","Question","Reason","Closure"]]+[[r["backlog_id"],r["status"],r["blocking"],r["question_sk"],r.get("reason_sk"),r.get("closure_condition_sk")] for r in data["backlog.yaml"]["records"]]; story.append(pdf_table(rows,[33,22,15,65,60,65])); story.append(Paragraph("Revision history",PDF_STYLES["h2"])); rows=[["Revision","Version","Date","Breaking","Change","Reason"]]+[[r["revision_id"],r["contract_version"],r["date"],r["breaking_change"],r["change_sk"],r.get("reason_sk")] for r in data["revisions.yaml"]["records"]]; story.append(pdf_table(rows,[38,15,20,15,87,85]))
    pdf.build(story,onFirstPage=header_footer,onLaterPages=header_footer)


def write_manifest(data,docx_path,pdf_path,manifest_path):
    manifest={
        "publication_version":"1.0","repository":REPOSITORY,"canonical_branch":BRANCH,
        "contract_ref":data["contract.yaml"]["contract_id"],"contract_version":"1.1",
        "generated_from":"canonical machine-readable YAML and canonical read-only SQL",
        "generator":"tools/generate_cp_publication.py","generator_version":GENERATOR_VERSION,
        "canonical_input_sha256":data["canonical_sha256"],"canonical_inputs":data["canonical_paths"],
        "artifacts":[
            {"path":docx_path.as_posix(),"sha256":hashlib.sha256(docx_path.read_bytes()).hexdigest()},
            {"path":pdf_path.as_posix(),"sha256":hashlib.sha256(pdf_path.read_bytes()).hexdigest()},
        ],
    }
    manifest_path.write_text(yaml.safe_dump(manifest,allow_unicode=True,sort_keys=False,width=110),encoding="utf-8")


def generate(root:Path,out_dir:Path):
    data=model(root); out_dir.mkdir(parents=True,exist_ok=True)
    docx=out_dir/f"{BASENAME}.docx"; pdf=out_dir/f"{BASENAME}.pdf"; manifest=out_dir/f"{BASENAME}.manifest.yaml"
    build_docx(data,docx); build_pdf(data,pdf)
    rel_docx=Path("generated")/docx.name
    rel_pdf=Path("generated")/pdf.name
    write_manifest(data,rel_docx,rel_pdf,manifest)
    return docx,pdf,manifest


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); parser.add_argument("--output-dir",type=Path); parser.add_argument("--check",action="store_true"); args=parser.parse_args()
    root=args.root.resolve(); output=(args.output_dir or root/"generated").resolve()
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            generated=generate(root,Path(tmp))
            expected=[root/"generated"/p.name for p in generated]
            mismatches=[e.name for g,e in zip(generated,expected) if not e.is_file() or g.read_bytes()!=e.read_bytes()]
            if mismatches: raise SystemExit("Generated publication differs: "+", ".join(mismatches))
        print("PASS: CP publication artifacts are deterministic and current")
    else:
        for path in generate(root,output): print(path)
if __name__=="__main__": main()

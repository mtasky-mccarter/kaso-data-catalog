#!/usr/bin/env python3
"""Generate the VYD v1.1 DOCX/PDF publication from canonical YAML and SQL."""
from __future__ import annotations

import argparse
import hashlib
import io
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import reportlab
import yaml
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
DOMAIN = Path("catalog/warehouse/vydajky")
SQL_DIR = Path("sql/diagnostic/vydajky")
BASENAME = "vydajky-v1.1"
FIXED_TIME = datetime(2026, 9, 12, 0, 0, 0, tzinfo=timezone.utc)


def read_yaml(root: Path, name: str):
    return yaml.safe_load((root / DOMAIN / name).read_text(encoding="utf-8"))


def canonical_paths(root: Path):
    return sorted((root / DOMAIN).glob("*.yaml")) + sorted((root / SQL_DIR).glob("*.sql"))


def canonical_digest(root: Path):
    digest = hashlib.sha256()
    paths = canonical_paths(root)
    for path in paths:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), [path.relative_to(root).as_posix() for path in paths]


def model(root: Path):
    names = [
        "contract.yaml", "fields-vyd_l.yaml", "fields-vyd_o.yaml",
        "fields-vyd_o_p_prij.yaml", "constraints.yaml", "relationships.yaml",
        "value-domains.yaml", "flows.yaml", "mutations.yaml", "temporal.yaml",
        "data-quality.yaml", "do-not-assume.yaml", "playbooks.yaml",
        "sql-registry.yaml", "dependencies.yaml", "dependency-direct-edges.yaml",
        "dependency-closure-nodes.yaml", "backlog.yaml", "revisions.yaml",
    ]
    data = {name: read_yaml(root, name) for name in names}
    data["api_parts"] = [
        yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted((root / DOMAIN).glob("api-references-part*.yaml"))
    ]
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
        return "; ".join(text(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{key}={text(item)}" for key, item in value.items())
    return str(value)


def shade(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), fill)
    properties.append(element)


def docx_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    header = table.rows[0]
    header._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for index, value in enumerate(headers):
        cell = header.cells[index]
        cell.text = value
        shade(cell, "1F4E78")
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(8)
    for row_index, values in enumerate(rows):
        body = table.add_row()
        body._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for index, value in enumerate(values):
            cell = body.cells[index]
            cell.text = text(value)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if row_index % 2:
                shade(cell, "F2F6FA")
            if widths:
                cell.width = Cm(widths[index])
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs:
                    run.font.size = Pt(7.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_docx_field(paragraph, instruction):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    field = OxmlElement("w:instrText")
    field.set(qn("xml:space"), "preserve")
    field.text = instruction
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, field, end])


def record_rows(row, keys):
    return [(label, row.get(key)) for key, label in keys if row.get(key) not in (None, [], "")]


def normalize_docx(path: Path):
    with zipfile.ZipFile(path, "r") as source:
        parts = [(info.filename, source.read(info.filename)) for info in source.infolist()]
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for name, payload in sorted(parts):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            target.writestr(info, payload)
    path.write_bytes(output.getvalue())


def dependency_summary(data):
    direct = data["dependency-direct-edges.yaml"]["summary"]
    closure = data["dependency-closure-nodes.yaml"]["summary"]
    api = [record for part in data["api_parts"] for record in part["records"]]
    dependencies = data["dependencies.yaml"]["records"]
    writers = {row["source_ref"] for row in dependencies if row["role"] == "DIRECT WRITER"}
    grants = [row for row in dependencies if row.get("discovery_method") == "ALL_TAB_PRIVS"]
    synonyms = [row for row in dependencies if row.get("discovery_method") == "ALL_SYNONYMS"]
    return [
        ("Direct inbound dependency edges", direct["record_count"]),
        ("Direct inbound unique source objects", 316),
        ("Inbound closure nodes", closure["inbound_count"]),
        ("Maximum inbound depth", closure["max_inbound_depth"]),
        ("Outbound closure nodes", closure["outbound_count"]),
        ("Maximum outbound depth", closure["max_outbound_depth"]),
        ("API source objects", len({(r["caller_owner"], r["caller_name"], r["caller_type"]) for r in api})),
        ("API source hits", sum(r["hit_count"] for r in api)),
        ("Source-visible direct writer objects", len(writers)),
        ("Object grants / ACCESS CAPABILITY", len(grants)),
        ("Synonyms / DEPENDENCY ONLY", len(synonyms)),
        ("Dependency role counts", [f"{key}: {value}" for key, value in sorted(Counter(r["role"] for r in dependencies).items())]),
    ]


FLOW_KEYS = [
    ("event_sk", "Event"), ("condition_sk", "Condition"),
    ("watched_field_refs", "Watched fields"), ("session_or_bypass_sk", "Session / bypass"),
    ("business_effect_sk", "Business effect"), ("diagnostic_meaning_sk", "Diagnostic meaning"),
    ("calls", "Calls"), ("direct_mutations", "Direct mutations"),
    ("side_effects", "Side effects"), ("exceptions", "Exceptions"),
]
MUTATION_KEYS = [
    ("target_refs", "Targets"), ("writer_ref", "Writer"), ("writer_role", "Writer role"),
    ("event_sk", "Event"), ("condition_sk", "Condition"),
    ("session_or_bypass_sk", "Session / bypass"), ("direct_mutations_sk", "Direct mutation"),
    ("side_effects_sk", "Side effects"), ("diagnostic_meaning_sk", "Diagnostic meaning"),
    ("status", "Status"),
]
TEMPORAL_KEYS = [
    ("scope_refs", "Scope"), ("classification", "Classification"),
    ("transition_or_event_sk", "Event"), ("rollback_behavior_sk", "Rollback"),
    ("reconstructable", "Reconstructable"), ("history_limitations_sk", "Limitations"),
    ("status", "Status"),
]


def build_docx(data, output: Path):
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Cm(29.7), Cm(21.0)
    section.top_margin = section.bottom_margin = Cm(1.5)
    section.left_margin = section.right_margin = Cm(1.5)
    for name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3"):
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
    doc.styles["Normal"].font.size = Pt(9)
    header = section.header.paragraphs[0]
    header.text = f"{REPOSITORY}  |  canonical {BRANCH}"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Generated from canonical YAML and SQL  |  ")
    add_docx_field(footer, "PAGE")

    contract = data["contract.yaml"]
    doc.add_heading("KASO Data Catalog VYD v1.1", 0)
    doc.add_paragraph("Canonical human-readable publication", style="Subtitle")
    doc.add_paragraph(contract["purpose_sk"])
    docx_table(doc, ["Proveniencia", "Hodnota"], [
        ("Repository", REPOSITORY), ("Canonical branch", BRANCH),
        ("Contract", contract["contract_id"]), ("Contract version", "1.1"),
        ("Maturity", contract["maturity"]),
        ("Authoritative environment / owner", f"{contract['authoritative_environment']} / {contract['authoritative_owner']}"),
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
    field_sets = [
        ("MC.VYD_L", "fields-vyd_l.yaml"), ("MC.VYD_O", "fields-vyd_o.yaml"),
        ("MC.VYD_O_P_PRIJ", "fields-vyd_o_p_prij.yaml"),
    ]
    for object_name, filename in field_sets:
        doc.add_heading(object_name, level=2)
        rows = [(r["ordinal_position"], r["oracle_name"], r["datatype_raw"], "Y" if r["nullable"] else "N",
                 r.get("canonical_alias"), r.get("business_definition_sk"), r["status"])
                for r in data[filename]["records"]]
        docx_table(doc, ["#", "Oracle field", "Datatype", "NULL", "Canonical alias", "Definition", "Status"],
                   rows, [1.0, 3.2, 3.0, 1.0, 3.5, 10.3, 2.4])

    doc.add_heading("3 Constraints and relationships", level=1)
    docx_table(doc, ["Constraint", "Object", "Type", "Columns", "Referenced object", "Status"], [
        (r["oracle_name"], r["object_ref"], r["constraint_type"], r.get("column_refs"),
         r.get("referenced_object_ref"), r["status"]) for r in data["constraints.yaml"]["records"]
    ], [4.0, 4.0, 2.0, 6.0, 5.0, 2.5])
    for row in data["relationships.yaml"]["records"]:
        doc.add_heading(row["relationship_id"], level=2)
        docx_table(doc, ["Vlastnosť", "Canonical hodnota"], record_rows(row, [
            ("relationship_type", "Type"), ("cardinality", "Cardinality"),
            ("validation_summary_sk", "Validation"), ("fanout_risk", "Fan-out"),
            ("safe_usage_sk", "Safe usage"), ("targets", "Polymorphic targets"), ("status", "Status"),
        ]), [4.2, 20.0])

    doc.add_heading("4 State and value domains", level=1)
    docx_table(doc, ["Scope", "Raw", "Canonical", "Label", "Observed", "Count", "Status"], [
        (r["scope_ref"], r["raw_value"], r.get("canonical_value"), r.get("business_label_sk"),
         r.get("observed_live"), r.get("observed_count"), r["status"])
        for r in data["value-domains.yaml"]["records"]
    ], [5.0, 2.0, 2.0, 5.0, 2.0, 2.0, 2.5])

    for title, filename, key, keys in [
        ("5 Trigger flows", "flows.yaml", "flow_id", FLOW_KEYS),
        ("6 Mutation matrix", "mutations.yaml", "mutation_id", MUTATION_KEYS),
        ("7 Temporal contract", "temporal.yaml", "temporal_rule_id", TEMPORAL_KEYS),
    ]:
        doc.add_page_break()
        doc.add_heading(title, level=1)
        for row in data[filename]["records"]:
            doc.add_heading(row[key], level=2)
            docx_table(doc, ["Vlastnosť", "Canonical hodnota"], record_rows(row, keys), [4.2, 20.0])

    doc.add_heading("Data quality snapshot", level=2)
    docx_table(doc, ["ID", "Observation", "Snapshot", "Blocking", "Status", "Interpretation limit"], [
        (r["dq_id"], r["observation_sk"], r.get("snapshot_date"), r["blocking"], r["status"],
         r.get("interpretation_limit_sk")) for r in data["data-quality.yaml"]["records"]
    ], [3.5, 8.5, 2.0, 1.5, 2.5, 7.0])

    doc.add_page_break()
    doc.add_heading("8 Do not assume", level=1)
    docx_table(doc, ["Rule", "Scope", "Statement", "Consequence"], [
        (r["rule_id"], r["scope_refs"], r["statement_sk"], r["consequence_sk"])
        for r in data["do-not-assume.yaml"]["records"]
    ], [3.0, 5.0, 8.0, 8.0])
    doc.add_heading("9 Diagnostic playbooks", level=1)
    docx_table(doc, ["Symptom", "First SQL", "Proves", "Does not prove", "Next step", "Flows / boundaries"], [
        (r["symptom_sk"], r["first_sql_ref"], r.get("proves_sk"), r.get("does_not_prove_sk"),
         r.get("next_step_sk"), list(r.get("flow_refs", [])) + list(r.get("dependency_or_boundary_refs", [])))
        for r in data["playbooks.yaml"]["records"]
    ], [4.0, 2.5, 4.5, 4.5, 5.0, 4.0])

    doc.add_page_break()
    doc.add_heading("10 Canonical read-only SQL", level=1)
    for row in data["sql-registry.yaml"]["records"]:
        doc.add_heading(row["sql_id"], level=2)
        docx_table(doc, ["Vlastnosť", "Canonical hodnota"], record_rows(row, [
            ("title_sk", "Title"), ("purpose_sk", "Purpose"), ("input_parameters", "Bind inputs"),
            ("result_grain_sk", "Result grain"), ("fanout_warning_sk", "Fan-out / limit"),
            ("proves_sk", "Proves"), ("does_not_prove_sk", "Does not prove"), ("sql_file", "Canonical file"),
        ]), [4.2, 20.0])
        code = doc.add_paragraph()
        run = code.add_run(data["sql_bodies"][row["sql_id"]])
        run.font.name = "Courier New"
        run.font.size = Pt(7)

    doc.add_heading("11 Dependency, caller and writer summary", level=1)
    docx_table(doc, ["Metric", "Canonical value"], dependency_summary(data), [8.0, 16.0])
    doc.add_heading("12 Backlog and freeze revision", level=1)
    docx_table(doc, ["Backlog", "Status", "Blocking", "Question", "Reason", "Closure"], [
        (r["backlog_id"], r["status"], r["blocking"], r["question_sk"], r.get("reason_sk"),
         r.get("closure_condition_sk")) for r in data["backlog.yaml"]["records"]
    ], [3.5, 2.5, 1.5, 7.0, 6.0, 6.0])
    doc.add_heading("Revision history", level=2)
    docx_table(doc, ["Revision", "Version", "Date", "Breaking", "Change", "Reason"], [
        (r["revision_id"], r["contract_version"], r["date"], r["breaking_change"], r["change_sk"],
         r.get("reason_sk")) for r in data["revisions.yaml"]["records"]
    ], [4.0, 1.5, 2.0, 1.5, 9.0, 9.0])

    doc.core_properties.title = "KASO Data Catalog VYD v1.1"
    doc.core_properties.subject = "Canonical human-readable publication"
    doc.core_properties.author = REPOSITORY
    doc.core_properties.created = FIXED_TIME
    doc.core_properties.modified = FIXED_TIME
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    normalize_docx(output)


def register_pdf_fonts():
    directory = Path(reportlab.__file__).resolve().parent / "fonts"
    regular, bold = directory / "Vera.ttf", directory / "VeraBd.ttf"
    if not regular.is_file() or not bold.is_file():
        raise RuntimeError("Pinned ReportLab Unicode fonts are unavailable")
    pdfmetrics.registerFont(TTFont("VYDRegular", regular))
    pdfmetrics.registerFont(TTFont("VYDBold", bold))


def escape(value):
    return text(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pdf_table(rows, widths, styles, header=True):
    cooked = [[Paragraph(escape(value), styles["cell"]) for value in row] for row in rows]
    table = Table(cooked, colWidths=[width * mm for width in widths], repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9D9D9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                     ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                     ("FONTNAME", (0, 0), (-1, 0), "VYDBold")]
    for index in range(1 if header else 0, len(rows)):
        if index % 2 == 0:
            commands.append(("BACKGROUND", (0, index), (-1, index), colors.HexColor("#F2F6FA")))
    table.setStyle(TableStyle(commands))
    return table


def build_pdf(data, output: Path):
    register_pdf_fonts()
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("vyd-title", parent=base["Title"], fontName="VYDBold", fontSize=22, leading=26,
                                textColor=colors.black, spaceAfter=8),
        "h1": ParagraphStyle("vyd-h1", parent=base["Heading1"], fontName="VYDBold", fontSize=15, leading=18,
                             textColor=colors.black, spaceBefore=10, spaceAfter=6),
        "h2": ParagraphStyle("vyd-h2", parent=base["Heading2"], fontName="VYDBold", fontSize=11, leading=14,
                             textColor=colors.black, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("vyd-body", parent=base["BodyText"], fontName="VYDRegular", fontSize=8.5,
                               leading=11, textColor=colors.black),
        "cell": ParagraphStyle("vyd-cell", parent=base["BodyText"], fontName="VYDRegular", fontSize=6.7,
                               leading=8, textColor=colors.black, alignment=TA_LEFT),
        "code": ParagraphStyle("vyd-code", parent=base["Code"], fontName="Courier", fontSize=6.2,
                               leading=7.4, textColor=colors.black),
    }

    def header_footer(canvas, document):
        canvas.saveState()
        canvas.setFont("VYDRegular", 7)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(15 * mm, 10 * mm, f"{REPOSITORY} | canonical {BRANCH}")
        canvas.drawRightString(282 * mm, 10 * mm, f"Generated from canonical YAML and SQL | {document.page}")
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output), pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=14 * mm, bottomMargin=16 * mm, title="KASO Data Catalog VYD v1.1",
        author=REPOSITORY, invariant=1, pageCompression=1,
    )
    story = []
    contract = data["contract.yaml"]
    story += [Paragraph("KASO Data Catalog VYD v1.1", styles["title"]),
              Paragraph("Canonical human-readable publication", styles["h2"]),
              Paragraph(escape(contract["purpose_sk"]), styles["body"]), Spacer(1, 4 * mm)]
    story.append(pdf_table([
        ["Proveniencia", "Hodnota"], ["Repository", REPOSITORY], ["Canonical branch", BRANCH],
        ["Contract", contract["contract_id"]], ["Contract version", "1.1"], ["Maturity", contract["maturity"]],
        ["Authoritative environment / owner", f"{contract['authoritative_environment']} / {contract['authoritative_owner']}"],
        ["Generated from", "Canonical machine-readable YAML and canonical read-only SQL"],
        ["Canonical input SHA-256", data["canonical_sha256"]],
    ], [45, 215], styles))
    story += [PageBreak(), Paragraph("1 Contract scope", styles["h1"]), pdf_table([
        ["Vrstva", "Canonical obsah"], ["Scope includes", contract["scope_includes"]],
        ["Scope excludes", contract["scope_excludes"]], ["Limitations", contract["limitations_sk"]],
        ["Boundary refs", contract["boundary_refs"]],
    ], [45, 215], styles), Paragraph("2 Physical field inventory", styles["h1"])]
    for object_name, filename in [("MC.VYD_L", "fields-vyd_l.yaml"), ("MC.VYD_O", "fields-vyd_o.yaml"),
                                  ("MC.VYD_O_P_PRIJ", "fields-vyd_o_p_prij.yaml")]:
        story.append(Paragraph(object_name, styles["h2"]))
        rows = [["#", "Oracle field", "Datatype", "NULL", "Canonical alias", "Definition", "Status"]]
        rows += [[r["ordinal_position"], r["oracle_name"], r["datatype_raw"], "Y" if r["nullable"] else "N",
                  r.get("canonical_alias"), r.get("business_definition_sk"), r["status"]]
                 for r in data[filename]["records"]]
        story.append(pdf_table(rows, [8, 30, 27, 10, 33, 125, 27], styles))

    story += [PageBreak(), Paragraph("3 Constraints and relationships", styles["h1"])]
    rows = [["Constraint", "Object", "Type", "Columns", "Referenced object", "Status"]]
    rows += [[r["oracle_name"], r["object_ref"], r["constraint_type"], r.get("column_refs"),
              r.get("referenced_object_ref"), r["status"]] for r in data["constraints.yaml"]["records"]]
    story.append(pdf_table(rows, [38, 40, 18, 65, 55, 24], styles))
    for row in data["relationships.yaml"]["records"]:
        story.append(Paragraph(row["relationship_id"], styles["h2"]))
        story.append(pdf_table([["Vlastnosť", "Canonical hodnota"]] + record_rows(row, [
            ("relationship_type", "Type"), ("cardinality", "Cardinality"),
            ("validation_summary_sk", "Validation"), ("fanout_risk", "Fan-out"),
            ("safe_usage_sk", "Safe usage"), ("targets", "Polymorphic targets"), ("status", "Status"),
        ]), [45, 215], styles))
    story += [PageBreak(), Paragraph("4 State and value domains", styles["h1"])]
    rows = [["Scope", "Raw", "Canonical", "Label", "Observed", "Count", "Status"]]
    rows += [[r["scope_ref"], r["raw_value"], r.get("canonical_value"), r.get("business_label_sk"),
              r.get("observed_live"), r.get("observed_count"), r["status"]]
             for r in data["value-domains.yaml"]["records"]]
    story.append(pdf_table(rows, [55, 18, 20, 62, 20, 20, 25], styles))

    for title, filename, key, keys in [
        ("5 Trigger flows", "flows.yaml", "flow_id", FLOW_KEYS),
        ("6 Mutation matrix", "mutations.yaml", "mutation_id", MUTATION_KEYS),
        ("7 Temporal contract", "temporal.yaml", "temporal_rule_id", TEMPORAL_KEYS),
    ]:
        story += [PageBreak(), Paragraph(title, styles["h1"])]
        for row in data[filename]["records"]:
            story.append(Paragraph(row[key], styles["h2"]))
            story.append(pdf_table([["Vlastnosť", "Canonical hodnota"]] + record_rows(row, keys),
                                   [45, 215], styles))
    story.append(Paragraph("Data quality snapshot", styles["h2"]))
    rows = [["ID", "Observation", "Snapshot", "Blocking", "Status", "Interpretation limit"]]
    rows += [[r["dq_id"], r["observation_sk"], r.get("snapshot_date"), r["blocking"], r["status"],
              r.get("interpretation_limit_sk")] for r in data["data-quality.yaml"]["records"]]
    story.append(pdf_table(rows, [35, 92, 20, 16, 22, 75], styles))

    story += [PageBreak(), Paragraph("8 Do not assume", styles["h1"])]
    rows = [["Rule", "Scope", "Statement", "Consequence"]]
    rows += [[r["rule_id"], r["scope_refs"], r["statement_sk"], r["consequence_sk"]]
             for r in data["do-not-assume.yaml"]["records"]]
    story.append(pdf_table(rows, [28, 52, 90, 90], styles))
    story.append(Paragraph("9 Diagnostic playbooks", styles["h1"]))
    rows = [["Symptom", "First SQL", "Proves", "Does not prove", "Next step", "Flows / boundaries"]]
    rows += [[r["symptom_sk"], r["first_sql_ref"], r.get("proves_sk"), r.get("does_not_prove_sk"),
              r.get("next_step_sk"), list(r.get("flow_refs", [])) + list(r.get("dependency_or_boundary_refs", []))]
             for r in data["playbooks.yaml"]["records"]]
    story.append(pdf_table(rows, [43, 27, 48, 48, 52, 42], styles))

    story += [PageBreak(), Paragraph("10 Canonical read-only SQL", styles["h1"])]
    for row in data["sql-registry.yaml"]["records"]:
        story.append(Paragraph(row["sql_id"], styles["h2"]))
        story.append(pdf_table([["Vlastnosť", "Canonical hodnota"]] + record_rows(row, [
            ("title_sk", "Title"), ("purpose_sk", "Purpose"), ("input_parameters", "Bind inputs"),
            ("result_grain_sk", "Result grain"), ("fanout_warning_sk", "Fan-out / limit"),
            ("proves_sk", "Proves"), ("does_not_prove_sk", "Does not prove"), ("sql_file", "Canonical file"),
        ]), [45, 215], styles))
        story.append(Preformatted(data["sql_bodies"][row["sql_id"]], styles["code"], maxLineLength=150))
        story.append(Spacer(1, 3 * mm))
    story += [PageBreak(), Paragraph("11 Dependency, caller and writer summary", styles["h1"]),
              pdf_table([["Metric", "Canonical value"]] + dependency_summary(data), [75, 185], styles),
              Paragraph("12 Backlog and freeze revision", styles["h1"])]
    rows = [["Backlog", "Status", "Blocking", "Question", "Reason", "Closure"]]
    rows += [[r["backlog_id"], r["status"], r["blocking"], r["question_sk"], r.get("reason_sk"),
              r.get("closure_condition_sk")] for r in data["backlog.yaml"]["records"]]
    story.append(pdf_table(rows, [33, 22, 15, 65, 60, 65], styles))
    story.append(Paragraph("Revision history", styles["h2"]))
    rows = [["Revision", "Version", "Date", "Breaking", "Change", "Reason"]]
    rows += [[r["revision_id"], r["contract_version"], r["date"], r["breaking_change"], r["change_sk"],
              r.get("reason_sk")] for r in data["revisions.yaml"]["records"]]
    story.append(pdf_table(rows, [38, 15, 20, 15, 87, 85], styles))
    document.build(story, onFirstPage=header_footer, onLaterPages=header_footer)


def write_manifest(data, docx_path, pdf_path, manifest_path):
    manifest = {
        "publication_version": "1.0", "repository": REPOSITORY, "canonical_branch": BRANCH,
        "contract_ref": data["contract.yaml"]["contract_id"], "contract_version": "1.1",
        "generated_from": "canonical machine-readable YAML and canonical read-only SQL",
        "generator": "tools/generate_vyd_publication.py", "generator_version": GENERATOR_VERSION,
        "canonical_input_sha256": data["canonical_sha256"], "canonical_inputs": data["canonical_paths"],
        "artifacts": [
            {"path": docx_path.as_posix(), "sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest()},
            {"path": pdf_path.as_posix(), "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest()},
        ],
    }
    manifest_path.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")


def generate(root: Path, output_dir: Path):
    data = model(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    docx = output_dir / f"{BASENAME}.docx"
    pdf = output_dir / f"{BASENAME}.pdf"
    manifest = output_dir / f"{BASENAME}.manifest.yaml"
    build_docx(data, docx)
    build_pdf(data, pdf)
    write_manifest(data, Path("generated") / docx.name, Path("generated") / pdf.name, manifest)
    return docx, pdf, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output_dir or root / "generated").resolve()
    if args.check:
        with tempfile.TemporaryDirectory() as temporary:
            generated = generate(root, Path(temporary))
            expected = [root / "generated" / path.name for path in generated]
            mismatches = [expected_path.name for generated_path, expected_path in zip(generated, expected)
                          if not expected_path.is_file() or generated_path.read_bytes() != expected_path.read_bytes()]
            if mismatches:
                raise SystemExit("Generated publication differs: " + ", ".join(mismatches))
        print("PASS: VYD publication artifacts are deterministic and current")
    else:
        for path in generate(root, output):
            print(path)


if __name__ == "__main__":
    main()

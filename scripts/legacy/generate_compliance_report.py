"""
generate_compliance_report.py
-----------------------------
Create a PDF report summarizing extracted plan data and Neo4j compliance results.

Usage:
    python3 scripts/generate_compliance_report.py \
        --plan data/House-Floor-Plans-vector_output.json \
        --compliance data/House-Floor-Plans-vector_compliance.json \
        --output reports/House-Floor-Plans-report.pdf

Dependencies:
    pip install reportlab
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def log(msg: str) -> None:
    print(f"[INFO] {msg}")


def summarize_plan(plan_data: dict) -> dict:
    """Build a lightweight textual summary from extracted plan JSON."""
    summary = {
        "num_sheets": len(plan_data.get("sheets", [])),
        "sheet_titles": [],
        "rooms": set(),
        "dimensions": set(),
    }

    room_keywords = ["BEDROOM", "KITCHEN", "BATH", "LIVING", "GARAGE", "DINING", "LAUNDRY"]
    dim_pattern = re.compile(r"(\d+'\-\d+|\d+\"|\d+'\s*\d+/\d+\")")

    for sheet in plan_data.get("sheets", []):
        for block in sheet.get("text_blocks", []):
            text = block.get("text", "").upper()
            if any(k in text for k in ["FLOOR", "PLAN", "ELEVATION", "SECTION", "ROOF", "FOUNDATION"]):
                summary["sheet_titles"].append(text)
            if any(k in text for k in room_keywords):
                summary["rooms"].add(text)
            if dim_pattern.search(text):
                summary["dimensions"].add(text)

    summary["sheet_titles"] = sorted(set(summary["sheet_titles"]))
    summary["rooms"] = sorted(summary["rooms"])
    summary["dimensions"] = sorted(summary["dimensions"])[:50]  # limit preview
    return summary


def load_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def build_summary_section(story, styles, plan_summary):
    story.append(Paragraph("<b>Plan Overview</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(f"Sheets detected: <b>{plan_summary['num_sheets']}</b>", styles["BodyText"]))

    if plan_summary["sheet_titles"]:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Sheet titles:", styles["BodyText"]))
        for title in plan_summary["sheet_titles"][:10]:
            story.append(Paragraph(f"&bull; {title}", styles["Bullet"]))

    if plan_summary["rooms"]:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Room labels spotted:", styles["BodyText"]))
        for room in plan_summary["rooms"][:15]:
            story.append(Paragraph(f"&bull; {room}", styles["Bullet"]))

    if plan_summary["dimensions"]:
        story.append(Spacer(1, 0.1 * inch))
        dims_preview = ", ".join(plan_summary["dimensions"][:10])
        story.append(Paragraph(f"Sample dimensions: {dims_preview}", styles["BodyText"]))

    story.append(Spacer(1, 0.25 * inch))


def build_compliance_table(results, styles):
    if not results:
        return [
            Paragraph("No compliance rules were evaluated or returned from Neo4j.", styles["BodyText"])
        ]

    sorted_results = sorted(results, key=lambda r: (r["status"] != "PASS", -r.get("score", 0)))

    table_data = [
        ["Rule ID", "Description", "Status", "Score", "Matched Details"]
    ]

    for row in sorted_results:
        table_data.append([
            row.get("rule_id", ""),
            Paragraph(row.get("description", "N/A"), styles["BodyText"]),
            row.get("status", ""),
            f"{row.get('score', 0):.2f}",
            Paragraph(", ".join(row.get("matched_conditions", [])) or "—", styles["BodyText"])
        ])

    table = Table(table_data, colWidths=[1.1 * inch, 2.6 * inch, 0.9 * inch, 0.8 * inch, 2.0 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F3C7E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (2, 1), (3, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F2F2F7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F7F7FC")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [table]


def build_report(plan_path: Path, compliance_path: Path, output_path: Path, title: str):
    plan_data = load_json(plan_path)
    compliance_data = load_json(compliance_path)
    plan_summary = summarize_plan(plan_data)
    results = compliance_data.get("results", [])

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=9, leading=11))

    story = []
    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Small"]))
    story.append(Paragraph(f"Source plan JSON: {plan_path.name}", styles["Small"]))
    story.append(Paragraph(f"Compliance file: {compliance_path.name}", styles["Small"]))
    story.append(Spacer(1, 0.3 * inch))

    build_summary_section(story, styles, plan_summary)

    story.append(Paragraph("<b>Compliance Results</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.15 * inch))
    story.extend(build_compliance_table(results, styles))

    stats = {
        "total_rules": len(results),
        "passed": sum(1 for r in results if r.get("status") == "PASS"),
        "review": sum(1 for r in results if r.get("status") == "REVIEW"),
    }
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        f"Rules evaluated: <b>{stats['total_rules']}</b> | PASS: <b>{stats['passed']}</b> | REVIEW: <b>{stats['review']}</b>",
        styles["BodyText"]
    ))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(story)
    log(f"PDF report written to {output_path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate PDF compliance report from plan + Neo4j results.")
    parser.add_argument("--plan", required=True, help="Path to _output.json produced by extract_vector_plan.")
    parser.add_argument("--compliance", required=True, help="Path to _compliance.json produced by check_plan_compliance_neo4j.")
    parser.add_argument("--output", help="Destination PDF path (defaults to plan_compliance_report.pdf).")
    parser.add_argument("--title", default="Building Plan Compliance Report", help="Report title.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    plan_path = Path(args.plan)
    compliance_path = Path(args.compliance)

    if not plan_path.exists():
        raise FileNotFoundError(f"Plan JSON not found: {plan_path}")
    if not compliance_path.exists():
        raise FileNotFoundError(f"Compliance JSON not found: {compliance_path}")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = compliance_path.with_name(compliance_path.stem + "_report.pdf")

    build_report(plan_path, compliance_path, output_path, title=args.title)


if __name__ == "__main__":
    main(sys.argv[1:])

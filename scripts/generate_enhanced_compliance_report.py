"""
generate_enhanced_compliance_report.py
---------------------------------------
Create comprehensive PDF reports from component-based compliance checking.

Usage:
    python3 scripts/generate_enhanced_compliance_report.py \
        --components data/House-Floor-Plans-vector_components.json \
        --compliance data/House-Floor-Plans-vector_compliance.json \
        --output reports/compliance_report.pdf

Dependencies:
    pip install reportlab
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


# =============================================================================
# Utilities
# =============================================================================

def log(msg: str) -> None:
    print(f"[INFO] {msg}")


def load_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def get_status_color(status: str) -> colors.Color:
    """Return color based on compliance status."""
    colors_map = {
        "PASS": colors.HexColor("#28A745"),  # Green
        "FAIL": colors.HexColor("#DC3545"),  # Red
        "REVIEW": colors.HexColor("#FFC107"),  # Yellow/Orange
        "NOT_APPLICABLE": colors.HexColor("#6C757D")  # Gray
    }
    return colors_map.get(status, colors.grey)


# =============================================================================
# Report Sections
# =============================================================================

def build_title_page(story, styles, plan_name: str, title: str):
    """Build the title page."""
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        f"<b>Plan:</b> {plan_name}",
        ParagraphStyle(name="Subtitle", parent=styles["Normal"], fontSize=14, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}",
        ParagraphStyle(name="DateStyle", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER, textColor=colors.grey)
    ))
    story.append(PageBreak())


def build_executive_summary(story, styles, components_data: Dict, compliance_data: Dict):
    """Build executive summary section."""
    story.append(Paragraph("<b>Executive Summary</b>", styles["Heading1"]))
    story.append(Spacer(1, 0.2 * inch))

    # Extract summary data
    comp_summary = components_data.get("summary", {})
    compl_summary = compliance_data.get("summary", {})

    status_breakdown = compl_summary.get("status_breakdown", {})
    total_evals = compl_summary.get("total_evaluations", 0)
    pass_count = status_breakdown.get("PASS", 0)
    fail_count = status_breakdown.get("FAIL", 0)
    review_count = status_breakdown.get("REVIEW", 0)

    # Summary statistics table
    summary_data = [
        ["Metric", "Value"],
        ["Total Components Extracted", str(comp_summary.get("total_rooms", 0) +
                                          comp_summary.get("total_setbacks", 0) +
                                          comp_summary.get("total_geometric_setbacks", 0) +
                                          comp_summary.get("total_openings", 0) +
                                          comp_summary.get("total_parking", 0))],
        ["Total Rule Evaluations", str(total_evals)],
        ["", ""],
        ["✓ PASSED", str(pass_count)],
        ["✗ FAILED", str(fail_count)],
        ["⚠ NEEDS REVIEW", str(review_count)],
        ["", ""],
        ["Pass Rate", f"{compl_summary.get('pass_rate', 0):.1f}%"]
    ]

    summary_table = Table(summary_data, colWidths=[3.5 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F3C7E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        # Highlight status rows
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#D4EDDA")),  # PASS - green tint
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#F8D7DA")),  # FAIL - red tint
        ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#FFF3CD")),  # REVIEW - yellow tint
        ("FONTNAME", (0, 7), (-1, 7), "Helvetica-Bold"),
        ("FONTSIZE", (0, 7), (-1, 7), 12),
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 0.3 * inch))


def build_components_overview(story, styles, components_data: Dict):
    """Build overview of extracted components."""
    story.append(Paragraph("<b>Extracted Components Overview</b>", styles["Heading1"]))
    story.append(Spacer(1, 0.15 * inch))

    summary = components_data.get("summary", {})

    # Component counts table
    comp_data = [
        ["Component Type", "Count", "Details"],
        ["Rooms", str(summary.get("total_rooms", 0)),
         ", ".join(summary.get("room_types", [])) if summary.get("room_types") else "None"],
        ["Setbacks (Annotated)", str(summary.get("total_setbacks", 0)), "From plan annotations"],
        ["Setbacks (Geometric)", str(summary.get("total_geometric_setbacks", 0)), "Calculated from geometry"],
        ["Openings (Doors/Windows)", str(summary.get("total_openings", 0)), "Entries, exits, windows"],
        ["Parking Spaces", str(summary.get("total_parking", 0)), "Garages, carports, spaces"],
        ["Stairs/Ramps", str(summary.get("total_stairs", 0)), "Vertical circulation"],
        ["Fire Safety Features", str(summary.get("total_fire_safety", 0)), "Alarms, sprinklers, exits"],
        ["Accessibility Features", str(summary.get("total_accessibility", 0)), "ADA compliance elements"],
        ["Height/Level Markers", str(summary.get("total_height_levels", 0)), "Elevations, ceiling heights"],
    ]

    # Add site plan components if present
    sheets = components_data.get("sheets", [])
    if sheets:
        sheet = sheets[0]
        if sheet.get("lot_info"):
            lot_info = sheet["lot_info"]
            lot_details = f"Lot {lot_info.get('lot_number', 'N/A')}"
            if lot_info.get("lot_area"):
                lot_details += f", {lot_info['lot_area']} {lot_info.get('lot_area_unit', 'm²')}"
            comp_data.append(["Lot Information", "1", lot_details])

        if sheet.get("adjacent_properties"):
            adj_props = sheet["adjacent_properties"]
            details = ", ".join([p.get("identifier", "") for p in adj_props[:3]])
            if len(adj_props) > 3:
                details += f", +{len(adj_props) - 3} more"
            comp_data.append(["Adjacent Properties", str(len(adj_props)), details])

        if sheet.get("water_features"):
            water_feats = sheet["water_features"]
            details = ", ".join([f"{w.get('name', 'Unknown')} ({w.get('feature_type', '')})" for w in water_feats])
            comp_data.append(["Water Features", str(len(water_feats)), details])

        if sheet.get("north_pointer") and sheet["north_pointer"].get("found"):
            comp_data.append(["North Pointer", "1", "Orientation indicator present"])

    comp_table = Table(comp_data, colWidths=[2.2 * inch, 1.0 * inch, 3.8 * inch])
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F3C7E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(comp_table)
    story.append(Spacer(1, 0.3 * inch))

    # Building envelope details
    sheets = components_data.get("sheets", [])
    if sheets and sheets[0].get("building_envelope"):
        envelope = sheets[0]["building_envelope"]
        story.append(Paragraph("<b>Building Envelope</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))

        envelope_text = []
        if envelope.get("total_length") and envelope.get("total_width"):
            envelope_text.append(f"Dimensions: {envelope['total_length']}' × {envelope['total_width']}'")
        if envelope.get("floor_area"):
            envelope_text.append(f"Floor Area: {envelope['floor_area']:,.0f} sq ft")
        if envelope.get("perimeter"):
            envelope_text.append(f"Perimeter: {envelope['perimeter']:.0f} ft")

        if envelope_text:
            story.append(Paragraph(" | ".join(envelope_text), styles["BodyText"]))
            story.append(Spacer(1, 0.2 * inch))

    story.append(PageBreak())


def build_compliance_by_component_type(story, styles, evaluations: List[Dict]):
    """Build detailed compliance section grouped by component type."""
    story.append(Paragraph("<b>Detailed Compliance Findings</b>", styles["Heading1"]))
    story.append(Spacer(1, 0.15 * inch))

    # Group evaluations by component type
    by_type = defaultdict(list)
    for eval in evaluations:
        by_type[eval["component_type"]].append(eval)

    # Process each component type
    for comp_type in sorted(by_type.keys()):
        evals = by_type[comp_type]

        # Component type header
        type_title = comp_type.replace("_", " ").title()
        story.append(Paragraph(f"<b>{type_title}</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))

        # Build table for this component type
        table_data = [
            ["Component", "Rule", "Requirement", "Expected", "Actual", "Status"]
        ]

        for eval in evals:
            status = eval.get("status", "REVIEW")
            status_style = f'<font color="{get_status_color(status).hexval()}">{status}</font>'

            # Format expected and actual values
            expected = str(eval.get("expected_value", "N/A"))
            actual = str(eval.get("actual_value", "N/A"))
            if isinstance(eval.get("actual_value"), dict):
                actual = ", ".join(f"{k}:{v}" for k, v in eval["actual_value"].items() if v)

            table_data.append([
                Paragraph(eval.get("component_name", ""), styles["BodyText"]),
                eval.get("rule_id", ""),
                Paragraph(eval.get("requirement", "")[:100] + "..." if len(eval.get("requirement", "")) > 100 else eval.get("requirement", ""),
                         styles["BodyText"]),
                expected[:20],
                actual[:20],
                Paragraph(status_style, styles["BodyText"])
            ])

        detail_table = Table(table_data, colWidths=[1.3*inch, 0.7*inch, 2.5*inch, 0.8*inch, 0.8*inch, 0.7*inch])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F3C7E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (5, 0), (5, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        story.append(detail_table)
        story.append(Spacer(1, 0.25 * inch))


def build_recommendations(story, styles, evaluations: List[Dict]):
    """Build recommendations section based on failures and reviews."""
    story.append(PageBreak())
    story.append(Paragraph("<b>Recommendations & Action Items</b>", styles["Heading1"]))
    story.append(Spacer(1, 0.15 * inch))

    # Collect failures and reviews
    failures = [e for e in evaluations if e.get("status") == "FAIL"]
    reviews = [e for e in evaluations if e.get("status") == "REVIEW"]

    # Critical Issues (Failures)
    if failures:
        story.append(Paragraph("<b>Critical Issues Requiring Immediate Action</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))

        for idx, failure in enumerate(failures[:10], 1):  # Limit to top 10
            issue_text = f"<b>{idx}. {failure.get('component_name', 'Unknown Component')}</b><br/>"
            issue_text += f"Rule: {failure.get('rule_id', '')} - {failure.get('section_title', '')}<br/>"
            issue_text += f"Issue: {' '.join(failure.get('notes', ['No details available']))}<br/>"
            story.append(Paragraph(issue_text, styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))

        story.append(Spacer(1, 0.2 * inch))

    # Items Requiring Review
    if reviews:
        story.append(Paragraph("<b>Items Requiring Manual Review</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))

        review_summary = f"{len(reviews)} item(s) require manual verification by a certified reviewer."
        story.append(Paragraph(review_summary, styles["BodyText"]))
        story.append(Spacer(1, 0.15 * inch))

        for idx, review in enumerate(reviews[:15], 1):  # Limit to top 15
            review_text = f"<b>{idx}. {review.get('component_name', 'Unknown')}</b> - "
            review_text += f"{review.get('rule_id', '')}: {' '.join(review.get('notes', ['Review required']))}"
            story.append(Paragraph(review_text, styles["BodyText"]))
            story.append(Spacer(1, 0.08 * inch))


# =============================================================================
# Main Report Builder
# =============================================================================

def build_enhanced_report(
    components_path: Path,
    compliance_path: Path,
    output_path: Path,
    title: str
):
    """Build the complete enhanced compliance report."""
    log(f"Loading data...")
    components_data = load_json(components_path)
    compliance_data = load_json(compliance_path)

    plan_name = components_data.get("pdf_name", components_path.stem)
    evaluations = compliance_data.get("evaluations", [])

    log(f"Building PDF report...")

    # Setup styles
    styles = getSampleStyleSheet()
    if "Bullet" not in styles:
        styles.add(ParagraphStyle(
            name="Bullet",
            parent=styles["BodyText"],
            leftIndent=20,
            fontSize=10
        ))

    # Build story
    story = []

    build_title_page(story, styles, plan_name, title)
    build_executive_summary(story, styles, components_data, compliance_data)
    build_components_overview(story, styles, components_data)
    build_compliance_by_component_type(story, styles, evaluations)
    build_recommendations(story, styles, evaluations)

    # Generate PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    log(f"Writing PDF...")
    doc.build(story)
    log(f"✅ PDF report generated: {output_path}")


# =============================================================================
# CLI Entry Point
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate enhanced PDF compliance report from component-based analysis"
    )
    parser.add_argument("--components", required=True, help="Path to components JSON")
    parser.add_argument("--compliance", required=True, help="Path to compliance JSON")
    parser.add_argument("--output", help="Output PDF path (optional)")
    parser.add_argument("--title", default="Building Plan Compliance Report", help="Report title")
    return parser.parse_args()


def main():
    args = parse_args()

    components_path = Path(args.components)
    compliance_path = Path(args.compliance)

    if not components_path.exists():
        raise FileNotFoundError(f"Components file not found: {components_path}")
    if not compliance_path.exists():
        raise FileNotFoundError(f"Compliance file not found: {compliance_path}")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = compliance_path.with_name(compliance_path.stem + "_report.pdf")

    build_enhanced_report(components_path, compliance_path, output_path, args.title)


if __name__ == "__main__":
    main()

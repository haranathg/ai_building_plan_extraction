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
    PageBreak, KeepTogether, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
import os


# =============================================================================
# Branding & Page Template
# =============================================================================

class BrandedPageTemplate:
    """Custom page template with CompliCheck branding."""

    def __init__(self, logo_path=None):
        self.logo_path = logo_path
        self.version = "v1.1"
        self.product_name = "CompliCheck"

    def add_page_decorations(self, canvas_obj, doc):
        """Add header/footer with branding to each page."""
        canvas_obj.saveState()

        # Footer
        page_width, page_height = LETTER
        footer_y = 0.5 * inch

        # Add product name and version in footer (left)
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.setFillColor(colors.HexColor("#2F3C7E"))
        canvas_obj.drawString(0.75 * inch, footer_y, f"{self.product_name} {self.version}")

        # Add "AI-Powered Building Plan Compliance" tagline
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(0.75 * inch, footer_y - 0.15 * inch, "AI-Powered Building Plan Compliance")

        # Add page number (center)
        canvas_obj.setFont("Helvetica", 8)
        page_num = canvas_obj.getPageNumber()
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawCentredString(page_width / 2, footer_y, f"Page {page_num}")

        # Add logo placeholder (right) - if logo exists
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # Draw logo in bottom right
                logo_x = page_width - 1.5 * inch
                logo_y = footer_y - 0.15 * inch
                canvas_obj.drawImage(self.logo_path, logo_x, logo_y,
                                    width=0.7 * inch, height=0.4 * inch,
                                    preserveAspectRatio=True, mask='auto')
            except:
                # If logo fails, just show text
                canvas_obj.setFont("Helvetica-Oblique", 7)
                canvas_obj.setFillColor(colors.grey)
                canvas_obj.drawRightString(page_width - 0.75 * inch, footer_y,
                                          "Powered by AI")
        else:
            # No logo - show powered by text
            canvas_obj.setFont("Helvetica-Oblique", 7)
            canvas_obj.setFillColor(colors.grey)
            canvas_obj.drawRightString(page_width - 0.75 * inch, footer_y,
                                      "Powered by AI")

        canvas_obj.restoreState()


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
    """Build the title page with CompliCheck branding."""
    story.append(Spacer(1, 1.5 * inch))

    # CompliCheck branding - use larger font and proper line spacing
    branding_style = ParagraphStyle(
        name="Branding",
        parent=styles["Normal"],
        fontSize=32,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#2F3C7E"),
        fontName="Helvetica-Bold",
        spaceBefore=0,
        spaceAfter=10,
        leading=40  # Line height for proper spacing
    )
    story.append(Paragraph("CompliCheck", branding_style))

    # Version and tagline - separate line with space
    version_style = ParagraphStyle(
        name="Version",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.grey,
        fontName="Helvetica-Oblique",
        spaceBefore=5,
        spaceAfter=10,
        leading=14  # Line height
    )
    story.append(Paragraph("v1.1 - AI-Powered Building Plan Compliance", version_style))
    story.append(Spacer(1, 0.8 * inch))

    # Report title
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

    # Check for enrichment data
    has_enrichment = "llm_enrichment" in components_data
    enrichment = components_data.get("llm_enrichment", {})

    # Extract summary data
    comp_summary = components_data.get("summary", {})
    compl_summary = compliance_data.get("summary", {})

    status_breakdown = compl_summary.get("status_breakdown", {})
    total_evals = compl_summary.get("total_evaluations", 0)
    pass_count = status_breakdown.get("PASS", 0)
    fail_count = status_breakdown.get("FAIL", 0)
    review_count = status_breakdown.get("REVIEW", 0)

    # Add data quality indicator if enriched
    if has_enrichment:
        reconciliation = enrichment.get("reconciliation", {})
        quality_score = reconciliation.get("quality_score", 1.0)
        confidence = reconciliation.get("confidence_level", "unknown")

        quality_text = f"Data Quality: {quality_score:.2f}/1.0 ({confidence} confidence)"
        if quality_score < 0.7:
            quality_text += " ⚠️"
            story.append(Paragraph(
                f"<font color='#DC3545'><b>⚠️ Data Quality Alert:</b> Quality score below threshold ({quality_score:.2f}). "
                "Manual review recommended for all findings.</font>",
                styles["BodyText"]
            ))
            story.append(Spacer(1, 0.1 * inch))
        else:
            story.append(Paragraph(
                f"<font color='#28A745'><b>✓ Data Quality:</b> {quality_text}</font>",
                styles["BodyText"]
            ))
            story.append(Spacer(1, 0.1 * inch))

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
    sheets = components_data.get("sheets", [])

    # Check if this is a site plan (has lot_info) vs building floor plan
    is_site_plan = False
    if sheets and sheets[0].get("lot_info"):
        is_site_plan = True

    # Component counts table
    comp_data = [["Component Type", "Count", "Details"]]

    # Only show building components for actual building plans
    if not is_site_plan:
        comp_data.extend([
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
        ])
    else:
        # For site plans, only show geometric setbacks (relevant for both plan types)
        comp_data.append(["Setbacks (Geometric)", str(summary.get("total_geometric_setbacks", 0)), "Calculated from geometry"])

    # Add site plan components if present
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

        # Add documentation & administrative elements
        if sheet.get("title_block"):
            tb = sheet["title_block"]
            tb_details = []
            if tb.get("drawing_number"):
                tb_details.append(f"Dwg#{tb['drawing_number']}")
            if tb.get("revision_number"):
                tb_details.append(f"Rev{tb['revision_number']}")
            if tb.get("professional_stamp_found"):
                tb_details.append("Professional stamp")
            comp_data.append(["Title Block", "1", ", ".join(tb_details) if tb_details else "Found"])

        if sheet.get("legend") and sheet["legend"].get("found"):
            legend = sheet["legend"]
            symbol_count = legend.get('symbol_count', 0)
            # Only show if meaningful (< 50 symbols, otherwise likely false positive text extraction)
            if symbol_count > 0 and symbol_count < 50:
                comp_data.append(["Legend/Symbol Key", "1", f"{symbol_count} symbols"])

        if sheet.get("schedules"):
            schedules = sheet["schedules"]
            schedule_types = [s.get("schedule_type", "") for s in schedules]
            comp_data.append(["Schedules", str(len(schedules)), ", ".join(schedule_types)])

        # Add technical elements for building plans
        if not is_site_plan:
            if sheet.get("structural_elements"):
                structural = sheet["structural_elements"]
                comp_data.append(["Structural Elements", str(len(structural)), "Beams, columns, footings"])

            if sheet.get("mep_elements"):
                mep = sheet["mep_elements"]
                systems = set([m.get("system_type", "") for m in mep])
                comp_data.append(["MEP Elements", str(len(mep)), ", ".join(systems)])

            if sheet.get("drawing_notes"):
                notes = sheet["drawing_notes"]
                comp_data.append(["Drawing Notes", str(len(notes)), "Specifications and references"])

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

    # Building envelope details - only for building floor plans, not site plans
    if not is_site_plan and sheets and sheets[0].get("building_envelope"):
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

            # Format expected and actual values more intelligently
            expected_val = eval.get("expected_value", "N/A")
            actual_val = eval.get("actual_value", "N/A")

            # Format expected value
            if expected_val == "undefined" or expected_val is None:
                expected = "See rule"
            elif isinstance(expected_val, (int, float)):
                expected = str(expected_val)
            elif isinstance(expected_val, dict):
                expected = "See details"
            else:
                expected = str(expected_val)[:25]

            # Format actual value
            if isinstance(actual_val, dict):
                # For dicts, show key info
                if "type" in actual_val and "name" in actual_val:
                    actual = f"{actual_val.get('name', '')} ({actual_val.get('type', '')})"
                elif "area" in actual_val:
                    actual = f"{actual_val.get('area', '')} {actual_val.get('unit', '')}"
                else:
                    actual = "See details"
            elif isinstance(actual_val, (int, float)):
                actual = f"{actual_val:.1f}"
            else:
                actual = str(actual_val)[:25]

            # Truncate long text and wrap in Paragraph for proper wrapping
            requirement_text = eval.get("requirement", "")
            if len(requirement_text) > 150:
                requirement_text = requirement_text[:147] + "..."

            table_data.append([
                Paragraph(eval.get("component_name", ""), styles["BodyText"]),
                Paragraph(eval.get("rule_id", ""), styles["BodyText"]),
                Paragraph(requirement_text, styles["BodyText"]),
                Paragraph(expected, styles["BodyText"]),
                Paragraph(actual, styles["BodyText"]),
                Paragraph(status_style, styles["BodyText"])
            ])

        detail_table = Table(table_data, colWidths=[1.2*inch, 0.6*inch, 2.7*inch, 0.9*inch, 0.9*inch, 0.6*inch])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F3C7E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (5, 0), (5, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("WORDWRAP", (0, 0), (-1, -1), True),
        ]))

        story.append(detail_table)
        story.append(Spacer(1, 0.25 * inch))


def build_appendix_extracted_components(story, styles, components_data: Dict):
    """Build appendix listing all extracted components from the plan."""
    story.append(PageBreak())
    story.append(Paragraph("<b>Appendix: Extracted Plan Components</b>", styles["Heading1"]))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph(
        "This section lists all components that were successfully extracted from the building plan document.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 0.2 * inch))

    # Document-level information
    story.append(Paragraph("<b>Document Information</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))

    pdf_name = components_data.get("pdf_name", "Unknown")
    story.append(Paragraph(f"• PDF Filename: {pdf_name}", styles["BodyText"]))

    # Try to extract address/project name from filename
    if pdf_name:
        # Remove .pdf extension and split by common delimiters
        base_name = pdf_name.replace(".pdf", "").replace("_", " ").replace("-", " ")
        story.append(Paragraph(f"• Extracted Name: {base_name}", styles["BodyText"]))

    summary = components_data.get("summary", {})
    if summary.get("total_sheets"):
        story.append(Paragraph(f"• Total Sheets: {summary.get('total_sheets')}", styles["BodyText"]))

    story.append(Spacer(1, 0.2 * inch))

    sheets = components_data.get("sheets", [])
    if not sheets:
        story.append(Paragraph("No sheet data available.", styles["BodyText"]))
        return

    for sheet_idx, sheet in enumerate(sheets, 1):
        # Detect if this is a site plan (has lot_info)
        lot_info = sheet.get("lot_info")
        is_site_plan = lot_info is not None

        # Sheet header
        sheet_title = sheet.get("sheet_title") or f"Sheet {sheet_idx}"
        story.append(Paragraph(f"<b>Sheet {sheet_idx}: {sheet_title}</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))

        # Plan metadata
        story.append(Paragraph("<b>Plan Metadata</b>", styles["Heading3"]))
        metadata_items = []
        if sheet.get("scale"):
            metadata_items.append(f"• Scale: {sheet.get('scale')}")
        if sheet.get("north_pointer", {}).get("found"):
            metadata_items.append(f"• North Pointer: Found at location {sheet['north_pointer'].get('location', 'Unknown')}")

        for item in metadata_items:
            story.append(Paragraph(item, styles["BodyText"]))
        story.append(Spacer(1, 0.1 * inch))

        # Lot Information
        if lot_info:
            story.append(Paragraph("<b>Lot Information</b>", styles["Heading3"]))
            story.append(Paragraph(f"• Lot Number: {lot_info.get('lot_number', 'N/A')}", styles["BodyText"]))
            if lot_info.get("lot_area"):
                story.append(Paragraph(
                    f"• Lot Area: {lot_info.get('lot_area')} {lot_info.get('lot_area_unit', 'm²')}",
                    styles["BodyText"]
                ))
            if lot_info.get("boundary_dimensions"):
                story.append(Paragraph(
                    f"• Boundary Dimensions: {len(lot_info.get('boundary_dimensions'))} measurements found",
                    styles["BodyText"]
                ))
            story.append(Spacer(1, 0.1 * inch))

        # Geometric Setbacks
        geometric_setbacks = sheet.get("geometric_setbacks", [])
        if geometric_setbacks:
            story.append(Paragraph("<b>Setbacks</b>", styles["Heading3"]))
            for setback in geometric_setbacks:
                story.append(Paragraph(
                    f"• {setback.get('direction', 'Unknown').replace('_', ' ').title()}: {setback.get('avg_distance', 'N/A')} units",
                    styles["BodyText"]
                ))
            story.append(Spacer(1, 0.1 * inch))

        # Water Features
        water_features = sheet.get("water_features", [])
        if water_features:
            story.append(Paragraph("<b>Water Features</b>", styles["Heading3"]))
            for feature in water_features:
                story.append(Paragraph(
                    f"• {feature.get('name', 'Unnamed')} ({feature.get('feature_type', 'Unknown type')})",
                    styles["BodyText"]
                ))
            story.append(Spacer(1, 0.1 * inch))

        # Adjacent Properties
        adjacent_props = sheet.get("adjacent_properties", [])
        if adjacent_props:
            story.append(Paragraph("<b>Adjacent Properties</b>", styles["Heading3"]))
            for prop in adjacent_props:
                story.append(Paragraph(
                    f"• {prop.get('identifier', 'Unknown ID')}",
                    styles["BodyText"]
                ))
            story.append(Spacer(1, 0.1 * inch))

        # Rooms (only show for building plans, not site plans)
        rooms = sheet.get("rooms", [])
        if rooms and not lot_info:  # Don't show rooms for site plans
            story.append(Paragraph("<b>Rooms</b>", styles["Heading3"]))
            story.append(Paragraph(f"• Total Rooms: {len(rooms)}", styles["BodyText"]))
            room_types = {}
            for room in rooms:
                rt = room.get("room_type", "unknown")
                room_types[rt] = room_types.get(rt, 0) + 1
            for room_type, count in room_types.items():
                story.append(Paragraph(f"  - {room_type.title()}: {count}", styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))

        # Openings
        openings = sheet.get("openings", [])
        if openings:
            story.append(Paragraph("<b>Openings (Doors/Windows)</b>", styles["Heading3"]))
            story.append(Paragraph(f"• Total Openings: {len(openings)}", styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))

        # Parking
        parking = sheet.get("parking", [])
        if parking:
            story.append(Paragraph("<b>Parking</b>", styles["Heading3"]))
            story.append(Paragraph(f"• Total Parking Spaces: {len(parking)}", styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))

        # Stairs (skip for site plans - likely false positives)
        if not is_site_plan:
            stairs = sheet.get("stairs", [])
            if stairs:
                story.append(Paragraph("<b>Circulation (Stairs/Ramps)</b>", styles["Heading3"]))
                story.append(Paragraph(f"• Total Stairs/Ramps: {len(stairs)}", styles["BodyText"]))
                story.append(Spacer(1, 0.1 * inch))

        # Fire Safety (skip for site plans - likely false positives)
        if not is_site_plan:
            fire_safety = sheet.get("fire_safety", [])
            if fire_safety:
                story.append(Paragraph("<b>Fire Safety Features</b>", styles["Heading3"]))
                for fs in fire_safety:
                    story.append(Paragraph(
                        f"• {fs.get('feature_type', 'Unknown').title()}",
                        styles["BodyText"]
                    ))
                story.append(Spacer(1, 0.1 * inch))

        # Accessibility
        if not is_site_plan:
            accessibility = sheet.get("accessibility", [])
            if accessibility:
                story.append(Paragraph("<b>Accessibility Features</b>", styles["Heading3"]))
                story.append(Paragraph(f"• Total Accessibility Features: {len(accessibility)}", styles["BodyText"]))
                story.append(Spacer(1, 0.1 * inch))

        # Height Levels (skip for site plans - likely false positives like "Beach", "flood", "such")
        if not is_site_plan:
            height_levels = sheet.get("height_levels", [])
            if height_levels:
                story.append(Paragraph("<b>Height/Elevation Levels</b>", styles["Heading3"]))
                for level in height_levels:
                    story.append(Paragraph(
                        f"• {level.get('level_name', 'Unknown Level')}",
                        styles["BodyText"]
                    ))
                story.append(Spacer(1, 0.1 * inch))

        # Title Block
        title_block = sheet.get("title_block")
        if title_block:
            story.append(Paragraph("<b>Title Block Information</b>", styles["Heading3"]))
            if title_block.get("drawing_number"):
                story.append(Paragraph(f"• Drawing Number: {title_block.get('drawing_number')}", styles["BodyText"]))
            if title_block.get("revision_number"):
                story.append(Paragraph(f"• Revision: {title_block.get('revision_number')}", styles["BodyText"]))
            if title_block.get("drawing_date"):
                story.append(Paragraph(f"• Drawing Date: {title_block.get('drawing_date')}", styles["BodyText"]))
            if title_block.get("professional_stamp_found"):
                story.append(Paragraph("• Professional Stamp: Found", styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))

        # Legend (only show if it has meaningful symbols, not just text words)
        legend = sheet.get("legend")
        if legend and legend.get("found"):
            # Skip if it's just extracted text (symbol_count > 50 is likely false positive)
            symbol_count = legend.get('symbol_count', 0)
            if symbol_count > 0 and symbol_count < 50:
                story.append(Paragraph("<b>Legend/Symbol Key</b>", styles["Heading3"]))
                story.append(Paragraph(
                    f"• Legend Found: Yes ({symbol_count} symbols detected)",
                    styles["BodyText"]
                ))
                story.append(Spacer(1, 0.1 * inch))

        # Schedules (skip for site plans)
        if not is_site_plan:
            schedules = sheet.get("schedules", [])
            if schedules:
                story.append(Paragraph("<b>Schedules</b>", styles["Heading3"]))
                for sched in schedules:
                    story.append(Paragraph(
                        f"• {sched.get('schedule_type', 'Unknown').title()} Schedule: {sched.get('item_count', 0)} items",
                        styles["BodyText"]
                    ))
                story.append(Spacer(1, 0.1 * inch))

        # Structural Elements (skip for site plans)
        if not is_site_plan:
            structural = sheet.get("structural_elements", [])
            if structural:
                story.append(Paragraph("<b>Structural Elements</b>", styles["Heading3"]))
                story.append(Paragraph(f"• Total Structural Elements: {len(structural)}", styles["BodyText"]))
                story.append(Spacer(1, 0.1 * inch))

        # MEP Elements (skip for site plans - likely false positives)
        if not is_site_plan:
            mep = sheet.get("mep_elements", [])
            if mep:
                story.append(Paragraph("<b>MEP (Mechanical/Electrical/Plumbing)</b>", styles["Heading3"]))
                mep_types = {}
                for element in mep:
                    system = element.get('system_type', 'unknown')
                    mep_types[system] = mep_types.get(system, 0) + 1
                for system, count in mep_types.items():
                    story.append(Paragraph(f"• {system.upper()}: {count} elements", styles["BodyText"]))
                story.append(Spacer(1, 0.1 * inch))

        # Drawing Notes (only show if meaningful - more than just "NOTES:", "NOTE:")
        notes = sheet.get("drawing_notes", [])
        meaningful_notes = [n for n in notes if len(n.get('text', '')) > 10]  # Filter out short text like "NOTES:"
        if meaningful_notes:
            story.append(Paragraph("<b>Drawing Notes</b>", styles["Heading3"]))
            story.append(Paragraph(f"• Total Notes: {len(meaningful_notes)}", styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))

        # Annotations (only show if meaningful - more than just "NOTES:", "NOTE:")
        annotations = sheet.get("annotations", [])
        meaningful_annotations = [a for a in annotations if len(a) > 10]  # Filter short annotations
        if meaningful_annotations:
            story.append(Paragraph("<b>Annotations Detected</b>", styles["Heading3"]))
            story.append(Paragraph(f"• Total Annotations: {len(meaningful_annotations)}", styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))


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
# Evaluation Filtering & Deduplication
# =============================================================================

def filter_and_deduplicate_evaluations(
    evaluations: List[Dict],
    components_data: Dict
) -> List[Dict]:
    """
    Filter and deduplicate evaluations for cleaner reports.

    - For site plans: Remove building-specific rules (dwelling houses, building work)
    - Deduplicate rules by rule_id (keep highest confidence instance)
    """
    # Check if this is a site plan
    is_site_plan = False
    sheets = components_data.get("sheets", [])
    if sheets and sheets[0].get("lot_info"):
        is_site_plan = True

    # Building-specific keywords to filter out for site plans
    building_keywords = [
        "dwelling house",
        "building work",
        "class 10 building",
        "building height",
        "roofed area",
        "site cover"
    ]

    filtered = []
    for eval in evaluations:
        # For site plans, skip building-specific rules
        if is_site_plan:
            requirement = eval.get("requirement", "").lower()
            topic = eval.get("topic", "").lower()
            zones = [z.lower() for z in eval.get("zones", [])]

            # Check if any building keyword appears in requirement, topic, or zones
            is_building_specific = any(
                keyword in requirement or
                keyword in topic or
                any(keyword in zone for zone in zones)
                for keyword in building_keywords
            )

            if is_building_specific:
                continue  # Skip this evaluation

        filtered.append(eval)

    # Deduplicate by rule_id - keep highest confidence instance
    seen_rules = {}
    for eval in filtered:
        rule_id = eval.get("rule_id")
        confidence = eval.get("confidence", 0.0)

        if rule_id not in seen_rules or confidence > seen_rules[rule_id].get("confidence", 0.0):
            seen_rules[rule_id] = eval

    deduplicated = list(seen_rules.values())

    log(f"  Filtered evaluations: {len(evaluations)} -> {len(filtered)} (removed building-specific)")
    log(f"  Deduplicated evaluations: {len(filtered)} -> {len(deduplicated)} (removed duplicates)")

    return deduplicated


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

    # Filter and deduplicate evaluations
    evaluations = filter_and_deduplicate_evaluations(evaluations, components_data)

    # Update compliance_data summary to reflect filtered evaluations
    status_breakdown = {}
    for eval in evaluations:
        status = eval.get("status", "REVIEW")
        status_breakdown[status] = status_breakdown.get(status, 0) + 1

    compliance_data["summary"] = {
        "total_evaluations": len(evaluations),
        "status_breakdown": status_breakdown,
        "pass_rate": (status_breakdown.get("PASS", 0) / len(evaluations) * 100) if evaluations else 0.0
    }

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
    build_appendix_extracted_components(story, styles, components_data)

    # Generate PDF with branded page template
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check for logo file (you can place logo in assets/complicheck_logo.png)
    logo_path = None
    possible_logo_paths = [
        "assets/complicheck_logo.png",
        "complicheck_logo.png",
        os.path.join(os.path.dirname(__file__), "..", "assets", "complicheck_logo.png")
    ]
    for path in possible_logo_paths:
        if os.path.exists(path):
            logo_path = path
            break

    branding = BrandedPageTemplate(logo_path=logo_path)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=1.0 * inch,  # Extra space for footer branding
    )

    log(f"Writing PDF...")
    doc.build(story, onFirstPage=branding.add_page_decorations,
              onLaterPages=branding.add_page_decorations)
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

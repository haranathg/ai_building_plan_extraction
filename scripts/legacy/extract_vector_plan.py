"""
extract_vector_plan.py
----------------------
Extract geometry and text from architectural vector PDFs, and optionally summarize.

Usage:
    python3 extract_vector_plan.py --pdf path/to/plan.pdf [--summary]

Dependencies:
    pip install pdfminer.six pdfplumber shapely tqdm
"""

import os
import re
import json
import argparse
from pathlib import Path
from tqdm import tqdm
import pdfplumber
from shapely.geometry import LineString, Polygon, mapping
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import resolve1

# -------------------------------------------------------------
# Utility logging
# -------------------------------------------------------------
def log(msg): 
    print(f"[INFO] {msg}")

# -------------------------------------------------------------
# Detect PDF type (vector vs raster)
# -------------------------------------------------------------
from PyPDF2 import PdfReader

def detect_pdf_type(pdf_path):
    """Detect vector vs raster PDFs, including Form XObjects."""
    reader = PdfReader(pdf_path)
    ops = [" m", " l", " re", " S", " f", " c", " n"]
    found_vector = False

    for page in reader.pages:
        contents = page.get_contents()
        if not contents:
            continue

        # Normalize to a list
        contents_list = contents if isinstance(contents, list) else [contents]
        for c in contents_list:
            try:
                # Resolve indirect objects
                if hasattr(c, "get_object"):
                    c = c.get_object()
                if hasattr(c, "get_data"):
                    data = c.get_data().decode(errors="ignore")
                    if any(op in data for op in ops):
                        return "vector"
                # --- NEW: check XObjects (nested form streams)
                xobjs = page.get("/Resources", {}).get("/XObject", {})
                for name, xo in xobjs.items():
                    xo_obj = xo.get_object()
                    if hasattr(xo_obj, "get_data"):
                        subdata = xo_obj.get_data().decode(errors="ignore")
                        if any(op in subdata for op in ops):
                            found_vector = True
            except Exception:
                continue

    return "vector" if found_vector else "raster"

# -------------------------------------------------------------
# Core vector extraction
# -------------------------------------------------------------
def extract_vector_data(pdf_path: Path) -> dict:
    result = {"sheets": []}
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(tqdm(pdf.pages, desc="Extracting vector data")):
            sheet = {
                "page_number": page_idx + 1,
                "width": page.width,
                "height": page.height,
                "text_blocks": [],
                "lines": [],
                "rects": [],
                "curves": []
            }

            # --- Text extraction
            for obj in page.extract_words():
                sheet["text_blocks"].append({
                    "text": obj["text"],
                    "x0": obj["x0"],
                    "y0": obj["top"],
                    "x1": obj["x1"],
                    "y1": obj["bottom"]
                })

            # --- Vector shapes
            for line in page.lines:
                line_geom = LineString([(line["x0"], line["y0"]), (line["x1"], line["y1"])])
                sheet["lines"].append(mapping(line_geom))
            for rect in page.rects:
                x0, y0, x1, y1 = rect["x0"], rect["y0"], rect["x1"], rect["y1"]
                poly = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
                sheet["rects"].append(mapping(poly))
            for curve in page.curves:
                pts = [(seg["x0"], seg["y0"]) for seg in page.curves]
                if len(pts) > 1:
                    sheet["curves"].append(pts)

            result["sheets"].append(sheet)
    return result

# -------------------------------------------------------------
# Optional summarizer
# -------------------------------------------------------------
def summarize_extraction(data: dict) -> dict:
    summary = {
        "num_sheets": len(data.get("sheets", [])),
        "sheet_titles": [],
        "rooms": set(),
        "dimensions": set()
    }
    room_keywords = ["BEDROOM", "KITCHEN", "BATH", "LIVING", "GARAGE", "DINING", "LAUNDRY"]
    dim_pattern = re.compile(r"(\d+'\-\d+|\d+\"|\d+'\s*\d+/\d+\")")

    for sheet in data.get("sheets", []):
        for block in sheet["text_blocks"]:
            text = block["text"].upper()
            if any(k in text for k in ["FLOOR", "PLAN", "ELEVATION", "SECTION", "ROOF", "FOUNDATION"]):
                summary["sheet_titles"].append(text)
            if any(k in text for k in room_keywords):
                summary["rooms"].add(text)
            if dim_pattern.search(text):
                summary["dimensions"].add(text)

    summary["rooms"] = sorted(list(summary["rooms"]))
    summary["dimensions"] = sorted(list(summary["dimensions"]))[:50]  # cap preview
    summary["sheet_titles"] = sorted(list(set(summary["sheet_titles"])))
    return summary

# -------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Extract vector plan data from PDF")
    parser.add_argument("--pdf", required=True, help="Input PDF path")
    parser.add_argument("--summary", action="store_true", help="Return a summarized view")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    log(f"Checking PDF type for {pdf_path.name} ...")
    pdf_type = detect_pdf_type(pdf_path)

    if pdf_type != "vector":
        msg = "⚠️ This is not a full vector-based PDF and cannot be fully processed."
        log(msg)
        print(json.dumps({"status": "error", "message": msg}, indent=2))
        return

    log("✅ Vector PDF detected. Beginning extraction ...")
    data = extract_vector_data(pdf_path)

    # Auto-named output file
    out_path = pdf_path.with_name(pdf_path.stem + "_output.json")

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    log(f"Extraction complete. JSON saved at {out_path.name}")

    # If summary flag, generate concise overview
    if args.summary:
        summary = summarize_extraction(data)
        summary_file = pdf_path.with_name(pdf_path.stem + "_summary.json")
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        log(f"Summary saved at {summary_file.name}")
        print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()

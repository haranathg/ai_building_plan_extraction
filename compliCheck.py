#!/usr/bin/env python3
"""
CompliCheck v1.1 - AI-Powered Building Plan Compliance
========================================================

One-command solution to analyze building plans and generate compliance reports.

Usage:
    python3 compliCheck.py path/to/plan.pdf
    python3 compliCheck.py path/to/plan.pdf --output custom_report.pdf

This script:
1. Extracts components from the PDF plan
2. Checks compliance against building codes (Neo4j + Pinecone)
3. Generates a comprehensive PDF compliance report

Requirements:
- Neo4j database with building codes
- Pinecone vector database
- OpenAI API key for LLM analysis
- All credentials in .env file
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os


# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
SCRIPTS_DIR = SCRIPT_DIR / "scripts"
DATA_DIR = SCRIPT_DIR / "data"
REPORTS_DIR = SCRIPT_DIR / "reports"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Use virtual environment Python if available
VENV_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python3"
PYTHON_CMD = str(VENV_PYTHON) if VENV_PYTHON.exists() else "python3"

# Script paths
EXTRACT_SCRIPT = SCRIPTS_DIR / "extract_compliance_components.py"
CHECK_SCRIPT = SCRIPTS_DIR / "check_component_compliance.py"
REPORT_SCRIPT = SCRIPTS_DIR / "generate_enhanced_compliance_report.py"


# =============================================================================
# Utilities
# =============================================================================

def log(msg: str, level: str = "INFO") -> None:
    """Print formatted log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[94m",  # Blue
        "SUCCESS": "\033[92m",  # Green
        "ERROR": "\033[91m",  # Red
        "WARNING": "\033[93m",  # Yellow
    }
    reset = "\033[0m"
    color = colors.get(level, "")
    print(f"{color}[{level}] {timestamp}{reset} - {msg}")


def run_command(cmd: list, description: str) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        log(f"Running: {description}...", "INFO")
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        log(f"Failed: {description}", "ERROR")
        log(f"Error: {e.stderr}", "ERROR")
        return False, e.stderr
    except FileNotFoundError:
        log(f"Script not found for: {description}", "ERROR")
        return False, "Script not found"


# =============================================================================
# Pipeline Steps
# =============================================================================

def step1_extract_components(pdf_path: Path, output_path: Path) -> bool:
    """Step 1: Extract components from PDF."""
    log("=" * 60, "INFO")
    log("STEP 1: Extracting components from PDF plan", "INFO")
    log("=" * 60, "INFO")

    cmd = [
        PYTHON_CMD, str(EXTRACT_SCRIPT),
        "--pdf", str(pdf_path),
        "--output", str(output_path)
    ]

    success, output = run_command(cmd, "Component extraction")
    if success:
        log(f"✓ Components saved to: {output_path}", "SUCCESS")
    return success


def step2_check_compliance(components_path: Path, output_path: Path) -> bool:
    """Step 2: Check compliance against building codes."""
    log("=" * 60, "INFO")
    log("STEP 2: Checking compliance against building codes", "INFO")
    log("=" * 60, "INFO")

    cmd = [
        PYTHON_CMD, str(CHECK_SCRIPT),
        "--components", str(components_path),
        "--output", str(output_path)
    ]

    success, output = run_command(cmd, "Compliance checking")
    if success:
        log(f"✓ Compliance results saved to: {output_path}", "SUCCESS")
    return success


def step3_generate_report(components_path: Path, compliance_path: Path,
                          output_path: Path, plan_name: str) -> bool:
    """Step 3: Generate PDF compliance report."""
    log("=" * 60, "INFO")
    log("STEP 3: Generating comprehensive PDF report", "INFO")
    log("=" * 60, "INFO")

    cmd = [
        PYTHON_CMD, str(REPORT_SCRIPT),
        "--components", str(components_path),
        "--compliance", str(compliance_path),
        "--output", str(output_path),
        "--title", "Building Plan Compliance Report"
    ]

    success, output = run_command(cmd, "Report generation")
    if success:
        log(f"✓ PDF report generated: {output_path}", "SUCCESS")
    return success


# =============================================================================
# Main Pipeline
# =============================================================================

def run_complicheck(pdf_path: Path, output_pdf: Path = None) -> bool:
    """
    Run the complete CompliCheck pipeline.

    Args:
        pdf_path: Path to input PDF plan
        output_pdf: Optional custom output path for final report

    Returns:
        True if successful, False otherwise
    """
    # Validate input
    if not pdf_path.exists():
        log(f"PDF file not found: {pdf_path}", "ERROR")
        return False

    if not pdf_path.suffix.lower() == '.pdf':
        log(f"Input must be a PDF file: {pdf_path}", "ERROR")
        return False

    # Generate file names
    base_name = pdf_path.stem
    components_json = DATA_DIR / f"{base_name}_components.json"
    compliance_json = DATA_DIR / f"{base_name}_compliance.json"

    if output_pdf is None:
        output_pdf = REPORTS_DIR / f"{base_name}_CompliCheck_Report.pdf"

    # Print header
    log("", "INFO")
    log("╔" + "═" * 58 + "╗", "INFO")
    log("║" + " " * 12 + "CompliCheck v1.1" + " " * 30 + "║", "INFO")
    log("║" + " " * 8 + "AI-Powered Building Plan Compliance" + " " * 15 + "║", "INFO")
    log("╚" + "═" * 58 + "╝", "INFO")
    log("", "INFO")
    log(f"Input PDF: {pdf_path.name}", "INFO")
    log(f"Output Report: {output_pdf.name}", "INFO")
    log("", "INFO")

    # Check for required environment
    if not (SCRIPT_DIR / ".env").exists():
        log("WARNING: .env file not found. Database connections may fail.", "WARNING")

    # Run pipeline steps
    start_time = datetime.now()

    # Step 1: Extract components
    if not step1_extract_components(pdf_path, components_json):
        return False

    # Step 2: Check compliance
    if not step2_check_compliance(components_json, compliance_json):
        log("WARNING: Compliance checking failed, but continuing...", "WARNING")
        # We can still generate a report with just components

    # Step 3: Generate report
    if not step3_generate_report(components_json, compliance_json,
                                  output_pdf, base_name):
        return False

    # Success summary
    elapsed = (datetime.now() - start_time).total_seconds()
    log("", "INFO")
    log("=" * 60, "SUCCESS")
    log("✓ CompliCheck pipeline completed successfully!", "SUCCESS")
    log("=" * 60, "SUCCESS")
    log(f"Time elapsed: {elapsed:.1f} seconds", "INFO")
    log("", "INFO")
    log("Generated files:", "INFO")
    log(f"  • Components: {components_json}", "INFO")
    log(f"  • Compliance: {compliance_json}", "INFO")
    log(f"  • Report PDF: {output_pdf}", "INFO")
    log("", "INFO")
    log(f"Open your report: open {output_pdf}", "SUCCESS")
    log("", "INFO")

    return True


# =============================================================================
# CLI Entry Point
# =============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CompliCheck v1.1 - AI-Powered Building Plan Compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 compliCheck.py plans/my_floor_plan.pdf
  python3 compliCheck.py plans/site_plan.pdf --output custom_report.pdf

For more information, visit: https://github.com/yourusername/complicheck
        """
    )

    parser.add_argument(
        "pdf",
        type=Path,
        help="Path to building plan PDF file"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Custom output path for PDF report (optional)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="CompliCheck v1.1"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    try:
        success = run_complicheck(args.pdf, args.output)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log("\nOperation cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

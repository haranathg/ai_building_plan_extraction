#!/usr/bin/env python3
"""
CompliCheck v2.0 - AI-Powered Building Plan Compliance with LLM Enrichment
==========================================================================

Enhanced pipeline that integrates LLM enrichment for improved accuracy:

Pipeline:
    PDF → Extract Components → LLM Enrichment → Check Compliance → Generate Report

Usage:
    python3 compliCheckV2.py path/to/plan.pdf [options]

Options:
    --enable-enrichment    Enable LLM enrichment layer (requires ANTHROPIC_API_KEY)
    --skip-enrichment      Skip enrichment and use standard processing
    --enrichment-ops       Specify enrichment operations: infer_metadata, categorize, label, reconcile, all
    --use-bedrock-kb       Use AWS Bedrock Knowledge Base for compliance checking
    --kb-id                Bedrock Knowledge Base ID (overrides BEDROCK_KB_ID env var)
    --output-dir           Directory for output files (default: reports/)
    --keep-intermediates   Keep intermediate JSON files for debugging

Features:
    - Automatic fallback if enrichment fails
    - Quality score indicators in reports
    - Enhanced plan type detection
    - Critical component prioritization
    - AWS Bedrock Knowledge Base integration for compliance
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import json

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars already set

# Colors for terminal output
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Color.HEADER}{Color.BOLD}{'='*70}{Color.ENDC}")
    print(f"{Color.HEADER}{Color.BOLD}{text:^70}{Color.ENDC}")
    print(f"{Color.HEADER}{Color.BOLD}{'='*70}{Color.ENDC}\n")

def print_step(step_num, text):
    print(f"{Color.OKBLUE}{Color.BOLD}[Step {step_num}]{Color.ENDC} {text}")

def print_success(text):
    print(f"{Color.OKGREEN}✓ {text}{Color.ENDC}")

def print_warning(text):
    print(f"{Color.WARNING}⚠ {text}{Color.ENDC}")

def print_error(text):
    print(f"{Color.FAIL}✗ {text}{Color.ENDC}")

def run_command(cmd, description, capture_output=False):
    """Run a shell command and return success status."""
    print(f"  {Color.OKCYAN}Running:{Color.ENDC} {description}")
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, result.stdout
        else:
            result = subprocess.run(cmd, check=True)
            return True, None
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if capture_output and e.stderr:
            print(f"  Error: {e.stderr}")
        return False, None

# Script paths
SCRIPT_DIR = Path(__file__).parent.resolve()
EXTRACT_SCRIPT = SCRIPT_DIR / "scripts" / "extract_compliance_components.py"
ENRICHMENT_SCRIPT = SCRIPT_DIR / "scripts" / "llm_enrichment_layer.py"
CHECK_SCRIPT = SCRIPT_DIR / "scripts" / "check_component_compliance.py"
CHECK_SCRIPT_BEDROCK = SCRIPT_DIR / "scripts" / "check_component_compliance_bedrock.py"
REPORT_SCRIPT = SCRIPT_DIR / "scripts" / "generate_enhanced_compliance_report.py"

# Find Python executable
VENV_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python3"
PYTHON_CMD = str(VENV_PYTHON) if VENV_PYTHON.exists() else "python3"

def step1_extract_components(pdf_path: Path, output_path: Path) -> bool:
    """Extract components from PDF."""
    print_step(1, "Extracting components from PDF")
    cmd = [PYTHON_CMD, str(EXTRACT_SCRIPT), "--pdf", str(pdf_path), "--output", str(output_path)]
    success, _ = run_command(cmd, "Component extraction")
    if success:
        print_success(f"Components saved: {output_path.name}")
    return success

def step2_enrich_components(components_path: Path, output_path: Path, operations: list) -> tuple:
    """Enrich components with LLM analysis (optional)."""
    print_step(2, "Enriching components with LLM analysis")

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print_warning("ANTHROPIC_API_KEY not found in environment")
        print(f"  To enable enrichment, add to .env file:")
        print(f"    ANTHROPIC_API_KEY=sk-ant-...")
        print(f"  Or export: export ANTHROPIC_API_KEY=sk-ant-...")
        return False, components_path

    # Check if enrichment script exists
    if not ENRICHMENT_SCRIPT.exists():
        print_warning(f"Enrichment script not found: {ENRICHMENT_SCRIPT}")
        return False, components_path

    cmd = [
        PYTHON_CMD, str(ENRICHMENT_SCRIPT),
        "--input", str(components_path),
        "--output", str(output_path),
        "--operations"
    ] + operations

    success, _ = run_command(cmd, "LLM enrichment")

    if success:
        print_success(f"Enriched data saved: {output_path.name}")
        return True, output_path
    else:
        print_warning("Enrichment failed - continuing with unenriched data")
        return False, components_path

def step3_check_compliance(components_path: Path, output_path: Path, use_bedrock: bool = False, kb_id: str = None) -> bool:
    """Check compliance against rules database."""
    print_step(3, "Checking compliance against building codes")

    if use_bedrock:
        print(f"  {Color.OKCYAN}Using AWS Bedrock Knowledge Base{Color.ENDC}")
        cmd = [
            PYTHON_CMD, str(CHECK_SCRIPT_BEDROCK),
            "--components", str(components_path),
            "--output", str(output_path)
        ]
        if kb_id:
            cmd.extend(["--kb-id", kb_id])
    else:
        print(f"  {Color.OKCYAN}Using Neo4j + Pinecone{Color.ENDC}")
        cmd = [
            PYTHON_CMD, str(CHECK_SCRIPT),
            "--components", str(components_path),
            "--output", str(output_path)
        ]

    success, _ = run_command(cmd, "Compliance checking")
    if success:
        print_success(f"Compliance results saved: {output_path.name}")
    return success

def step4_generate_report(components_path: Path, compliance_path: Path,
                          output_path: Path, plan_name: str) -> bool:
    """Generate PDF compliance report."""
    print_step(4, "Generating PDF compliance report")
    cmd = [
        PYTHON_CMD, str(REPORT_SCRIPT),
        "--components", str(components_path),
        "--compliance", str(compliance_path),
        "--output", str(output_path)
    ]
    success, _ = run_command(cmd, "Report generation")
    if success:
        print_success(f"Report generated: {output_path.name}")
    return success

def run_complicheck(
    pdf_path: Path,
    enable_enrichment: bool = True,
    enrichment_ops: list = None,
    output_dir: Path = None,
    keep_intermediates: bool = False,
    use_bedrock_kb: bool = False,
    kb_id: str = None
) -> bool:
    """Run the complete CompliCheck v2.0 pipeline."""

    mode = "Bedrock KB" if use_bedrock_kb else "Neo4j + Pinecone"
    print_header(f"CompliCheck v2.0 - Enhanced Compliance Checking ({mode})")

    # Validate input
    if not pdf_path.exists():
        print_error(f"PDF file not found: {pdf_path}")
        return False

    # Setup output paths
    if output_dir is None:
        output_dir = SCRIPT_DIR / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = pdf_path.stem

    # Add 'e' suffix for enriched files to distinguish from non-enriched
    suffix = "e" if enable_enrichment else ""
    components_file = output_dir / f"{base_name}_components.json"
    enriched_file = output_dir / f"{base_name}{suffix}_enriched.json"
    compliance_file = output_dir / f"{base_name}{suffix}_compliance.json"
    report_file = output_dir / f"{base_name}{suffix}_CompliCheck_Report.pdf"

    start_time = datetime.now()

    # === STEP 1: Extract Components ===
    if not step1_extract_components(pdf_path, components_file):
        return False

    # === STEP 2: Enrich Components (Optional) ===
    enriched = False
    working_components_file = components_file

    if enable_enrichment:
        if enrichment_ops is None:
            enrichment_ops = ["all"]

        enriched, working_components_file = step2_enrich_components(
            components_file, enriched_file, enrichment_ops
        )

        if enriched:
            print_success("Using enriched data for compliance checking")
        else:
            print_warning("Using standard (unenriched) data")
    else:
        print_step(2, "Enrichment disabled - using standard processing")

    # === STEP 3: Check Compliance ===
    if not step3_check_compliance(working_components_file, compliance_file, use_bedrock_kb, kb_id):
        return False

    # === STEP 4: Generate Report ===
    if not step4_generate_report(working_components_file, compliance_file,
                                 report_file, base_name):
        return False

    # === Cleanup ===
    if not keep_intermediates and not enriched:
        # Only clean up non-enriched intermediate files
        if components_file.exists():
            components_file.unlink()
            print(f"  Cleaned up: {components_file.name}")
        if compliance_file.exists():
            compliance_file.unlink()
            print(f"  Cleaned up: {compliance_file.name}")

    # === Summary ===
    elapsed = (datetime.now() - start_time).total_seconds()
    print_header("CompliCheck v2.0 Complete")
    print(f"  Input PDF:      {pdf_path.name}")
    print(f"  Output Report:  {report_file}")
    print(f"  Enrichment:     {'✓ Enabled' if enriched else '✗ Disabled'}")
    print(f"  Elapsed Time:   {elapsed:.1f} seconds")

    if keep_intermediates:
        print(f"\n  Intermediate Files:")
        print(f"    - {components_file}")
        if enriched:
            print(f"    - {enriched_file}")
        print(f"    - {compliance_file}")

    print(f"\n{Color.OKGREEN}{Color.BOLD}✓ Success!{Color.ENDC} Open report: {report_file}\n")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="CompliCheck v2.0 - Enhanced AI-Powered Building Plan Compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard run with enrichment (Neo4j + Pinecone)
  python3 compliCheckV2.py data/plan.pdf

  # Use AWS Bedrock Knowledge Base for compliance
  python3 compliCheckV2.py data/plan.pdf --use-bedrock-kb

  # Skip enrichment for faster processing
  python3 compliCheckV2.py data/plan.pdf --skip-enrichment

  # Use Bedrock KB with specific KB ID
  python3 compliCheckV2.py data/plan.pdf --use-bedrock-kb --kb-id YOUR_KB_ID

  # Run only specific enrichment operations
  python3 compliCheckV2.py data/plan.pdf --enrichment-ops infer_metadata categorize

  # Keep intermediate files for debugging
  python3 compliCheckV2.py data/plan.pdf --keep-intermediates
        """
    )

    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the building plan PDF"
    )

    parser.add_argument(
        "--enable-enrichment",
        action="store_true",
        default=True,
        help="Enable LLM enrichment (default: enabled)"
    )

    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Skip LLM enrichment for faster processing"
    )

    parser.add_argument(
        "--enrichment-ops",
        nargs="+",
        choices=["infer_metadata", "categorize", "label", "reconcile", "all"],
        default=None,
        help="Enrichment operations to run (default: all)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: reports/)"
    )

    parser.add_argument(
        "--keep-intermediates",
        action="store_true",
        help="Keep intermediate JSON files for debugging"
    )

    parser.add_argument(
        "--use-bedrock-kb",
        action="store_true",
        help="Use AWS Bedrock Knowledge Base for compliance checking (instead of Neo4j + Pinecone)"
    )

    parser.add_argument(
        "--kb-id",
        type=str,
        default=None,
        help="AWS Bedrock Knowledge Base ID (overrides BEDROCK_KB_ID env var)"
    )

    args = parser.parse_args()

    # Handle enrichment flags
    enable_enrichment = args.enable_enrichment and not args.skip_enrichment

    try:
        success = run_complicheck(
            pdf_path=args.pdf_path,
            enable_enrichment=enable_enrichment,
            enrichment_ops=args.enrichment_ops,
            output_dir=args.output_dir,
            keep_intermediates=args.keep_intermediates,
            use_bedrock_kb=args.use_bedrock_kb,
            kb_id=args.kb_id
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print_error("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

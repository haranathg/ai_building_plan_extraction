"""
config.py
---------
Configuration settings for CompliCheck v2.0 pipeline

This file contains all configurable parameters for the compliance checking pipeline.
Modify these settings to customize behavior without changing code.
"""

import os
from pathlib import Path

# =============================================================================
# Pipeline Settings
# =============================================================================

class PipelineConfig:
    """Main pipeline configuration."""

    # Enable/disable pipeline steps
    ENABLE_EXTRACTION = True
    ENABLE_ENRICHMENT = True  # Can be overridden by CLI flag
    ENABLE_COMPLIANCE_CHECK = True
    ENABLE_REPORT_GENERATION = True

    # Fallback behavior
    CONTINUE_ON_ENRICHMENT_FAILURE = True  # Continue with unenriched data if enrichment fails
    CONTINUE_ON_COMPLIANCE_FAILURE = False  # Stop if compliance check fails

    # Performance
    PARALLEL_PROCESSING = False  # Future: process multiple sheets in parallel
    MAX_WORKERS = 4

    # Output
    DEFAULT_OUTPUT_DIR = Path("reports")
    KEEP_INTERMEDIATE_FILES = False  # Keep JSON files between steps
    OVERWRITE_EXISTING = True

# =============================================================================
# LLM Enrichment Settings
# =============================================================================

class EnrichmentConfig:
    """LLM enrichment layer configuration."""

    # API Settings
    API_PROVIDER = "anthropic"  # Currently only Anthropic supported
    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 4096

    # Operations to run
    DEFAULT_OPERATIONS = ["all"]  # Options: infer_metadata, categorize, label, reconcile, all

    # Performance
    ENABLE_CACHING = True  # Cache enrichment results to avoid re-processing
    CACHE_DIR = Path(".cache/enrichment")
    CACHE_EXPIRY_DAYS = 7

    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = 50
    RETRY_ON_RATE_LIMIT = True
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5

    # Cost Control
    MAX_COST_PER_DOCUMENT = 0.50  # USD - stop if estimated cost exceeds this
    WARN_HIGH_COST = True

    # Quality Thresholds
    MIN_QUALITY_SCORE = 0.5  # Warn if quality score below this
    SKIP_ENRICHMENT_FOR_SIMPLE_DOCS = True  # Skip enrichment for single-sheet site plans

# =============================================================================
# Knowledge Base Settings
# =============================================================================

class KnowledgeBaseConfig:
    """Neo4j and Pinecone configuration."""

    # Neo4j
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://your-instance.databases.neo4j.io")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    # Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX", "planning-rules")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

    # Query Settings
    DEFAULT_TOP_K = 5  # Number of rules to retrieve per component
    MIN_SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score to consider

    # LLM Relevance Filtering
    USE_LLM_RELEVANCE_CHECK = True  # Use LLM to filter irrelevant rules
    OPENAI_MODEL = "gpt-4o-mini"  # Model for relevance checking

# =============================================================================
# Report Generation Settings
# =============================================================================

class ReportConfig:
    """PDF report generation configuration."""

    # Branding
    PRODUCT_NAME = "CompliCheck"
    VERSION = "v2.0"
    TAGLINE = "AI-Powered Building Plan Compliance"

    # Logo
    LOGO_PATH_OPTIONS = [
        Path("assets/complicheck_logo.png"),
        Path("complicheck_logo.png"),
        Path(__file__).parent / "assets" / "complicheck_logo.png"
    ]

    # Page Layout
    PAGE_SIZE = "LETTER"  # or "A4"
    MARGINS = {
        "left": 0.75,    # inches
        "right": 0.75,
        "top": 0.75,
        "bottom": 1.0    # Extra space for footer
    }

    # Colors
    PRIMARY_COLOR = "#2F3C7E"
    SUCCESS_COLOR = "#28A745"
    WARNING_COLOR = "#FFC107"
    DANGER_COLOR = "#DC3545"

    # Content
    INCLUDE_EXECUTIVE_SUMMARY = True
    INCLUDE_COMPONENTS_OVERVIEW = True
    INCLUDE_DETAILED_COMPLIANCE = True
    INCLUDE_RECOMMENDATIONS = True
    INCLUDE_APPENDIX = True

    # Quality Indicators
    SHOW_DATA_QUALITY_SCORE = True  # Show enrichment quality score
    SHOW_CONFIDENCE_LEVELS = True
    HIGHLIGHT_LOW_QUALITY = True

    # Filtering
    HIDE_FALSE_POSITIVES_IN_APPENDIX = True  # Filter out likely false positives
    MAX_LEGEND_SYMBOLS = 50  # Hide legend if more than this (likely text extraction error)
    MIN_NOTE_LENGTH = 10  # Hide notes shorter than this

# =============================================================================
# Extraction Settings
# =============================================================================

class ExtractionConfig:
    """PDF extraction configuration."""

    # Processing
    DPI = 300  # Resolution for image-based PDFs
    EXTRACT_IMAGES = True
    EXTRACT_VECTOR = True

    # Component Detection
    ROOM_MIN_AREA = 10  # sq ft - minimum area to consider as room
    SETBACK_PRECISION = 2  # decimal places for setback measurements

    # Text Extraction
    MIN_TEXT_LENGTH = 2  # Minimum characters to consider as text
    FILTER_GIBBERISH = True

# =============================================================================
# Logging Settings
# =============================================================================

class LoggingConfig:
    """Logging and progress display configuration."""

    # Log Levels
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_TO_FILE = False
    LOG_FILE = Path("logs/complicheck.log")

    # Progress Display
    SHOW_PROGRESS_BARS = True
    SHOW_STEP_NUMBERS = True
    COLORIZE_OUTPUT = True

    # Verbosity
    VERBOSE = False  # Show detailed operation info
    SHOW_TIMING = True  # Show elapsed time for each step

# =============================================================================
# Advanced Settings
# =============================================================================

class AdvancedConfig:
    """Advanced configuration for power users."""

    # Experimental Features
    ENABLE_EXPERIMENTAL_FEATURES = False

    # Data Validation
    VALIDATE_JSON_SCHEMA = False  # Validate JSON structure between steps
    STRICT_MODE = False  # Fail on warnings

    # Debugging
    DEBUG_MODE = False
    SAVE_LLM_PROMPTS = False  # Save all LLM prompts for debugging
    SAVE_LLM_RESPONSES = False

    # Custom Rules
    CUSTOM_RULES_PATH = None  # Path to custom rule definitions
    MERGE_CUSTOM_WITH_KB = True

# =============================================================================
# Helper Functions
# =============================================================================

def get_config(section: str = "pipeline"):
    """Get configuration for a specific section."""
    configs = {
        "pipeline": PipelineConfig,
        "enrichment": EnrichmentConfig,
        "kb": KnowledgeBaseConfig,
        "report": ReportConfig,
        "extraction": ExtractionConfig,
        "logging": LoggingConfig,
        "advanced": AdvancedConfig,
    }
    return configs.get(section.lower(), PipelineConfig)

def validate_config():
    """Validate configuration settings."""
    errors = []

    # Check required API keys
    if EnrichmentConfig.ENABLE_CACHING and not EnrichmentConfig.CACHE_DIR.exists():
        EnrichmentConfig.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if PipelineConfig.ENABLE_COMPLIANCE_CHECK:
        if not KnowledgeBaseConfig.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD not set")
        if not KnowledgeBaseConfig.PINECONE_API_KEY:
            errors.append("PINECONE_API_KEY not set")

    # Check paths
    if not ReportConfig.DEFAULT_OUTPUT_DIR.exists():
        ReportConfig.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    return errors

def print_config():
    """Print current configuration (useful for debugging)."""
    print("CompliCheck v2.0 Configuration")
    print("=" * 60)
    print(f"\nPipeline:")
    print(f"  Enrichment: {PipelineConfig.ENABLE_ENRICHMENT}")
    print(f"  Output Dir: {PipelineConfig.DEFAULT_OUTPUT_DIR}")

    print(f"\nEnrichment:")
    print(f"  Model: {EnrichmentConfig.MODEL}")
    print(f"  Operations: {EnrichmentConfig.DEFAULT_OPERATIONS}")
    print(f"  Max Cost: ${EnrichmentConfig.MAX_COST_PER_DOCUMENT}")

    print(f"\nKnowledge Base:")
    print(f"  Neo4j: {KnowledgeBaseConfig.NEO4J_URI}")
    print(f"  Pinecone: {KnowledgeBaseConfig.PINECONE_INDEX}")
    print(f"  Top K: {KnowledgeBaseConfig.DEFAULT_TOP_K}")

    print(f"\nReport:")
    print(f"  Version: {ReportConfig.PRODUCT_NAME} {ReportConfig.VERSION}")
    print(f"  Quality Score: {ReportConfig.SHOW_DATA_QUALITY_SCORE}")

    print("=" * 60)

if __name__ == "__main__":
    # Validate and print config when run directly
    errors = validate_config()
    if errors:
        print("Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Configuration valid")

    print("\n")
    print_config()

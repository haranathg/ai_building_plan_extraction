# CompliCheck v2.0 - Quick Start Guide

## Overview

CompliCheck v2.0 now includes an **LLM enrichment layer** that uses AI to enhance compliance checking with:
- Automatic plan type detection (site plan, floor plan, elevation, etc.)
- Component categorization by compliance domain
- Data quality scoring and confidence levels
- Human-readable labels with compliance context

---

## Installation

### 1. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r scripts/requirements.txt
```

Required packages:
- `anthropic>=0.40.0` (for Claude)
- `openai>=1.0.0` (for GPT)
- `python-dotenv` (for environment variables)
- `neo4j`, `pinecone-client`, `reportlab`, etc.

---

## Configuration

### Set Up API Keys

Create a `.env` file in the project root:

```bash
# For OpenAI (recommended)
OPENAI_API_KEY=sk-...

# OR for Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# Neo4j (required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Pinecone (required)
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=building-codes
```

**Note:** The system automatically detects which LLM provider to use based on available API keys. OpenAI is checked first.

---

## Usage

### Basic Usage (With Enrichment)

```bash
python compliCheckV2.py \
  --pdf "path/to/your/plan.pdf" \
  --output-dir "reports/my_project" \
  --plan-name "My Project Site Plan"
```

This will:
1. Extract components from the PDF
2. **Enrich with LLM analysis** (automatically uses available API key)
3. Check compliance against 891 building code rules
4. Generate a branded PDF report with quality indicators

### Without Enrichment (Faster, No LLM Cost)

```bash
python compliCheckV2.py \
  --pdf "path/to/your/plan.pdf" \
  --skip-enrichment
```

### Custom Enrichment Operations

```bash
python compliCheckV2.py \
  --pdf "plan.pdf" \
  --enrichment-ops metadata categorization labels
```

Available operations:
- `metadata` - Infer drawing type and compliance categories
- `categorization` - Group components by domain
- `labels` - Generate human-readable descriptions
- `reconciliation` - Check data quality
- `all` - All operations (default)

### Keep Intermediate Files

```bash
python compliCheckV2.py \
  --pdf "plan.pdf" \
  --keep-intermediates
```

This preserves:
- `{name}_components.json` - Raw extraction
- `{name}_enriched.json` - With LLM enrichment
- `{name}_compliance.json` - Compliance results

---

## Output Structure

```
reports/
└── my_project/
    ├── Plan-Name_components.json      # Raw extraction
    ├── Plan-Name_enriched.json        # + LLM enrichment
    ├── Plan-Name_compliance.json      # Compliance results
    └── Plan-Name_CompliCheck_Report.pdf  # Final report
```

---

## Understanding the Enriched Data

### Sheet Metadata
Automatically detected by LLM:
```json
{
  "drawing_type": "site_plan",        // Detected type
  "confidence": 0.85,                  // Detection confidence
  "compliance_categories": ["fire_safety"],  // Relevant categories
  "review_priority": "medium"          // Suggested priority
}
```

### Component Categorization
Groups components by compliance domain:
```json
{
  "by_compliance_domain": {
    "zoning": {"count": 0},
    "building_code": {"count": 2},
    "fire_safety": {"count": 1}
  },
  "critical_components": ["fire_safety"]
}
```

### Quality Score
Overall data quality assessment:
```json
{
  "quality_score": 0.70,               // 0.0 to 1.0
  "confidence_level": "medium",        // low/medium/high
  "missing_data": ["room dimensions"]  // What's missing
}
```

---

## How Enrichment Improves Results

### 1. Plan Type Detection
**Without Enrichment:**
- Uses heuristic rules (e.g., "if rooms > 3, probably floor plan")
- Can misclassify site plans with room labels
- May check irrelevant building-specific rules

**With Enrichment:**
- LLM analyzes drawing content and determines actual type
- Confidence score indicates reliability
- KB matcher filters out irrelevant rules automatically

**Example:**
```
Without: Checked 891 rules, many false positives
With: Filtered 21 building-specific rules for site plan
```

### 2. Component Prioritization
**Without Enrichment:**
- All components treated equally
- Reviewer must manually identify critical items

**With Enrichment:**
- Critical components flagged (e.g., fire safety)
- Suggested review priority for each sheet
- Missing components highlighted

### 3. Data Quality Awareness
**Without Enrichment:**
- No visibility into extraction quality
- User must manually verify all findings

**With Enrichment:**
- Quality score in report (0.70/1.0)
- Automatic warning if score < 0.7
- Missing data clearly identified

---

## Report Enhancements

### Executive Summary (With Enrichment)
- ✅ **Data Quality Score:** 0.70/1.0 (medium confidence)
- ⚠️ **Low Quality Alert:** Shown if score < 0.7
- **Missing Data:** Listed for manual verification

### Compliance Results
- Filtered evaluations based on plan type
- Deduplication removes repeated rule checks
- Critical components highlighted

---

## Performance

| Configuration | Time | Cost | Quality Score |
|--------------|------|------|---------------|
| No Enrichment | 110.7s | $0.00 | N/A |
| OpenAI (gpt-4o-mini) | 95.2s | ~$0.02 | 0.70 |
| Anthropic (Claude) | ~90s | ~$0.05 | N/A |

**Benefit:** Enrichment is often faster due to better rule filtering!

---

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
1. Check `.env` file exists in project root
2. Verify key format: `ANTHROPIC_API_KEY=sk-ant-...`
3. Restart terminal/reload environment

### "Your credit balance is too low"
**Solution:** Switch to OpenAI
```bash
# In .env file
OPENAI_API_KEY=sk-...
```

The system will automatically use OpenAI instead.

### "No module named 'anthropic'" or "'openai'"
```bash
.venv/bin/pip install anthropic openai
```

### Low Quality Score (< 0.7)
**Causes:**
- Poor PDF quality or scan
- Missing annotations
- Incomplete drawings

**Solutions:**
- Manually review all findings
- Request clearer drawings from architect
- Use `--skip-enrichment` if score consistently low

### Enrichment Takes Too Long
```bash
# Skip enrichment for faster processing
python compliCheckV2.py --pdf "plan.pdf" --skip-enrichment

# Or use only specific operations
python compliCheckV2.py --pdf "plan.pdf" --enrichment-ops metadata
```

---

## CLI Arguments Reference

### Required
- `--pdf PATH` - Input PDF file path

### Optional
- `--output-dir DIR` - Output directory (default: `reports/`)
- `--plan-name NAME` - Project name for report
- `--enable-enrichment` - Enable LLM enrichment (default: auto-detect)
- `--skip-enrichment` - Disable enrichment layer
- `--enrichment-ops OPS` - Specific operations (default: `all`)
- `--keep-intermediates` - Preserve JSON files
- `--provider PROVIDER` - Force provider: `openai` or `anthropic`

### Examples

```bash
# Minimal (auto-enrichment if API key found)
python compliCheckV2.py --pdf "plan.pdf"

# Full control
python compliCheckV2.py \
  --pdf "site_plan.pdf" \
  --output-dir "reports/project_x" \
  --plan-name "Project X Site Plan" \
  --enable-enrichment \
  --provider openai \
  --keep-intermediates

# Fast mode (no enrichment)
python compliCheckV2.py --pdf "plan.pdf" --skip-enrichment

# Metadata only
python compliCheckV2.py --pdf "plan.pdf" --enrichment-ops metadata
```

---

## Cost Management

### OpenAI Pricing (gpt-4o-mini)
- Input: $0.150 / 1M tokens
- Output: $0.600 / 1M tokens
- **Typical site plan:** ~$0.02 per document

### Anthropic Pricing (Claude Sonnet)
- Input: $3.00 / 1M tokens
- Output: $15.00 / 1M tokens
- **Typical site plan:** ~$0.05 per document

### Cost Control
Edit `config.py`:
```python
class EnrichmentConfig:
    MAX_COST_PER_DOCUMENT = 0.50  # Stop if cost exceeds
    MAX_REQUESTS_PER_MINUTE = 50   # Rate limiting
```

---

## What's New in v2.0

✅ **LLM Enrichment Layer**
- Automatic plan type detection
- Component categorization
- Data quality scoring

✅ **Dual Provider Support**
- OpenAI GPT-4o-mini (recommended)
- Anthropic Claude Sonnet
- Auto-detection and fallback

✅ **Enhanced KB Matcher**
- Uses enriched metadata for filtering
- Identifies critical components
- Quality-based warnings

✅ **Improved Reports**
- Data quality indicators
- Confidence levels
- Missing data alerts

✅ **Master Pipeline Script**
- Single command execution
- Colored terminal output
- Automatic fallback handling

✅ **Configuration System**
- Centralized settings in `config.py`
- Cost limits and rate limiting
- Environment-based configuration

---

## Support

### Documentation
- **INTEGRATION_GUIDE.md** - Complete technical reference (85+ sections)
- **SETUP_ENRICHMENT.md** - API setup and troubleshooting
- **TEST_RESULTS.md** - Test verification and benchmarks

### Files Modified
- `scripts/llm_enrichment_layer.py` - Dual provider support
- `scripts/check_component_compliance.py` - Enrichment detection
- `scripts/generate_enhanced_compliance_report.py` - Quality indicators
- `compliCheckV2.py` - Master pipeline (new)
- `config.py` - Configuration system (new)

### Getting Help
1. Check error message in terminal
2. Review TEST_RESULTS.md for working examples
3. Verify `.env` file configuration
4. Check INTEGRATION_GUIDE.md troubleshooting section

---

## Migration from v1.1

### Old Pipeline (compliCheck.py)
```bash
python compliCheck.py --pdf "plan.pdf"
```
- No enrichment
- Basic plan type detection
- 891 rules always checked

### New Pipeline (compliCheckV2.py)
```bash
python compliCheckV2.py --pdf "plan.pdf"
```
- Optional LLM enrichment
- Accurate plan type detection
- Smart rule filtering
- Quality indicators

**Backward Compatible:** Use `--skip-enrichment` for v1.1 behavior

---

**Last Updated:** November 6, 2024
**Version:** CompliCheck v2.0
**Status:** Production Ready ✅

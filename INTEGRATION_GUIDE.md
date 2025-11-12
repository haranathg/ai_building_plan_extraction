# CompliCheck v2.0 - LLM Enrichment Integration Guide

## Overview

This guide documents the integration of the LLM enrichment layer into the CompliCheck compliance checking pipeline.

## Architecture

### Pipeline Flow

```
┌─────────────────┐
│   Input PDF     │
└────────┬────────┘
         │
         ▼
┌────────────────────────────────┐
│  Step 1: Extract Components    │
│  extract_compliance_components │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Step 2: LLM Enrichment        │  ◄─── NEW
│  llm_enrichment_layer          │
│  (Optional, with fallback)     │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Step 3: Check Compliance      │
│  check_component_compliance    │
│  (Enhanced with enriched data) │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Step 4: Generate Report       │
│  generate_enhanced_report      │
│  (Shows quality indicators)    │
└────────┬───────────────────────┘
         │
         ▼
┌─────────────────┐
│  PDF Report     │
└─────────────────┘
```

## Enriched Data Structure

### Top-Level Structure

```json
{
  "pdf_name": "plan.pdf",
  "summary": { ... },
  "sheets": [ ... ],
  "llm_enrichment": {
    "sheet_metadata": [...],
    "categorization": {...},
    "room_labels": [...],
    "reconciliation": {...}
  }
}
```

### Sheet Metadata

Added by `infer_metadata` operation:

```json
"sheet_metadata": [
  {
    "sheet_number": 1,
    "metadata": {
      "drawing_type": "site_plan",
      "drawing_subtype": "lot_layout",
      "confidence": 0.95,
      "primary_purpose": "Show lot boundaries and setbacks",
      "compliance_categories": ["setbacks", "lot_sizing", "environmental"],
      "review_priority": "high",
      "extraction_quality": "excellent"
    }
  }
]
```

**Usage in KB Matcher:**
```python
# Get sheet type for better rule filtering
sheet_metadata = enrichment.get("sheet_metadata", [])
if sheet_metadata:
    drawing_type = sheet_metadata[0]["metadata"]["drawing_type"]
    if drawing_type == "site_plan":
        # Filter out building-specific rules
        pass
```

### Component Categorization

Added by `categorize` operation:

```json
"categorization": {
  "by_compliance_domain": {
    "zoning": {
      "components": ["setbacks", "lot_coverage"],
      "count": 5
    },
    "building_code": {
      "components": ["rooms", "stairs", "openings"],
      "count": 23
    },
    "fire_safety": {
      "components": ["fire_safety"],
      "count": 8
    }
  },
  "critical_components": [
    "front_setback",
    "egress_door",
    "fire_exit"
  ],
  "missing_common_components": [
    "accessibility_features",
    "smoke_alarms"
  ]
}
```

**Usage in KB Matcher:**
```python
# Route components to domain-specific checks
categorization = enrichment.get("categorization", {})
domains = categorization.get("by_compliance_domain", {})

for domain, info in domains.items():
    if domain == "zoning":
        # Query zoning-specific rules
        rules = query_zoning_rules(info["components"])
    elif domain == "fire_safety":
        # Query fire safety rules
        rules = query_fire_safety_rules(info["components"])
```

### Component Labels

Added by `label` operation:

```json
"room_labels": [
  {
    "original": {"name": "BR1", "room_type": "bedroom"},
    "readable_label": "Primary Bedroom (BR1)",
    "compliance_context": "Minimum bedroom size: 70 sq ft, egress window required",
    "review_notes": "Check window dimensions meet egress requirements"
  }
]
```

**Usage in Report Generator:**
```python
# Use better room descriptions in report
room_labels = enrichment.get("room_labels", [])
for label in room_labels:
    add_room_section(
        title=label["readable_label"],
        context=label["compliance_context"]
    )
```

### Reconciliation

Added by `reconcile` operation:

```json
"reconciliation": {
  "conflicts": [
    {
      "issue": "Site plan has bedrooms listed but no building shown",
      "severity": "high",
      "resolution": "Likely false positive - filter bedrooms for site plans"
    }
  ],
  "missing_data": [
    "title_block",
    "professional_stamp",
    "north_pointer"
  ],
  "quality_score": 0.75,
  "confidence_level": "medium"
}
```

**Usage in Report Generator:**
```python
# Show quality warning if needed
reconciliation = enrichment.get("reconciliation", {})
quality_score = reconciliation.get("quality_score", 1.0)

if quality_score < 0.7:
    add_warning(
        f"Data quality: {quality_score:.2f}/1.0 - "
        "Manual review recommended"
    )
```

## Integration Points

### 1. KB Matcher (check_component_compliance.py)

**Changes Made:**

1. **Detect enriched data at start of processing:**
   ```python
   has_enrichment = "llm_enrichment" in components_data
   if has_enrichment:
       log("✨ Using LLM-enriched data for enhanced compliance checking")
   ```

2. **Use enriched sheet metadata for plan type detection:**
   ```python
   if has_enrichment:
       sheet_metadata = enrichment.get("sheet_metadata", [])
       drawing_type = sheet_metadata[0]["metadata"]["drawing_type"]
       if "site_plan" in drawing_type:
           plan_context = "site_plan"
   ```

3. **Log quality warnings:**
   ```python
   quality_score = reconciliation.get("quality_score", 1.0)
   if quality_score < 0.7:
       log(f"⚠️  Low data quality: {quality_score:.2f}")
   ```

**Benefits:**
- More accurate plan type detection
- Earlier warning of data quality issues
- Potential for domain-specific rule routing

### 2. Report Generator (generate_enhanced_compliance_report.py)

**Changes Made:**

1. **Add quality indicator to executive summary:**
   ```python
   if has_enrichment:
       quality_score = reconciliation.get("quality_score", 1.0)
       if quality_score < 0.7:
           story.append(Paragraph(
               "⚠️ Data Quality Alert: Manual review recommended",
               warning_style
           ))
   ```

2. **Use enriched labels for better descriptions** (future enhancement)

3. **Show enrichment status in report header** (future enhancement)

**Benefits:**
- Users aware of data quality
- Better context for compliance findings
- Clearer identification of issues

### 3. Master Pipeline (compliCheckV2.py)

**Features:**

1. **Automatic fallback if enrichment fails:**
   ```python
   if enable_enrichment:
       enriched, working_file = step2_enrich_components(...)
       if not enriched:
           print_warning("Enrichment failed - using unenriched data")
           working_file = components_file  # Fall back
   ```

2. **Flexible enrichment control:**
   ```bash
   # Full enrichment
   python3 compliCheckV2.py plan.pdf

   # Skip enrichment
   python3 compliCheckV2.py plan.pdf --skip-enrichment

   # Partial enrichment
   python3 compliCheckV2.py plan.pdf --enrichment-ops infer_metadata categorize
   ```

3. **Clear status reporting:**
   - Shows which steps are running
   - Indicates if enrichment succeeded/failed
   - Reports elapsed time per step

## Usage Examples

### Basic Usage (With Enrichment)

```bash
# Requires ANTHROPIC_API_KEY environment variable
export ANTHROPIC_API_KEY=sk-...

python3 compliCheckV2.py data/site-plan.pdf
```

**Output:**
```
======================================================================
         CompliCheck v2.0 - Enhanced Compliance Checking
======================================================================

[Step 1] Extracting components from PDF
  Running: Component extraction
✓ Components saved: site-plan_components.json

[Step 2] Enriching components with LLM analysis
  Running: LLM enrichment
🧠 LLM Enrichment Layer
============================================================
📋 Inferring sheet metadata...
   Sheet 1: site_plan

🏷️  Categorizing components...
   zoning: 6 components
   environmental: 2 components

✅ Enrichment complete
✓ Enriched data saved: site-plan_enriched.json
✓ Using enriched data for compliance checking

[Step 3] Checking compliance against building codes
  Running: Compliance checking
✨ Using LLM-enriched data for enhanced compliance checking
  Critical components identified: 4
Detected SITE PLAN (from enrichment) - will filter out building-specific rules
✓ Compliance results saved: site-plan_compliance.json

[Step 4] Generating PDF compliance report
  Running: Report generation
✓ Report generated: site-plan_CompliCheck_Report.pdf

======================================================================
              CompliCheck v2.0 Complete
======================================================================
  Input PDF:      site-plan.pdf
  Output Report:  reports/site-plan_CompliCheck_Report.pdf
  Enrichment:     ✓ Enabled
  Elapsed Time:   145.2 seconds

✓ Success! Open report: reports/site-plan_CompliCheck_Report.pdf
```

### Fast Mode (Without Enrichment)

```bash
# For quick checks or when API key not available
python3 compliCheckV2.py data/site-plan.pdf --skip-enrichment
```

Runs ~40% faster but with less accurate plan type detection.

### Selective Enrichment

```bash
# Run only essential operations for cost savings
python3 compliCheckV2.py data/site-plan.pdf \
    --enrichment-ops infer_metadata categorize
```

Skips expensive `label` and `reconcile` operations.

### Debugging Mode

```bash
# Keep all intermediate files
python3 compliCheckV2.py data/site-plan.pdf --keep-intermediates
```

Saves:
- `*_components.json` - Raw extraction
- `*_enriched.json` - After LLM enrichment
- `*_compliance.json` - Compliance results
- `*_CompliCheck_Report.pdf` - Final report

## Configuration

See `config.py` for all configurable settings:

### Key Settings

```python
# Enable/disable enrichment
PipelineConfig.ENABLE_ENRICHMENT = True

# Enrichment operations
EnrichmentConfig.DEFAULT_OPERATIONS = ["all"]

# Quality thresholds
EnrichmentConfig.MIN_QUALITY_SCORE = 0.5
ReportConfig.SHOW_DATA_QUALITY_SCORE = True

# Cost control
EnrichmentConfig.MAX_COST_PER_DOCUMENT = 0.50  # USD

# Caching
EnrichmentConfig.ENABLE_CACHING = True
EnrichmentConfig.CACHE_EXPIRY_DAYS = 7
```

## Performance Considerations

### Enrichment Cost

Estimated costs per document (using Claude Sonnet 4):

| Operation | Tokens (Input/Output) | Cost | Time |
|-----------|----------------------|------|------|
| infer_metadata | 500 / 200 | $0.01 | ~2s |
| categorize | 300 / 150 | $0.01 | ~1.5s |
| label (20 rooms) | 2000 / 1000 | $0.05 | ~5s |
| reconcile | 400 / 300 | $0.02 | ~2s |
| **Total (all ops)** | ~3200 / 1650 | **~$0.09** | **~10s** |

### Caching Strategy

Enrichment results are cached by default:
- Cache key: SHA256(components JSON + operations list)
- Cache location: `.cache/enrichment/`
- Expiry: 7 days
- Cache hit saves: ~10s and $0.09

### When to Skip Enrichment

Skip enrichment for:
1. **Simple site plans** - Heuristic detection works well
2. **Batch processing** - Costs add up quickly
3. **Repeated runs** - Use cached results
4. **Development/testing** - Faster iteration

## Troubleshooting

### Enrichment Fails

**Symptom:** "Enrichment failed - continuing with unenriched data"

**Causes:**
1. ANTHROPIC_API_KEY not set
2. API rate limit exceeded
3. Network issues
4. Malformed components JSON

**Solutions:**
1. Check API key: `echo $ANTHROPIC_API_KEY`
2. Wait and retry
3. Use `--skip-enrichment` flag
4. Validate components JSON structure

### Low Quality Score

**Symptom:** Report shows "⚠️ Data Quality Alert: Quality score below threshold"

**Causes:**
1. Poor PDF quality (scanned images)
2. Complex/unusual plan layout
3. Missing expected components
4. Extraction errors

**Actions:**
1. **Manual review required** - Don't trust automated findings
2. Check extraction quality in components JSON
3. Try re-scanning PDF at higher DPI
4. Consider manual data entry for critical fields

### Wrong Plan Type Detected

**Symptom:** Site plan shows building-specific rules (or vice versa)

**Causes:**
1. Mixed drawing types on same sheet
2. Ambiguous sheet content
3. Extraction errors

**Solutions:**
1. Check enriched metadata: `drawing_type` field
2. Verify `lot_info` presence in components JSON
3. Report false detection for future improvement

## API Reference

### Enrichment Operations

#### infer_metadata
- **Purpose:** Determine drawing type and compliance categories
- **Cost:** ~$0.01 per sheet
- **Time:** ~2s per sheet
- **Critical for:** Plan type detection

#### categorize
- **Purpose:** Group components by compliance domain
- **Cost:** ~$0.01 per document
- **Time:** ~1.5s
- **Critical for:** Domain-specific rule routing

#### label
- **Purpose:** Generate human-readable descriptions
- **Cost:** ~$0.05 for 20 rooms
- **Time:** ~5s
- **Optional:** Improves report readability

#### reconcile
- **Purpose:** Identify conflicts and data quality issues
- **Cost:** ~$0.02 per document
- **Time:** ~2s
- **Critical for:** Quality score and warnings

## Future Enhancements

### Planned Features

1. **Smart caching:** Cache by PDF hash, not just components
2. **Batch processing:** Process multiple PDFs in parallel
3. **Cost optimization:** Skip enrichment for simple documents
4. **Enhanced routing:** Use categorization for targeted KB queries
5. **Conflict resolution:** Auto-fix common extraction errors
6. **Custom prompts:** Allow user-defined enrichment prompts

### Integration Ideas

1. **Web UI:** Show enrichment progress in real-time
2. **API mode:** REST API for enrichment as a service
3. **Webhook support:** Notify when enrichment complete
4. **Multi-provider:** Support OpenAI, Gemini, etc.

## Support

For issues or questions:
1. Check this guide first
2. Review `config.py` for settings
3. Run with `--keep-intermediates` for debugging
4. Check intermediate JSON files for data quality

## Version History

- **v2.0** (2025-01-06): Initial integration of LLM enrichment layer
- **v1.1** (2024-11): Added branded reports and site plan detection
- **v1.0** (2024-10): Initial release with basic compliance checking

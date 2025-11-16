# Pipeline Integration Guide

## Overview

This LLM enrichment layer plugs into your existing compliance workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR EXISTING PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: extract_compliance_components.py                       │
│          ↓                                                       │
│  Step 2: llm_enrichment_layer.py ← NEW MODULE                  │
│          ↓                                                       │
│  Step 3: compliance_kb_matcher.py (your existing KB lookup)     │
│          ↓                                                       │
│  Step 4: pdf_report_generator.py (your existing report gen)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Integration Options

### Option 1: CLI Pipeline (Easiest)

Run each step sequentially from the command line:

```bash
# Step 1: Extract components (your existing script)
python3 extract_compliance_components.py \
    --pdf building_plan.pdf \
    --output components.json

# Step 2: LLM enrichment (new module)
python3 llm_enrichment_layer.py \
    --input components.json \
    --output enriched_components.json

# Step 3: Match against KB (your existing script)
python3 compliance_kb_matcher.py \
    --input enriched_components.json \
    --kb-path compliance_rules.db \
    --output matched_rules.json

# Step 4: Generate PDF report (your existing script)
python3 pdf_report_generator.py \
    --input matched_rules.json \
    --output final_report.pdf
```

### Option 2: Python Integration (Recommended)

Create a master pipeline script:

```python
# master_pipeline.py
from pathlib import Path
from extract_compliance_components import extract_compliance_components
from llm_enrichment_layer import LLMEnrichmentEngine
# Import your existing modules
# from compliance_kb_matcher import match_compliance_rules
# from pdf_report_generator import generate_report

def run_complete_pipeline(pdf_path: Path, api_key: str):
    """Run the complete compliance checking pipeline."""
    
    # Step 1: Extract components
    print("📄 Step 1: Extracting components...")
    components = extract_compliance_components(pdf_path)
    
    # Step 2: LLM enrichment
    print("\n🧠 Step 2: LLM enrichment...")
    engine = LLMEnrichmentEngine(api_key)
    enriched = engine.enrich_components(components)
    
    # Step 3: Match against KB (your code)
    print("\n📚 Step 3: Matching compliance rules...")
    # matched = match_compliance_rules(enriched, kb_path="rules.db")
    
    # Step 4: Generate report (your code)
    print("\n📄 Step 4: Generating PDF report...")
    # report_path = generate_report(matched, output_path)
    
    return enriched

# Usage
if __name__ == "__main__":
    import os
    pdf = Path("building_plan.pdf")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    run_complete_pipeline(pdf, api_key)
```

### Option 3: Conditional Enrichment

Only run LLM enrichment when needed:

```python
from llm_enrichment_layer import LLMEnrichmentEngine

def smart_pipeline(pdf_path, use_llm=True):
    # Always extract
    components = extract_compliance_components(pdf_path)
    
    # Conditionally enrich
    if use_llm:
        engine = LLMEnrichmentEngine(api_key)
        # Only run specific operations you need
        components = engine.enrich_components(
            components, 
            operations=["infer_metadata", "categorize"]  # Skip expensive ops
        )
    
    # Continue with KB matching
    # ...
```

## What the LLM Layer Adds

The enrichment layer adds an `llm_enrichment` section to your JSON:

```json
{
  "pdf_name": "building_plan.pdf",
  "summary": { ... },
  "sheets": [ ... ],
  
  "llm_enrichment": {
    "sheet_metadata": [
      {
        "sheet_number": 1,
        "metadata": {
          "drawing_type": "floor_plan",
          "drawing_subtype": "first_floor",
          "confidence": 0.95,
          "primary_purpose": "Residential first floor layout",
          "compliance_categories": ["room_sizing", "egress", "accessibility"],
          "review_priority": "high",
          "extraction_quality": "excellent"
        }
      }
    ],
    
    "categorization": {
      "by_compliance_domain": {
        "zoning": {"components": ["setbacks", "lot_coverage"], "count": 5},
        "building_code": {"components": ["rooms", "stairs"], "count": 23},
        "fire_safety": {"components": ["fire_safety"], "count": 8}
      },
      "critical_components": ["egress_stairs", "fire_exits"],
      "missing_common_components": ["accessibility_ramps"]
    },
    
    "room_labels": [
      {
        "readable_label": "Master Bedroom Suite",
        "compliance_context": "Primary sleeping area - IRC minimum size requirements apply",
        "review_notes": "Check for egress window, minimum 70 sq ft"
      }
    ],
    
    "reconciliation": {
      "conflicts": [],
      "missing_data": ["accessibility_features"],
      "quality_score": 0.85,
      "confidence_level": "high"
    }
  }
}
```

## How to Use Enriched Data in Your KB Matcher

The enriched data helps route components to the right compliance checks:

```python
# In your compliance_kb_matcher.py

def match_compliance_rules(enriched_components, kb_path):
    """Enhanced KB matching using LLM metadata."""
    
    # Get LLM categorization to route checks efficiently
    categorization = enriched_components.get("llm_enrichment", {}).get("categorization", {})
    
    if categorization:
        # Route to specific compliance domains
        for domain, info in categorization["by_compliance_domain"].items():
            if domain == "zoning":
                # Run zoning checks on specified components
                run_zoning_checks(enriched_components, kb_path)
            elif domain == "fire_safety":
                # Run fire safety checks
                run_fire_safety_checks(enriched_components, kb_path)
            # etc.
    
    # Use sheet metadata for targeted checks
    for sheet_meta in enriched_components.get("llm_enrichment", {}).get("sheet_metadata", []):
        sheet_num = sheet_meta["sheet_number"]
        metadata = sheet_meta["metadata"]
        
        if metadata.get("drawing_type") == "floor_plan":
            # This is a floor plan - check room sizes, egress, etc.
            check_floor_plan_compliance(sheet_num, kb_path)
        
        elif metadata.get("drawing_type") == "site_plan":
            # This is a site plan - check setbacks, lot coverage, etc.
            check_site_plan_compliance(sheet_num, kb_path)
    
    return matched_rules
```

## How to Use Enriched Data in Your Report Generator

The enrichment adds human-readable context for better reports:

```python
# In your pdf_report_generator.py

def generate_report(matched_rules, enriched_components, output_path):
    """Generate PDF report with enhanced context."""
    
    # Use reconciliation data for report quality indicators
    reconciliation = enriched_components.get("llm_enrichment", {}).get("reconciliation", {})
    quality_score = reconciliation.get("quality_score", 0.0)
    
    # Add quality notice to report
    if quality_score < 0.7:
        add_report_warning("Data quality is lower than ideal - manual review recommended")
    
    # Use room labels for better descriptions
    room_labels = enriched_components.get("llm_enrichment", {}).get("room_labels", [])
    for label in room_labels:
        # Add friendly labels to report instead of "bedroom_1", "bedroom_2"
        add_room_section(label["readable_label"], label["compliance_context"])
    
    # Highlight critical components
    critical = enriched_components.get("llm_enrichment", {}).get("categorization", {}).get("critical_components", [])
    if critical:
        add_priority_section("Critical Items Requiring Review", critical)
    
    # Use review priority to order report sections
    # High priority items first, etc.
```

## Performance Considerations

### Token Usage
- Sheet metadata inference: ~500 tokens per sheet
- Categorization: ~300 tokens once per document
- Component labeling: ~100 tokens per component
- Reconciliation: ~200 tokens once per document

**Typical document (5 sheets, 20 rooms):** ~5,000 tokens = $0.03 with Claude Sonnet

### Speed
- LLM calls: 1-2 seconds each
- Typical document: 5-10 seconds total for enrichment
- Parallel processing possible for multi-document batches

### Cost Optimization

```python
# Run only what you need
engine.enrich_components(
    components,
    operations=["infer_metadata"]  # Skip expensive labeling
)

# Or skip enrichment for simple plans
if components["summary"]["total_sheets"] <= 2:
    # Small document, skip LLM enrichment
    pass
else:
    # Complex document, use enrichment
    enriched = engine.enrich_components(components)
```

## Testing the Integration

```python
# test_integration.py
from pathlib import Path
import json

def test_pipeline_integration():
    """Test that enrichment layer integrates cleanly."""
    
    # Load sample output from your extractor
    with open("test_data/sample_components.json") as f:
        components = json.load(f)
    
    # Run enrichment
    engine = LLMEnrichmentEngine(api_key="test-key")
    enriched = engine.enrich_components(components)
    
    # Verify structure
    assert "llm_enrichment" in enriched
    assert "sheet_metadata" in enriched["llm_enrichment"]
    
    # Verify original data preserved
    assert enriched["summary"] == components["summary"]
    assert len(enriched["sheets"]) == len(components["sheets"])
    
    print("✅ Integration test passed")

if __name__ == "__main__":
    test_pipeline_integration()
```

## Troubleshooting

### Issue: API rate limits
**Solution**: Add retry logic or batch processing delays

```python
import time

for sheet in sheets:
    metadata = engine.infer_sheet_metadata(sheet)
    time.sleep(0.5)  # Rate limit protection
```

### Issue: LLM enrichment too slow
**Solution**: Run only essential operations

```python
# Fast mode - metadata only
enriched = engine.enrich_components(
    components, 
    operations=["infer_metadata", "categorize"]
)
```

### Issue: Enrichment fails but pipeline should continue
**Solution**: Add fallback logic

```python
try:
    enriched = engine.enrich_components(components)
except Exception as e:
    print(f"Warning: LLM enrichment failed: {e}")
    enriched = components  # Continue with unenriched data
```

## Next Steps

1. ✅ Copy these files to your project
2. ✅ Test enrichment layer standalone
3. ✅ Integrate into your KB matcher
4. ✅ Update report generator to use enriched context
5. ✅ Run full pipeline test

## Questions for Claude Code

When asking Claude Code to integrate this, provide:

```
I have an LLM enrichment layer (llm_enrichment_layer.py) that needs to be 
integrated into my existing compliance checking pipeline. 

Current pipeline:
1. extract_compliance_components.py → components.json
2. [NEW] llm_enrichment_layer.py → enriched_components.json  
3. compliance_kb_matcher.py → matched_rules.json
4. pdf_report_generator.py → final_report.pdf

Please:
1. Review my existing KB matcher and report generator code
2. Update them to use the enriched data from llm_enrichment_layer
3. Create a master pipeline script that chains all steps
4. Add error handling if LLM enrichment fails

The enriched JSON adds an "llm_enrichment" section with:
- sheet_metadata: Drawing type inference and review priority
- categorization: Components grouped by compliance domain  
- room_labels: Human-readable labels and compliance context
- reconciliation: Data quality score and conflict detection
```

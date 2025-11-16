# PROMPT FOR CLAUDE CODE

Copy and paste this prompt into Claude Code after uploading your KB matcher and report generator:

---

## Integration Request

I have an LLM enrichment layer ready to integrate into my compliance checking pipeline. I need your help connecting all the pieces.

### Current Pipeline
```
PDF → extract_compliance_components.py → components.json
    → compliance_kb_matcher.py → matched_rules.json
    → pdf_report_generator.py → final_report.pdf
```

### New Pipeline (with LLM enrichment)
```
PDF → extract_compliance_components.py → components.json
    → llm_enrichment_layer.py → enriched_components.json [NEW]
    → compliance_kb_matcher.py [UPDATE NEEDED]
    → pdf_report_generator.py [UPDATE NEEDED]
    → final_report.pdf
```

### Files I've Uploaded
1. `extract_compliance_components.py` - Original extraction (already working)
2. `llm_enrichment_layer.py` - New enrichment module (ready to integrate)
3. `compliance_kb_matcher.py` - My existing KB matcher (needs updates)
4. `pdf_report_generator.py` - My existing report generator (needs updates)
5. `INTEGRATION_GUIDE.md` - Reference documentation

### What I Need You To Do

#### Task 1: Update KB Matcher
Update `compliance_kb_matcher.py` to leverage the enriched data:

**Use these new fields:**
- `enriched["llm_enrichment"]["categorization"]["by_compliance_domain"]` - Route components to correct KB queries
- `enriched["llm_enrichment"]["sheet_metadata"]` - Use drawing_type to filter applicable rules
- `enriched["llm_enrichment"]["categorization"]["critical_components"]` - Prioritize these checks

**Example integration:**
```python
# In your KB matcher
categorization = enriched_data.get("llm_enrichment", {}).get("categorization", {})

for domain, info in categorization.get("by_compliance_domain", {}).items():
    if domain == "zoning":
        # Run zoning-specific KB queries
        check_zoning_compliance(info["components"], kb_connection)
    elif domain == "fire_safety":
        # Run fire safety KB queries
        check_fire_safety(info["components"], kb_connection)
```

#### Task 2: Update Report Generator  
Update `pdf_report_generator.py` to use enriched context:

**Use these new fields:**
- `enriched["llm_enrichment"]["room_labels"]` - Better room descriptions
- `enriched["llm_enrichment"]["reconciliation"]["quality_score"]` - Add quality indicator
- `enriched["llm_enrichment"]["reconciliation"]["missing_data"]` - Flag missing components
- `enriched["llm_enrichment"]["sheet_metadata"][x]["metadata"]["review_priority"]` - Order report sections

**Example integration:**
```python
# In your report generator
quality = enriched_data.get("llm_enrichment", {}).get("reconciliation", {}).get("quality_score", 0)
if quality < 0.7:
    add_report_warning("Data quality below threshold - manual review recommended")

room_labels = enriched_data.get("llm_enrichment", {}).get("room_labels", [])
for label in room_labels:
    add_room_section(
        title=label["readable_label"],
        context=label["compliance_context"]
    )
```

#### Task 3: Create Master Pipeline
Create `master_pipeline.py` that chains all steps:

**Requirements:**
- Run extraction → enrichment → KB matching → report generation
- Handle enrichment failures gracefully (continue with unenriched data)
- Log progress at each step
- Accept command-line arguments for PDF path, API key, KB path
- Save intermediate JSONs for debugging

**Structure:**
```python
def run_pipeline(pdf_path, api_key, kb_path, output_dir):
    # Step 1: Extract
    components = extract_compliance_components(pdf_path)
    
    # Step 2: Enrich (with error handling)
    try:
        enriched = enrich_components(components, api_key)
    except Exception as e:
        print(f"Warning: Enrichment failed: {e}")
        enriched = components
    
    # Step 3: Match KB rules
    matched = match_compliance_rules(enriched, kb_path)
    
    # Step 4: Generate report
    report_path = generate_pdf_report(matched, output_dir)
    
    return report_path
```

#### Task 4: Add Configuration
Create `config.py` for pipeline settings:

**Include:**
- Enrichment operations to run (allow disabling expensive ops)
- KB connection settings
- Report formatting options
- API rate limiting
- Error handling behavior

### Constraints & Notes

1. **Preserve existing functionality** - The pipeline should work with or without enrichment
2. **Backward compatible** - If enrichment layer not available, continue with original data
3. **Error handling** - Don't fail entire pipeline if enrichment fails
4. **Performance** - Allow skipping enrichment for simple documents
5. **Logging** - Clear progress indicators at each step

### Testing

Please create `test_integration.py` that:
1. Loads a sample components.json
2. Runs enrichment
3. Verifies structure is correct
4. Tests KB matcher with enriched data
5. Tests report generator with enriched data

### Questions to Address

1. How should I handle API rate limits in batch processing?
2. Should I cache enrichment results for repeated runs?
3. What's the best way to configure which enrichment operations to run?
4. How can I validate that enriched data is being used correctly?

### Reference

See `INTEGRATION_GUIDE.md` for:
- Detailed examples of using enriched data
- Performance optimization tips
- Troubleshooting guide
- Full enriched JSON structure

---

Please review all uploaded files and create the integrated pipeline. Let me know if you need any clarification on my existing code structure.

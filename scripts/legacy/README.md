# Legacy Scripts

This folder contains **deprecated scripts** that are kept for reference only.

## Why These Scripts Are Deprecated

The original scripts used a **text-based extraction approach** that was less accurate for compliance checking:

- **extract_vector_plan.py** - Extracted raw text and geometry without semantic understanding of building components
- **check_plan_compliance_neo4j.py** - Performed text-matching against rules without component-specific intelligence
- **generate_compliance_report.py** - Generated basic reports without detailed analysis

## Current Recommended Scripts

Use these **component-based scripts** instead (located in `scripts/` root):

| Current Script | Purpose |
|----------------|---------|
| `extract_compliance_components.py` | Extracts compliance-ready components with geometric analysis |
| `check_component_compliance.py` | Component-aware compliance checking with hybrid Pinecone + Neo4j matching |
| `generate_enhanced_compliance_report.py` | Professional PDF reports with executive summary and recommendations |

## Key Improvements in Current Scripts

1. **Component-Based Extraction**
   - Identifies rooms, setbacks, openings, parking, etc. as structured components
   - Calculates geometric setbacks even when not annotated
   - Provides room areas, dimensions, and classifications

2. **Intelligent Compliance Checking**
   - Component-specific evaluation logic (e.g., area checks for rooms, distance checks for setbacks)
   - Hybrid rule matching using Pinecone (semantic similarity) + Neo4j (keywords + relationships)
   - Confidence scoring for each evaluation

3. **Enhanced Reporting**
   - Executive summary with pass/fail statistics
   - Detailed findings grouped by component type
   - Color-coded status (PASS=green, FAIL=red, REVIEW=yellow)
   - Actionable recommendations

## Migration Notes

If you have existing workflows using legacy scripts:

**Old workflow:**
```bash
python scripts/legacy/extract_vector_plan.py --pdf data/plan.pdf
python scripts/legacy/check_plan_compliance_neo4j.py --plan data/plan_output.json
python scripts/legacy/generate_compliance_report.py --plan data/plan_output.json --compliance data/plan_compliance.json
```

**New workflow:**
```bash
python scripts/extract_compliance_components.py --pdf data/plan.pdf
python scripts/check_component_compliance.py --components data/plan_components.json
python scripts/generate_enhanced_compliance_report.py --components data/plan_components.json --compliance data/plan_compliance.json
```

## Support

For questions about migrating from legacy scripts, refer to:
- [../README.md](../../README.md) - Main documentation
- [../COMPONENT_EXTRACTION_GUIDE.md](../../COMPONENT_EXTRACTION_GUIDE.md) - Component specifications

---

**Last Updated:** October 31, 2025

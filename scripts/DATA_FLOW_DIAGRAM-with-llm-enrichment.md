# Data Flow Diagram

## Complete Pipeline Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ARCHITECTURAL PDF                               │
│                     (Floor plans, site plans, etc.)                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 1: extract_compliance_components.py                    │
│                    (PyMuPDF, pdfplumber, Shapely)                       │
├─────────────────────────────────────────────────────────────────────────┤
│ Extracts:                                                                │
│  • Geometric shapes (rectangles, lines, circles)                        │
│  • Text blocks with coordinates                                         │
│  • Dimensions and measurements                                          │
│  • Layer information                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ Identifies:                                                             │
│  • Rooms (name, type, area, dimensions)                                │
│  • Setbacks (direction, distance, location)                            │
│  • Openings (doors, windows, egress)                                   │
│  • Parking spaces                                                      │
│  • Stairs & circulation                                                │
│  • Fire safety features                                                │
│  • Accessibility features                                              │
│  • MEP elements                                                        │
│  • Structural elements                                                 │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
                        components.json
                                 │
    {                            │
      "pdf_name": "...",         │
      "summary": {               │
        "total_sheets": 5,       │
        "total_rooms": 12,       │
        "total_setbacks": 4      │
      },                         │
      "sheets": [                │
        {                        │
          "sheet_number": 1,     │
          "rooms": [...],        │
          "setbacks": [...],     │
          "openings": [...],     │
          ...                    │
        }                        │
      ]                          │
    }                            │
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 2: llm_enrichment_layer.py [NEW]                      │
│                      (Claude AI via API)                                │
├─────────────────────────────────────────────────────────────────────────┤
│ Operation 1: INFER SHEET METADATA                                       │
│  • Analyzes extracted components per sheet                             │
│  • Determines: floor_plan, site_plan, elevation, etc.                 │
│  • Assigns confidence score (0.0-1.0)                                  │
│  • Identifies applicable compliance categories                         │
│  • Sets review priority (high/medium/low)                              │
│                                                                         │
│ Operation 2: CATEGORIZE COMPONENTS                                      │
│  • Groups components by compliance domain                              │
│    - Zoning (setbacks, lot coverage)                                  │
│    - Building code (rooms, stairs, openings)                          │
│    - Fire safety (alarms, sprinklers, exits)                         │
│    - Accessibility (ADA features)                                      │
│  • Identifies critical components needing priority review              │
│  • Flags missing common components                                     │
│                                                                         │
│ Operation 3: GENERATE LABELS                                            │
│  • Creates human-readable labels                                       │
│  • Adds compliance context for each component                          │
│  • Provides review notes                                               │
│                                                                         │
│ Operation 4: RECONCILE CONFLICTS                                        │
│  • Identifies data inconsistencies                                     │
│  • Flags missing expected data                                         │
│  • Calculates overall data quality score                               │
│  • Determines confidence level                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
                      enriched_components.json
                                 │
    {                            │
      "pdf_name": "...",         │
      "summary": {...},          │ ← Original data preserved
      "sheets": [...],           │
                                 │
      "llm_enrichment": {        │ ← NEW: AI-generated metadata
        "sheet_metadata": [      │
          {                      │
            "sheet_number": 1,   │
            "metadata": {        │
              "drawing_type": "floor_plan",
              "drawing_subtype": "first_floor",
              "confidence": 0.95,│
              "primary_purpose": "Residential layout",
              "compliance_categories": ["room_sizing", "egress"],
              "review_priority": "high",
              "extraction_quality": "excellent"
            }                    │
          }                      │
        ],                       │
        "categorization": {      │
          "by_compliance_domain": {
            "zoning": {...},     │
            "building_code": {...},
            "fire_safety": {...} │
          },                     │
          "critical_components": [...],
          "missing_common_components": [...]
        },                       │
        "room_labels": [         │
          {                      │
            "readable_label": "Master Bedroom Suite",
            "compliance_context": "Primary sleeping area...",
            "review_notes": "Check egress window..."
          }                      │
        ],                       │
        "reconciliation": {      │
          "conflicts": [],       │
          "missing_data": [...], │
          "quality_score": 0.85, │
          "confidence_level": "high"
        }                        │
      }                          │
    }                            │
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│            STEP 3: compliance_kb_matcher.py [YOUR EXISTING CODE]        │
│              (Query knowledge base for compliance rules)                │
├─────────────────────────────────────────────────────────────────────────┤
│ ENHANCED WITH ENRICHMENT:                                               │
│                                                                         │
│ Uses: categorization["by_compliance_domain"]                           │
│  → Routes components to correct KB queries                             │
│  → Instead of checking ALL rules against ALL components,               │
│    only check zoning rules against zoning components, etc.             │
│                                                                         │
│ Uses: sheet_metadata[x]["metadata"]["drawing_type"]                    │
│  → Applies drawing-specific rules                                      │
│  → Floor plans: room sizing, egress, accessibility                     │
│  → Site plans: setbacks, lot coverage, parking                         │
│                                                                         │
│ Uses: categorization["critical_components"]                            │
│  → Prioritizes checking these components first                         │
│  → Flags them in results as high-priority                              │
│                                                                         │
│ Uses: reconciliation["quality_score"]                                  │
│  → If < 0.7, adds warning about data quality                           │
│  → May require manual verification                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ Example KB Query Enhancement:                                          │
│                                                                         │
│  OLD: SELECT * FROM rules WHERE component_type = 'room'                │
│       → Returns 500 rules, checks all against all rooms                │
│                                                                         │
│  NEW: For floor_plan sheet with bedrooms in "building_code" domain:   │
│       SELECT * FROM rules                                               │
│       WHERE component_type = 'room'                                     │
│       AND drawing_type = 'floor_plan'                                   │
│       AND compliance_domain = 'building_code'                           │
│       AND room_type = 'bedroom'                                         │
│       → Returns 25 relevant rules, faster and more accurate            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
                          matched_rules.json
                                 │
    {                            │
      "pdf_name": "...",         │
      "enriched_data": {...},    │ ← Includes all enrichment
      "matched_rules": [         │
        {                        │
          "component_id": "room_1",
          "component_type": "bedroom",
          "rules_checked": [     │
            {                    │
              "rule_id": "IRC_R304.1",
              "description": "Minimum room size 70 sq ft",
              "status": "compliant",
              "component_value": "120 sq ft",
              "requirement": "70 sq ft"
            }                    │
          ],                     │
          "priority": "high",    │ ← From enrichment
          "readable_label": "Master Bedroom" ← From enrichment
        }                        │
      ],                         │
      "compliance_summary": {    │
        "total_rules_checked": 127,
        "compliant": 118,        │
        "non_compliant": 3,      │
        "needs_review": 6        │
      },                         │
      "data_quality": 0.85       │ ← From enrichment
    }                            │
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│          STEP 4: pdf_report_generator.py [YOUR EXISTING CODE]          │
│                    (Generate professional PDF report)                   │
├─────────────────────────────────────────────────────────────────────────┤
│ ENHANCED WITH ENRICHMENT:                                               │
│                                                                         │
│ Uses: room_labels[x]["readable_label"]                                 │
│  → Report shows "Master Bedroom Suite" not "bedroom_1"                 │
│                                                                         │
│ Uses: room_labels[x]["compliance_context"]                             │
│  → Adds explanatory text: "Primary sleeping area - IRC minimum        │
│    size requirements apply"                                            │
│                                                                         │
│ Uses: reconciliation["quality_score"]                                  │
│  → Adds quality indicator to report header                             │
│  → If < 0.7, adds prominent data quality warning                       │
│                                                                         │
│ Uses: sheet_metadata[x]["review_priority"]                             │
│  → Orders report sections by priority                                  │
│  → High priority items appear first                                    │
│                                                                         │
│ Uses: categorization["missing_common_components"]                      │
│  → Adds "Missing Components" section to report                         │
│  → Flags items that should be present but weren't found                │
│                                                                         │
│ Uses: reconciliation["conflicts"]                                      │
│  → Adds "Data Quality Notes" section                                   │
│  → Lists any conflicts or inconsistencies found                        │
├─────────────────────────────────────────────────────────────────────────┤
│ Report Structure Enhancement:                                          │
│                                                                         │
│  OLD Report:                                                           │
│   - List of rooms                                                      │
│   - List of compliance checks                                          │
│   - Summary                                                            │
│                                                                         │
│  NEW Report:                                                           │
│   - Executive Summary (from enrichment context)                        │
│   - Data Quality Score: 0.85/1.0 ✓                                    │
│   - High Priority Items (sorted by review_priority)                    │
│   - Building Components by Domain (grouped by categorization)          │
│     • Zoning Compliance                                                │
│       - Setbacks: ✓ Compliant                                         │
│     • Building Code                                                    │
│       - Master Bedroom Suite: ✓ Compliant                             │
│         Context: Primary sleeping area - IRC minimums apply            │
│       - Guest Bedroom: ✓ Compliant                                    │
│   - Missing Components ⚠                                               │
│     - Accessibility ramps (expected but not found)                     │
│   - Data Quality Notes                                                 │
│     - No conflicts detected                                            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
                          final_report.pdf
                                 │
                    Professional compliance report
                    with enhanced context and clarity


## Key Data Transformations

### Transformation 1: Raw → Structured
```
PDF Lines & Text  →  components.json
"BEDROOM 12'x10'" →  {"name": "BEDROOM", "width": 12, "length": 10}
```

### Transformation 2: Structured → Enriched
```
components.json           →  enriched_components.json + llm_enrichment
{"name": "BEDROOM", ...}  →  {"readable_label": "Master Bedroom Suite",
                              "compliance_context": "Primary sleeping area",
                              "review_notes": "Check egress requirements"}
```

### Transformation 3: Enriched → Matched
```
enriched_components.json              →  matched_rules.json
{"name": "BEDROOM", "area": 120}      →  {"rule": "IRC R304.1",
+ llm_enrichment["categorization"]    →   "status": "compliant",
                                          "component_value": "120 sq ft",
                                          "requirement": "70 sq ft"}
```

### Transformation 4: Matched → Report
```
matched_rules.json                    →  final_report.pdf
{"rule": "IRC R304.1", ...}           →  ✓ Master Bedroom Suite
+ enriched["room_labels"]             →    120 sq ft (Compliant with IRC R304.1)
                                          Context: Primary sleeping area
```

## Benefits of Enrichment Layer

| Without Enrichment | With Enrichment |
|-------------------|-----------------|
| Components have generic IDs | Components have readable labels |
| All rules checked against all components | Smart routing to relevant rules |
| No context in reports | Rich compliance context |
| Can't detect missing components | Flags missing expected components |
| No data quality metrics | Quality score & confidence level |
| Report ordering arbitrary | Priority-based ordering |
| Generic "bedroom_1" labels | "Master Bedroom Suite" labels |

## Performance Impact

```
Without Enrichment:
  Extract: 3s → KB Match: 45s → Report: 2s = 50s total

With Enrichment:
  Extract: 3s → Enrich: 8s → KB Match: 15s → Report: 2s = 28s total
                    ↑             ↑
                  +8s cost    -30s savings (smarter routing)
  
  Net: 22s faster + better quality
```

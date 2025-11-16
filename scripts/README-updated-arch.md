# LLM-Enhanced PDF Compliance Parser

A sophisticated PDF parsing system that extracts architectural compliance components and enriches them with AI-powered analysis using Claude.

## 🏗️ Architecture

```
┌─────────────────┐
│   Vector PDF    │
└────────┬────────┘
         ↓
┌─────────────────────────────────────────────┐
│   🔧 Python Parser (PyMuPDF, pdfplumber)   │
│   • Extract shapes, text, coordinates       │
│   • Identify layers and drawing elements    │
│   • Parse dimensions and annotations        │
└────────┬────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│   🗂️ Structured JSON Output                │
│   • Rooms, dimensions, setbacks             │
│   • Fire safety, accessibility features     │
│   • MEP elements, structural components     │
└────────┬────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│   🧠 LLM Agent (Claude 4 Sonnet)           │
│                                             │
│   Layer 1: Section Type Inference           │
│   └─ Identify drawing types & purposes      │
│                                             │
│   Layer 2: Entity Grouping                  │
│   └─ Group related components logically     │
│                                             │
│   Layer 3: Compliance Validation            │
│   └─ Check against building codes           │
│                                             │
│   Layer 4: Human Summaries                  │
│   └─ Generate natural language reports      │
│                                             │
│   Layer 5: Metadata Reconciliation          │
│   └─ Resolve conflicts & fill gaps          │
└────────┬────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│   📦 Enriched JSON Output                   │
│   • Original structured data                │
│   • AI-inferred metadata                    │
│   • Compliance validation results           │
│   • Human-readable summaries                │
│   • Quality scores & recommendations        │
└─────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Basic Usage

```bash
# Run the enhanced parser
python3 llm_enhanced_compliance_parser.py --pdf path/to/architectural_plan.pdf

# Specify custom output location
python3 llm_enhanced_compliance_parser.py \
    --pdf plans/building_A.pdf \
    --output results/building_A_enriched.json

# Provide API key inline
python3 llm_enhanced_compliance_parser.py \
    --pdf plan.pdf \
    --api-key sk-ant-xxxxx
```

## 📊 Output Structure

The enriched JSON output contains five main sections:

### 1. Original Data
Complete structured extraction from the original parser:
```json
{
  "original_data": {
    "pdf_name": "building_plan.pdf",
    "summary": {
      "total_sheets": 5,
      "total_rooms": 12,
      "total_setbacks": 4,
      "room_types": ["bedroom", "bathroom", "kitchen", "living_room"]
    },
    "sheets": [...]
  }
}
```

### 2. Section Inferences
AI-determined drawing types and purposes:
```json
{
  "section_inferences": [
    {
      "sheet_number": 1,
      "inferred_type": "floor_plan",
      "confidence": 0.95,
      "purpose": "First floor layout with room dimensions",
      "key_features": ["bedrooms", "bathrooms", "kitchen"],
      "compliance_relevance": ["room_sizing", "egress", "accessibility"]
    }
  ]
}
```

### 3. Grouped Entities
Intelligently organized components:
```json
{
  "grouped_entities": [
    {
      "group_name": "All Bedrooms",
      "entity_type": "room",
      "entities": [...],
      "summary": "Three bedrooms ranging from 120-180 sq ft, all meeting minimum size requirements",
      "compliance_notes": [
        "All bedrooms meet IRC minimum 70 sq ft requirement",
        "Master bedroom includes ensuite bathroom"
      ]
    }
  ]
}
```

### 4. Compliance Validations
Code compliance check results:
```json
{
  "compliance_validations": [
    {
      "check_category": "setbacks",
      "status": "compliant",
      "findings": [
        "Front setback: 25 ft (required: 20 ft)",
        "Rear setback: 15 ft (required: 15 ft)"
      ],
      "requirements": ["IRC R302.1", "Local zoning ordinance"],
      "recommendations": []
    }
  ]
}
```

### 5. Human Summary
Executive summary and recommendations:
```json
{
  "human_summary": {
    "executive_summary": "Single-family residential building with 3 bedrooms, 2 bathrooms, compliant with IRC requirements",
    "project_overview": "...",
    "key_compliance_findings": [
      "All setbacks meet zoning requirements",
      "Egress windows properly sized and located"
    ],
    "areas_of_concern": [
      "Accessibility features not identified - may require ADA review"
    ],
    "recommendations": [
      "Verify fire alarm placement with local fire code",
      "Confirm accessibility requirements with jurisdiction"
    ],
    "confidence_notes": [
      "High confidence in structural data",
      "Limited MEP information available"
    ]
  }
}
```

## 🧩 LLM Enhancement Layers Explained

### Layer 1: Section Type Inference
**Purpose**: Automatically identify what each drawing sheet represents

**How it works**:
- Analyzes extracted data (rooms, elements, annotations)
- Determines drawing type (floor plan, site plan, elevation, etc.)
- Assigns confidence score and identifies key features
- Maps to relevant compliance checks

**Example**: 
- Input: Sheet with 5 rooms, stairs, dimensions
- Output: "Floor Plan - Second Story" with 0.92 confidence

### Layer 2: Entity Grouping
**Purpose**: Organize related components for better analysis

**How it works**:
- Groups similar entities (all bedrooms, all fire safety devices)
- Generates natural language summaries for each group
- Identifies compliance implications for grouped items

**Example**:
- Input: 3 bedrooms scattered across sheets
- Output: Grouped "Bedroom Suite" with size comparison and compliance notes

### Layer 3: Compliance Validation
**Purpose**: Check against building codes and regulations

**How it works**:
- Evaluates setbacks, room sizes, egress paths, accessibility
- Compares against common code requirements (IRC, IBC, ADA)
- Provides status: compliant, non-compliant, needs review, insufficient data
- Offers specific recommendations

**Example**:
- Input: Room dimensions and egress windows
- Output: "Compliant - all bedrooms meet IRC minimum size and egress requirements"

### Layer 4: Human Summaries
**Purpose**: Generate readable reports for building officials

**How it works**:
- Creates executive summary (2-3 sentences)
- Writes detailed project overview
- Highlights key findings and concerns
- Provides actionable recommendations
- Notes data quality and confidence levels

**Example Output**:
```
Executive Summary:
This is a two-story single-family residence with 2,400 sq ft of living space,
featuring 4 bedrooms and 3 bathrooms. The building generally complies with
IRC requirements, with minor accessibility considerations requiring review.
```

### Layer 5: Metadata Reconciliation
**Purpose**: Improve data quality and resolve inconsistencies

**How it works**:
- Identifies conflicts (e.g., room count discrepancies)
- Fills data gaps using context and inference
- Calculates overall data quality score (0.0 to 1.0)
- Documents resolution decisions

**Example**:
- Conflict: Title block says "3 bedrooms" but 4 bedrooms detected
- Resolution: "4 bedrooms confirmed via floor plan analysis"

## 🎯 Use Cases

### For Building Departments
- Automated initial plan review
- Consistency checking across sheets
- Code compliance pre-screening
- Identify missing documentation

### For Architects
- Quality assurance before submission
- Catch missing compliance elements
- Generate submission documentation
- Validate against requirements

### For Contractors
- Understand scope and requirements
- Identify potential compliance issues early
- Extract quantities and dimensions
- Verify specifications

## 🔧 Configuration

### Adjusting LLM Behavior

Edit the `ComplianceLLMAgent` class to customize:

```python
# Change Claude model
agent = ComplianceLLMAgent(api_key, model="claude-opus-4-20250514")

# Adjust token limits for longer responses
self.max_tokens = 8192

# Modify system prompts for specific jurisdictions
system_prompt = """You are an expert in California building codes..."""
```

### Adding Custom Compliance Checks

Extend the `validate_compliance` method:

```python
def validate_compliance(self, components: Dict[str, Any]) -> List[ComplianceValidation]:
    # Add custom validation logic
    if self._check_california_energy_code(components):
        validations.append(ComplianceValidation(...))
    
    return validations
```

## 🧪 Testing

```bash
# Test with sample PDF
python3 llm_enhanced_compliance_parser.py --pdf tests/sample_floor_plan.pdf

# Compare with original parser output
python3 extract_compliance_components.py --pdf tests/sample_floor_plan.pdf
```

## 📈 Performance

- **Parse Time**: ~2-5 seconds per page (geometric extraction)
- **LLM Enhancement**: ~3-10 seconds per sheet (5 layers × 1-2s each)
- **Total Pipeline**: ~5-15 seconds per page

**Optimization Tips**:
- Batch similar requests to Claude
- Cache section inferences for repeated analysis
- Use parallel processing for multi-sheet PDFs

## 🔐 Security & Privacy

- API keys stored in environment variables (never in code)
- No PDF data transmitted except extracted JSON structures
- Local processing for geometric extraction
- Cloud processing only for LLM enhancement

## 🛠️ Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### API key issues
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# Set temporarily
export ANTHROPIC_API_KEY="your-key"
```

### JSON parsing errors
- LLM responses sometimes include markdown formatting
- Parser automatically strips ```json``` wrappers
- Fallback logic handles parsing failures gracefully

### Low confidence scores
- Indicates ambiguous or incomplete data
- Review original PDF quality
- Check if drawing standards are unusual

## 📚 Related Documentation

- [Original Parser Documentation](extract_compliance_components.py)
- [Anthropic Claude API Docs](https://docs.anthropic.com)
- [International Building Code (IBC)](https://codes.iccsafe.org/)
- [International Residential Code (IRC)](https://codes.iccsafe.org/)

## 🤝 Contributing

Improvements welcome! Key areas:

1. **More Compliance Checks**: Add jurisdiction-specific validations
2. **Better Entity Recognition**: Improve grouping algorithms
3. **Confidence Scoring**: Enhance reliability metrics
4. **Performance**: Optimize LLM call batching
5. **Documentation**: Add more examples and use cases

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- Built on top of `extract_compliance_components.py`
- Powered by Anthropic's Claude AI
- PDF parsing via pdfplumber and Shapely

---

**Questions or Issues?** Open an issue or contact the maintainers.

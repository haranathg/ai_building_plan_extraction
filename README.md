# AI Building Plan Extraction & Compliance Pipeline

This module provides a simple end‑to‑end workflow for:

1. **Vector plan extraction** – convert architectural PDFs into structured JSON.
2. **Compliance checking** – compare the extracted plan against rules stored in Neo4j (optionally with semantic scoring via OpenAI/Pinecone).
3. **Report generation** – bundle the plan summary and compliance results into a PDF.

The sample plan included in the repo is `data/House-Floor-Plans-vector.pdf`.

---

## 1. Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Populate `.env` with your credentials (example placeholders shown):

```
USE_OPENAI=1                      # set to 0 if running fully local
OPENAI_API_KEY=sk-...

PINECONE_API_KEY=pcsk_...
PINECONE_REGION=us-east-1
PINECONE_INDEX=planning-rules

NEO4J_URI=neo4j+s://<Aura hostname>
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>

LOCAL_LLM_BASE_URL=http://127.0.0.1:1234/v1   # only used when USE_OPENAI=0
LLM_MODEL=qwen3-4b-instruct-2507              # chat model for local LM Studio
EMBEDDING_MODEL=bge-large-en-v1.5             # embedding model for local LM Studio
```

> If you prefer local inference via LM Studio, leave `USE_OPENAI=0`, start the API server, and load both the chat and embedding models listed above.

---

## 2. Enhanced Workflow (Recommended)

### Step 1: Extract Components
```bash
python scripts/extract_compliance_components.py \
    --pdf data/House-Floor-Plans-vector.pdf
```

**Output:** `data/House-Floor-Plans-vector_components.json`

Extracts:
- Rooms with dimensions & areas
- Setbacks (annotated + geometric)
- Openings (doors/windows)
- Parking spaces
- Stairs/ramps
- Fire safety features
- Accessibility features
- Heights/levels
- Building envelope

### Step 2: Check Compliance
```bash
python scripts/check_component_compliance.py \
    --components data/House-Floor-Plans-vector_components.json \
    --top-k 2
```

**Output:** `data/House-Floor-Plans-vector_compliance.json`

For each component:
- Queries Pinecone for top 2 semantically similar rules
- Queries Neo4j for keyword-matched rules
- Evaluates component attributes against rule requirements
- Generates PASS/FAIL/REVIEW status with confidence scores

### Step 3: Generate Report
```bash
python scripts/generate_enhanced_compliance_report.py \
    --components data/House-Floor-Plans-vector_components.json \
    --compliance data/House-Floor-Plans-vector_compliance.json \
    --output reports/House-Floor-Plans-enhanced_report.pdf
```

**Output:** Comprehensive PDF compliance report

Report includes:
- Executive summary with pass/fail statistics
- Component extraction overview
- Detailed findings by component type
- Recommendations and action items
- Color-coded compliance status

---

## 3. Useful Tips

- **Check connections**: the compliance script will fail fast if Neo4j/OpenAI/Pinecone credentials are missing. Use the same `.env` in each repo that shares the rule knowledge base.
- **Local LM Studio**: if running offline, keep the API server running with both models loaded (`LLM_MODEL` for chat and `EMBEDDING_MODEL` for embeddings).
- **Batch size**: Pinecone upserts are automatically chunked in batches of 50 vectors; if you change the embedding dimension or metadata volume, adjust as needed inside `loaders/pinecone_loader.py`.
- **House-Floor-Plans-vector.pdf**: serves as the sample plan; swap in new PDFs by pointing the `--pdf` flag at a different file inside `data/`.

---

## Summary of Scripts

### Current Scripts (Recommended)

| Script | Purpose |
| ------ | ------- |
| `scripts/extract_compliance_components.py` | Extracts compliance-ready components (rooms, setbacks, openings, etc.) with geometric analysis. |
| `scripts/check_component_compliance.py` | Component-based compliance checking using Pinecone + Neo4j with intelligent matching. |
| `scripts/generate_enhanced_compliance_report.py` | Professional PDF reports with executive summary, detailed findings, and recommendations. |

### Legacy Scripts (scripts/legacy/)

The following scripts are deprecated and kept for reference only:

| Script | Purpose |
| ------ | ------- |
| `scripts/legacy/extract_vector_plan.py` | Extracts raw geometry & text from vector PDFs (text-based extraction). |
| `scripts/legacy/check_plan_compliance_neo4j.py` | Text-based compliance checking (less accurate than component-based approach). |
| `scripts/legacy/generate_compliance_report.py` | Basic PDF report generation (replaced by enhanced version). |

---

## Component Extraction Features

See **[COMPONENT_EXTRACTION_GUIDE.md](COMPONENT_EXTRACTION_GUIDE.md)** for complete documentation.

**Key Advantages:**
- ✅ Geometric setback calculation (works without annotations)
- ✅ Room area calculation from dimensions
- ✅ Component-type classification for intelligent rule matching
- ✅ 50+ component subtypes detected
- ✅ All measurements in consistent units (feet)

This README guides you through the enhanced pipeline. The new component-based approach provides better compliance checking accuracy and more detailed analysis than the legacy text-based extraction.

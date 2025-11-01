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

## 2. Extract Vector Plan Data

```bash
source .venv/bin/activate
python scripts/extract_vector_plan.py \
    --pdf data/House-Floor-Plans-vector.pdf \
    --summary
```

Outputs:
- `data/House-Floor-Plans-vector_output.json` – structured geometry/text extraction.
- `data/House-Floor-Plans-vector_summary.json` – quick summary preview (rooms, dimensions, sheet titles).

---

## 3. Run Compliance Check

This script pulls rules from Neo4j, optionally uses OpenAI embeddings (or Pinecone) for semantic scores, and writes a compliance report JSON.

```bash
python scripts/check_plan_compliance_neo4j.py \
    --plan data/House-Floor-Plans-vector_output.json \
    --use-openai              # omit to rely on local LM Studio embeddings
    # --pinecone              # optional: query Pinecone if no OpenAI fallback
    # --writeback             # optional: push results back into Neo4j
```

Outputs:
- `data/House-Floor-Plans-vector_compliance.json`

Environment values used:
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `OPENAI_API_KEY` *(or LM Studio via `LOCAL_LLM_BASE_URL` when `USE_OPENAI=0`)*
- `PINECONE_API_KEY` *(only if `--pinecone` flag is set)*

---

## 4. Generate a PDF Report (optional)

```bash
python scripts/generate_compliance_report.py \
    --plan data/House-Floor-Plans-vector_output.json \
    --compliance data/House-Floor-Plans-vector_compliance.json \
    --output reports/House-Floor-Plans-vector_report.pdf
```

Result: `reports/House-Floor-Plans-vector_report.pdf`

---

## 5. Useful Tips

- **Check connections**: the compliance script will fail fast if Neo4j/OpenAI/Pinecone credentials are missing. Use the same `.env` in each repo that shares the rule knowledge base.
- **Local LM Studio**: if running offline, keep the API server running with both models loaded (`LLM_MODEL` for chat and `EMBEDDING_MODEL` for embeddings).
- **Batch size**: Pinecone upserts are automatically chunked in batches of 50 vectors; if you change the embedding dimension or metadata volume, adjust as needed inside `loaders/pinecone_loader.py`.
- **House-Floor-Plans-vector.pdf**: serves as the sample plan; swap in new PDFs by pointing the `--pdf` flag at a different file inside `data/`.

---

## Summary of Scripts

| Script | Purpose |
| ------ | ------- |
| `scripts/extract_vector_plan.py` | Extracts geometry & text from vector PDFs, optionally summarises. |
| `scripts/check_plan_compliance_neo4j.py` | Compares the extracted plan JSON against Neo4j rules; can use OpenAI/Pinecone scoring. |
| `scripts/generate_compliance_report.py` | Generates a PDF report using the extracted plan data and compliance results. |

This README should guide you through the full pipeline using the sample plan. Feel free to adapt the commands for new plans or integrate the scripts into larger automation workflows.

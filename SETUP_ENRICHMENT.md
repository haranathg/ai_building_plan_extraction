# Setting Up LLM Enrichment

## Quick Start

To enable LLM enrichment in CompliCheck v2.0, you need to add your Anthropic API key.

### Option 1: Add to .env file (Recommended)

Edit your `.env` file and add:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here...
```

Then run:
```bash
python3 compliCheckV2.py data/plan.pdf
```

### Option 2: Export as environment variable

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here...
python3 compliCheckV2.py data/plan.pdf
```

### Option 3: Pass as command-line argument

```bash
python3 scripts/llm_enrichment_layer.py \
    --input data/components.json \
    --output data/enriched.json \
    --api-key sk-ant-api03-...your-key-here...
```

## Getting an Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

## Verify Setup

Test that enrichment works:

```bash
# Should show enrichment running
python3 compliCheckV2.py data/10-North-Point_REV-A_Lot-2.pdf --keep-intermediates

# Check for enriched file
ls reports/10-North-Point_REV-A_Lot-2_enriched.json
```

If you see:
```
⚠ ANTHROPIC_API_KEY not found in environment
  To enable enrichment, add to .env file:
    ANTHROPIC_API_KEY=sk-ant-...
```

Then the API key is not set correctly.

## Cost Estimates

Typical costs per document:
- **Simple site plan**: ~$0.05 (1 sheet, basic components)
- **Building floor plan**: ~$0.10 (1 sheet, many rooms)
- **Multi-sheet plan**: ~$0.20 (3 sheets, complex)

**To control costs**, use selective enrichment:
```bash
# Only run metadata inference (cheapest)
python3 compliCheckV2.py plan.pdf --enrichment-ops infer_metadata

# Skip expensive labeling
python3 compliCheckV2.py plan.pdf --enrichment-ops infer_metadata categorize reconcile
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"

Install the anthropic library:
```bash
.venv/bin/pip install "anthropic>=0.40.0"
```

### "API key required" error

Make sure:
1. API key is in `.env` file OR exported as environment variable
2. `.env` file is in the project root directory
3. API key starts with `sk-ant-`

Test:
```bash
# Check if .env has the key
grep ANTHROPIC_API_KEY .env

# Check if environment variable is set
echo $ANTHROPIC_API_KEY
```

### Enrichment fails with rate limit error

If you see rate limit errors:
1. Wait a few minutes and retry
2. Configure rate limiting in `config.py`:
   ```python
   EnrichmentConfig.MAX_REQUESTS_PER_MINUTE = 20  # Lower from 50
   EnrichmentConfig.RETRY_DELAY_SECONDS = 10  # Increase from 5
   ```

### Enrichment is too expensive

Options:
1. **Skip enrichment** for simple documents:
   ```bash
   python3 compliCheckV2.py plan.pdf --skip-enrichment
   ```

2. **Use caching** (enabled by default):
   - Enrichment results are cached for 7 days
   - Re-running on same PDF uses cache (free)

3. **Run selective operations**:
   ```bash
   # Only essential operations
   python3 compliCheckV2.py plan.pdf --enrichment-ops infer_metadata categorize
   ```

4. **Set cost limits** in `config.py`:
   ```python
   EnrichmentConfig.MAX_COST_PER_DOCUMENT = 0.05  # Stop if > 5 cents
   ```

## Running Without Enrichment

CompliCheck v2.0 works perfectly fine without enrichment:

```bash
# Fast mode - no API key required
python3 compliCheckV2.py plan.pdf --skip-enrichment
```

You'll still get:
- ✓ Component extraction
- ✓ Compliance checking
- ✓ PDF report generation

You won't get:
- ✗ Enhanced plan type detection
- ✗ Data quality scores
- ✗ Critical component identification

For most simple site plans, the heuristic detection works well enough.

## Next Steps

Once enrichment is working:

1. **Review enriched data**:
   ```bash
   python3 compliCheckV2.py plan.pdf --keep-intermediates
   cat reports/plan_enriched.json | python3 -m json.tool
   ```

2. **Check quality scores** in the PDF report executive summary

3. **Customize operations** in `config.py` based on your needs

4. **Monitor costs** through Anthropic console

---

For more details, see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)

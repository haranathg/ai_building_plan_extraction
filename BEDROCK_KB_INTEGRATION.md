# AWS Bedrock Knowledge Base Integration

## Overview

CompliCheck v2.0 now supports AWS Bedrock Knowledge Base as an alternative to Neo4j + Pinecone for building code compliance checking. This allows you to leverage your existing AWS infrastructure and building code knowledge base stored in Bedrock.

## Features

- **Dual Compliance Engine**: Choose between Neo4j + Pinecone (default) or AWS Bedrock KB
- **Seamless Integration**: Toggle between modes via command-line flag or web UI
- **Claude-Powered Evaluation**: Uses Claude via Bedrock for intelligent compliance assessment
- **Knowledge Base Search**: Automatic retrieval of relevant building codes from your KB
- **Confidence Scoring**: Each compliance check includes a confidence score
- **Source Attribution**: Track which KB documents informed each decision

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# AWS Bedrock Configuration
BEDROCK_API_KEY=<your-base64-encoded-api-key>
BEDROCK_REGION=us-east-1
BEDROCK_KB_ID=<your-knowledge-base-id>
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

**Note**: If you have AWS credentials configured (via `~/.aws/credentials` or IAM role), you can omit `BEDROCK_API_KEY`.

### Required AWS Permissions

Your AWS credentials need the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:Retrieve",
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

## Usage

### Command Line

#### Using Bedrock KB for Compliance

```bash
# Basic usage with Bedrock KB
python3 compliCheckV2.py data/plan.pdf --use-bedrock-kb

# Specify custom KB ID
python3 compliCheckV2.py data/plan.pdf --use-bedrock-kb --kb-id YOUR_KB_ID

# With enrichment enabled (recommended)
python3 compliCheckV2.py data/plan.pdf --use-bedrock-kb --enable-enrichment

# Keep intermediate files for debugging
python3 compliCheckV2.py data/plan.pdf --use-bedrock-kb --keep-intermediates
```

#### Using Neo4j + Pinecone (Default)

```bash
# Standard run - uses Neo4j + Pinecone
python3 compliCheckV2.py data/plan.pdf

# With enrichment
python3 compliCheckV2.py data/plan.pdf --enable-enrichment
```

### Web Frontend

1. Navigate to the **BasicInfo** page
2. Toggle **"Use AWS Bedrock Knowledge Base"** switch
3. Continue with file upload and processing

The choice is saved with your pre-check and used during compliance checking.

## Standalone Script

You can also use the Bedrock KB compliance checker directly:

```bash
python3 scripts/check_component_compliance_bedrock.py \
    --components data/plan_components.json \
    --kb-id YOUR_KB_ID \
    --output data/plan_compliance_bkb.json
```

### Options

- `--components`: Path to extracted components JSON (required)
- `--kb-id`: Bedrock Knowledge Base ID (defaults to `BEDROCK_KB_ID` env var)
- `--region`: AWS region (default: `us-east-1`)
- `--model-id`: Bedrock model ID (default: `anthropic.claude-3-sonnet-20240229-v1:0`)
- `--max-results`: Max KB search results per component (default: 5)
- `--output`: Custom output path (default: `<input>_compliance_bkb.json`)

## Output Format

The Bedrock KB compliance checker produces JSON output with this structure:

```json
{
  "metadata": {
    "timestamp": "2025-01-16T10:30:00Z",
    "kb_id": "YOUR_KB_ID",
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "total_components": 15,
    "status_summary": {
      "PASS": 10,
      "FAIL": 2,
      "REVIEW": 2,
      "NOT_APPLICABLE": 1
    }
  },
  "evaluations": [
    {
      "component_id": "comp_001",
      "component_type": "setback",
      "component_name": "Front Setback",
      "requirement": "Minimum 6m front setback for residential zones",
      "expected_value": "6m",
      "actual_value": "5.5m",
      "status": "FAIL",
      "confidence": 0.95,
      "notes": [
        "Component does not meet minimum setback requirement",
        "Requires variance or redesign"
      ],
      "kb_sources": [
        "s3://building-codes/residential-zones.pdf",
        "s3://building-codes/setback-requirements.pdf"
      ]
    }
  ]
}
```

## Compliance Status Codes

- **PASS**: Component meets all requirements
- **FAIL**: Component violates one or more requirements
- **REVIEW**: Requires manual review (unclear or edge case)
- **NOT_APPLICABLE**: No relevant building codes found

## How It Works

### 1. Component Extraction
Building plan components are extracted using the standard pipeline (same for both modes).

### 2. Knowledge Base Query
For each component, the system:
- Constructs a search query based on component type and attributes
- Retrieves top N relevant building code documents from Bedrock KB
- Ranks results by relevance score

### 3. Claude Evaluation
Claude (via Bedrock) analyzes:
- Component attributes
- Retrieved building code requirements
- Contextual information

Then determines:
- Compliance status
- Specific requirement violated/met
- Expected vs actual values
- Confidence score
- Detailed explanation

### 4. Report Generation
Results are formatted into:
- JSON compliance report with all details
- PDF report (same format as Neo4j + Pinecone mode)

## Comparison: Bedrock KB vs Neo4j + Pinecone

| Feature | Bedrock KB | Neo4j + Pinecone |
|---------|------------|------------------|
| **Setup** | AWS account + KB | Local infrastructure |
| **Cost** | Pay-per-use | Self-hosted |
| **Scalability** | AWS managed | Manual scaling |
| **Data Format** | Unstructured docs | Graph + vectors |
| **Query Speed** | AWS network latency | Local speed |
| **Accuracy** | Depends on KB quality | Depends on data quality |
| **Maintenance** | AWS managed | Self-managed |

## Troubleshooting

### "Knowledge Base ID not specified"

**Solution**: Set `BEDROCK_KB_ID` in `.env` or use `--kb-id` flag.

```bash
export BEDROCK_KB_ID=YOUR_KB_ID
python3 compliCheckV2.py data/plan.pdf --use-bedrock-kb
```

### "boto3 not installed"

**Solution**: Install AWS SDK for Python.

```bash
pip install boto3
```

### "Bedrock KB query failed: AccessDeniedException"

**Solution**: Check AWS credentials and permissions.

```bash
aws sts get-caller-identity  # Verify credentials
aws bedrock list-foundation-models  # Test Bedrock access
```

### "No KB results found for component"

**Possible Causes**:
- Knowledge Base doesn't contain relevant building codes
- Component type not well-described
- KB search query too specific

**Solutions**:
- Enrich your KB with more building code documents
- Use enrichment layer (`--enable-enrichment`) for better component descriptions
- Adjust `--max-results` to retrieve more documents

## Best Practices

1. **Use Enrichment**: Always enable LLM enrichment for better component descriptions
   ```bash
   python3 compliCheckV2.py data/plan.pdf --use-bedrock-kb --enable-enrichment
   ```

2. **Populate Your KB**: Ensure your Bedrock Knowledge Base contains:
   - Local building codes and regulations
   - Zoning requirements
   - Safety standards
   - Historical precedents

3. **Monitor Costs**: Bedrock usage is billed by AWS. Monitor your usage:
   - KB retrieval calls
   - Claude inference tokens
   - Data transfer

4. **Test Both Modes**: Compare results from both engines to validate accuracy

5. **Keep Intermediates**: Use `--keep-intermediates` during development to debug issues

## Migration Guide

### From Neo4j + Pinecone to Bedrock KB

1. **Export your building codes** from Neo4j to documents
2. **Upload to S3** and configure as Bedrock KB data source
3. **Sync KB** to index documents
4. **Test** with sample plans
5. **Switch** production traffic with `--use-bedrock-kb`

### From Bedrock KB to Neo4j + Pinecone

Simply remove the `--use-bedrock-kb` flag - the system defaults to Neo4j + Pinecone.

## API Integration

The FastAPI backend automatically uses the selected compliance engine based on the `use_bedrock_kb` flag saved during BasicInfo.

No additional API changes required - the frontend toggle controls the behavior.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review AWS Bedrock KB documentation
- Check CompliCheck logs in `reports_web/` directory
- Open an issue in the repository

## Future Enhancements

- [ ] Hybrid mode: Use both engines and compare results
- [ ] Custom KB configuration per project
- [ ] Caching of KB queries for faster processing
- [ ] Batch processing for multiple plans
- [ ] Historical compliance tracking
- [ ] KB document suggestions based on components


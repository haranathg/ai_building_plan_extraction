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

### AWS Credentials Setup

**IMPORTANT**: This integration requires AWS IAM credentials, NOT Bedrock API Keys (ABSK).

#### Option 1: AWS CLI Configuration (Recommended)

1. **Create IAM Access Keys**:
   - Go to AWS Console > IAM > Users > Your User
   - Click "Security credentials" tab
   - Click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Save the Access Key ID and Secret Access Key

2. **Configure AWS CLI**:
   ```bash
   aws configure
   ```
   Enter when prompted:
   - AWS Access Key ID: `<your-access-key-id>`
   - AWS Secret Access Key: `<your-secret-access-key>`
   - Default region name: `ap-southeast-2` (or your region)
   - Default output format: `json`

#### Option 2: Environment Variables

Add the following to your `.env` file:

```bash
# AWS IAM Credentials (NOT Bedrock API Keys!)
AWS_ACCESS_KEY_ID=<your-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-secret-access-key>

# AWS Bedrock Configuration
USE_BEDROCK_KB=1  # Set to 1 to use Bedrock KB by default, 0 for Neo4j + Pinecone
BEDROCK_REGION=ap-southeast-2
BEDROCK_KB_ID=<your-knowledge-base-id>
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

**Note**:
- Remove or comment out `BEDROCK_API_KEY` if you have it in your `.env` - it's not compatible with boto3.
- The `--use-bedrock-kb` flag overrides the `USE_BEDROCK_KB` environment variable if both are set.

### Required IAM Permissions

Your IAM user/role needs the following permissions:

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

### Why Not Bedrock API Keys (ABSK)?

Bedrock API Keys (starting with "ABSK") are designed for direct REST API access and require AWS Signature V4 signing, which is complex to implement. The boto3 SDK (which this integration uses) requires IAM credentials instead.

If you have a Bedrock API Key:
1. Keep it for other use cases (e.g., direct REST API calls)
2. Create IAM access keys for this integration (see instructions above)
3. Both can coexist - use IAM credentials for boto3-based tools

## Usage

### Command Line

#### Using Bedrock KB for Compliance

**Option 1: Set in .env (recommended for persistent use)**
```bash
# In .env file
USE_BEDROCK_KB=1

# Then run normally
python3 compliCheckV2.py data/plan.pdf
```

**Option 2: Use command-line flag**
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
# In .env file
USE_BEDROCK_KB=0

# Or just run normally (Neo4j + Pinecone is the default)
python3 compliCheckV2.py data/plan.pdf

# With enrichment
python3 compliCheckV2.py data/plan.pdf --enable-enrichment
```

### Web Frontend

The web frontend uses the compliance engine configured via the `USE_BEDROCK_KB` environment variable in your backend `.env` file. There is no UI toggle - the backend automatically uses whatever is configured in the environment.

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

### "BEDROCK API KEY (ABSK) DETECTED"

**Problem**: You have a Bedrock API Key in your `.env` file, but boto3 requires IAM credentials.

**Solution**: Create and configure IAM access keys instead:

1. Go to AWS Console > IAM > Users > Your User > Security Credentials
2. Click "Create access key" > Choose "CLI"
3. Run `aws configure` and enter the credentials
4. Remove or comment out `BEDROCK_API_KEY` from `.env`

### "The security token included in the request is invalid"

**Problem**: AWS credentials are not configured or are invalid.

**Solution**: Configure AWS credentials:

```bash
# Check if credentials are configured
aws sts get-caller-identity

# If not, configure them
aws configure
```

### "Bedrock KB query failed: AccessDeniedException"

**Problem**: Your IAM user/role lacks required Bedrock permissions.

**Solution**: Add required permissions to your IAM user/role:

1. Go to AWS Console > IAM > Users > Your User > Permissions
2. Attach policy with `bedrock:InvokeModel` and `bedrock:Retrieve` permissions
3. Or create a custom policy using the JSON from the Configuration section above

You can test your permissions:

```bash
aws sts get-caller-identity  # Verify credentials
aws bedrock list-foundation-models --region ap-southeast-2  # Test Bedrock access
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

### "ThrottlingException: Too many requests"

**Problem**: AWS Bedrock has rate limits on API calls. When processing many components, you may hit these limits.

**Solution**: The script includes automatic retry logic and a 2-second delay between component evaluations. If you still encounter throttling:
- Wait a few minutes before retrying
- Process fewer components at a time
- Check your AWS account's service quotas for Bedrock
- Consider requesting a quota increase from AWS Support

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


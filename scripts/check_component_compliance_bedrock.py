"""
check_component_compliance_bedrock.py
--------------------------------------
AWS Bedrock Knowledge Base compliance checking for building plan components.

This script uses AWS Bedrock Knowledge Base to retrieve relevant building code
rules and evaluate compliance using Claude via Bedrock.

Usage:
    python3 scripts/check_component_compliance_bedrock.py \
        --components data/House-Floor-Plans-vector_components.json

Optional flags:
    --kb-id BEDROCK_KB_ID           # Knowledge Base ID (from env if not specified)
    --region us-east-1              # AWS region
    --model-id anthropic.claude-3-sonnet-20240229-v1:0  # Bedrock model
    --max-results 5                 # Max KB search results per component
    --output path/to/output.json    # Custom output path

Output:
    Writes <plan>_compliance_bkb.json with detailed compliance findings.

Environment Variables Required:
    BEDROCK_API_KEY or AWS credentials configured
    BEDROCK_KB_ID (if not passed via --kb-id)
    BEDROCK_REGION (optional, default: us-east-1)
    BEDROCK_MODEL_ID (optional, default: anthropic.claude-3-sonnet-20240229-v1:0)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import base64
import hmac
import hashlib
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    print("[WARNING] boto3 not installed. Install with: pip install boto3")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_REGION = os.getenv('BEDROCK_REGION', 'us-east-1')
DEFAULT_KB_ID = os.getenv('BEDROCK_KB_ID')
DEFAULT_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
# Try both environment variable names
BEDROCK_API_KEY = os.getenv('AWS_BEARER_TOKEN_BEDROCK') or os.getenv('BEDROCK_API_KEY')


# =============================================================================
# Logging
# =============================================================================

def log(msg: str) -> None:
    print(f"[INFO] {msg}")


def error(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class KBSearchResult:
    """Result from Bedrock Knowledge Base search."""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]


@dataclass
class ComplianceEvaluation:
    """Result of evaluating a component against rules."""
    component_id: str
    component_type: str
    component_name: str
    requirement: str
    expected_value: Any
    actual_value: Any
    status: str  # PASS, FAIL, REVIEW, NOT_APPLICABLE
    confidence: float
    notes: List[str]
    kb_sources: List[str]


# =============================================================================
# AWS Bedrock HTTP Client (for ABSK API Keys)
# =============================================================================

class BedrockHTTPClient:
    """HTTP client for AWS Bedrock using ABSK API Keys."""

    def __init__(self, api_key: str, region: str):
        # Decode base64 if needed
        decoded_key = api_key
        try:
            if not api_key.startswith('ABSK'):
                decoded = base64.b64decode(api_key).decode('utf-8')
                if decoded.startswith('ABSK'):
                    decoded_key = decoded
        except:
            pass

        self.api_key = decoded_key
        self.region = region
        self.kb_base_url = f"https://bedrock-agent-runtime.{region}.amazonaws.com"
        self.runtime_base_url = f"https://bedrock-runtime.{region}.amazonaws.com"

        log(f"Using Bedrock API Key authentication for region {region}")

    def retrieve(self, knowledgeBaseId: str, retrievalQuery: Dict, retrievalConfiguration: Dict) -> Dict:
        """Query Knowledge Base."""
        import requests

        url = f"{self.kb_base_url}/knowledgebases/{knowledgeBaseId}/retrieve"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'retrievalQuery': retrievalQuery,
            'retrievalConfiguration': retrievalConfiguration
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error(f"HTTP {e.response.status_code}: {e.response.text}")
            raise

    def invoke_model(self, modelId: str, contentType: str, accept: str, body: str) -> Dict:
        """Invoke Bedrock model."""
        import requests

        url = f"{self.runtime_base_url}/model/{modelId}/invoke"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': contentType,
            'Accept': accept
        }

        response = requests.post(url, headers=headers, data=body, timeout=60)
        response.raise_for_status()

        # Return response in boto3-compatible format
        class ResponseWrapper:
            def __init__(self, content):
                self._content = content
            def read(self):
                return self._content

        return {'body': ResponseWrapper(response.content)}


def setup_bedrock_clients_boto3(region: str):
    """Initialize Bedrock clients using boto3 with IAM credentials."""

    if not BOTO3_AVAILABLE:
        error("boto3 is required but not installed. Run: pip install boto3")
        sys.exit(1)

    try:
        session = boto3.Session(region_name=region)

        # Test credentials
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        log(f"Using AWS IAM credentials for account: {identity['Account']}")
        log(f"ARN: {identity['Arn']}")

        bedrock_agent = session.client('bedrock-agent-runtime')
        bedrock_runtime = session.client('bedrock-runtime')

        return bedrock_agent, bedrock_runtime

    except Exception as e:
        error(f"Failed to initialize boto3 clients: {e}")
        error("\nTo use this script, you need either:")
        error("  1. BEDROCK_API_KEY (ABSK*) in .env, OR")
        error("  2. AWS IAM credentials (AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY)")
        error("\nFor IAM credentials:")
        error("  - Run 'aws configure', OR")
        error("  - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        sys.exit(1)


def setup_bedrock_client(region: str, api_key: str):
    """Initialize Bedrock client - supports both ABSK keys and IAM credentials."""

    # Try ABSK key first
    if api_key:
        # Decode to check if it's an ABSK key
        decoded_key = api_key
        try:
            if not api_key.startswith('ABSK'):
                decoded = base64.b64decode(api_key).decode('utf-8')
                if decoded.startswith('ABSK'):
                    decoded_key = decoded
        except:
            pass

        if 'ABSK' in decoded_key or decoded_key.startswith('ABSK'):
            log("Using Bedrock API Key (ABSK) authentication")
            client = BedrockHTTPClient(api_key, region)
            return client, client

    # Fall back to IAM credentials via boto3
    log("Using AWS IAM credentials (boto3)")
    return setup_bedrock_clients_boto3(region)


# =============================================================================
# Bedrock Knowledge Base Query
# =============================================================================

def query_knowledge_base(
    bedrock_agent,
    kb_id: str,
    query: str,
    max_results: int = 5
) -> List[KBSearchResult]:
    """Query Bedrock Knowledge Base and return relevant documents."""

    try:
        response = bedrock_agent.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': max_results
                }
            }
        )

        results = []
        for item in response.get('retrievalResults', []):
            results.append(KBSearchResult(
                content=item['content']['text'],
                score=item.get('score', 0.0),
                source=item.get('location', {}).get('s3Location', {}).get('uri', 'Unknown'),
                metadata=item.get('metadata', {})
            ))

        return results

    except Exception as e:
        error(f"Bedrock KB query failed: {e}")
        return []


# =============================================================================
# Claude Evaluation via Bedrock
# =============================================================================

def evaluate_compliance_with_claude(
    bedrock_runtime,
    model_id: str,
    component: Dict[str, Any],
    kb_results: List[KBSearchResult]
) -> ComplianceEvaluation:
    """Use Claude via Bedrock to evaluate component compliance."""

    # Build context from KB results
    kb_context = "\n\n".join([
        f"[Rule {i+1}] (Relevance: {r.score:.2f})\n{r.content}"
        for i, r in enumerate(kb_results)
    ])

    # Build prompt for Claude
    prompt = f"""You are a building code compliance expert. Evaluate the following component against relevant building regulations.

COMPONENT INFORMATION:
- Type: {component.get('component_type', 'Unknown')}
- Name: {component.get('component_name', 'Unnamed')}
- Attributes: {json.dumps(component.get('attributes', {}), indent=2)}

RELEVANT BUILDING CODE RULES:
{kb_context}

TASK:
1. Determine if the component complies with the relevant building codes
2. Identify specific requirements that apply
3. Compare expected values vs actual values
4. Provide a compliance status: PASS, FAIL, REVIEW, or NOT_APPLICABLE

Respond ONLY with a JSON object in this format:
{{
    "requirement": "Brief description of the primary requirement",
    "expected_value": "What the code requires",
    "actual_value": "What the component has",
    "status": "PASS|FAIL|REVIEW|NOT_APPLICABLE",
    "confidence": 0.0-1.0,
    "notes": ["Detailed explanation", "Additional context"]
}}"""

    try:
        # Call Claude via Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0.0,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )

        response_body = json.loads(response['body'].read())
        result_text = response_body['content'][0]['text']

        # Parse JSON response from Claude
        # Extract JSON from markdown code blocks if present
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()

        result = json.loads(result_text)

        # Build ComplianceEvaluation
        return ComplianceEvaluation(
            component_id=component.get('component_id', ''),
            component_type=component.get('component_type', 'Unknown'),
            component_name=component.get('component_name', 'Unnamed'),
            requirement=result.get('requirement', 'Unknown requirement'),
            expected_value=result.get('expected_value', 'N/A'),
            actual_value=result.get('actual_value', 'N/A'),
            status=result.get('status', 'REVIEW'),
            confidence=float(result.get('confidence', 0.5)),
            notes=result.get('notes', []),
            kb_sources=[r.source for r in kb_results]
        )

    except Exception as e:
        error(f"Claude evaluation failed for component {component.get('component_id', 'unknown')}: {e}")

        return ComplianceEvaluation(
            component_id=component.get('component_id', ''),
            component_type=component.get('component_type', 'Unknown'),
            component_name=component.get('component_name', 'Unnamed'),
            requirement='Evaluation failed',
            expected_value='N/A',
            actual_value='N/A',
            status='REVIEW',
            confidence=0.0,
            notes=[f"Error during evaluation: {str(e)}"],
            kb_sources=[]
        )


# =============================================================================
# Main Processing
# =============================================================================

def process_components(
    bedrock_agent,
    bedrock_runtime,
    components: List[Dict[str, Any]],
    kb_id: str,
    model_id: str,
    max_results: int
) -> Dict[str, Any]:
    """Process all components and evaluate compliance."""

    log(f"Processing {len(components)} components with Bedrock KB...")

    evaluations = []

    for i, component in enumerate(components, 1):
        comp_type = component.get('component_type', 'Unknown')
        comp_name = component.get('component_name', 'Unnamed')

        log(f"[{i}/{len(components)}] Checking {comp_type}: {comp_name}")

        # Build query for KB
        query = f"Building code requirements for {comp_type}"
        if comp_name and comp_name != 'Unnamed':
            query += f" {comp_name}"

        # Get relevant rules from KB
        kb_results = query_knowledge_base(bedrock_agent, kb_id, query, max_results)

        if not kb_results:
            log(f"  ⚠ No KB results found for {comp_type}")
            evaluations.append(ComplianceEvaluation(
                component_id=component.get('component_id', ''),
                component_type=comp_type,
                component_name=comp_name,
                requirement='No applicable rules found',
                expected_value='N/A',
                actual_value='N/A',
                status='NOT_APPLICABLE',
                confidence=0.0,
                notes=['No relevant building code rules found in knowledge base'],
                kb_sources=[]
            ))
            continue

        log(f"  Found {len(kb_results)} relevant rules")

        # Evaluate compliance with Claude
        evaluation = evaluate_compliance_with_claude(
            bedrock_runtime,
            model_id,
            component,
            kb_results
        )

        evaluations.append(evaluation)
        log(f"  Status: {evaluation.status} (Confidence: {evaluation.confidence:.2f})")

        # Add delay to avoid AWS throttling (except for last component)
        if i < len(components):
            import time
            time.sleep(2.0)  # 2 second delay between requests

    # Calculate summary statistics
    status_counts = defaultdict(int)
    for eval in evaluations:
        status_counts[eval.status] += 1

    return {
        'metadata': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'kb_id': kb_id,
            'model_id': model_id,
            'total_components': len(components),
            'status_summary': dict(status_counts)
        },
        'evaluations': [asdict(e) for e in evaluations]
    }


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Check building plan compliance using AWS Bedrock Knowledge Base'
    )
    parser.add_argument(
        '--components',
        required=True,
        help='Path to components JSON file'
    )
    parser.add_argument(
        '--kb-id',
        default=DEFAULT_KB_ID,
        help='Bedrock Knowledge Base ID'
    )
    parser.add_argument(
        '--region',
        default=DEFAULT_REGION,
        help='AWS region'
    )
    parser.add_argument(
        '--model-id',
        default=DEFAULT_MODEL_ID,
        help='Bedrock model ID for Claude'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=5,
        help='Maximum KB search results per component'
    )
    parser.add_argument(
        '--output',
        help='Output JSON path (default: <input>_compliance_bkb.json)'
    )

    args = parser.parse_args()

    # Validate KB ID
    if not args.kb_id:
        error("Bedrock Knowledge Base ID not specified. Set BEDROCK_KB_ID in .env or use --kb-id")
        sys.exit(1)

    # Load components
    components_path = Path(args.components)
    if not components_path.exists():
        error(f"Components file not found: {components_path}")
        sys.exit(1)

    log(f"Loading components from {components_path}")
    with open(components_path) as f:
        data = json.load(f)

        # Try different component structures
        components = data.get('components', [])

        # If no top-level components array, flatten from sheets structure
        if not components and 'sheets' in data:
            components = []
            for sheet in data['sheets']:
                # Add rooms as components
                for room in sheet.get('rooms', []):
                    room['component_type'] = 'room'
                    room['component_id'] = f"room_{len(components)}"
                    room['component_name'] = room.get('name', 'Unnamed')
                    components.append(room)

                # Add setbacks as components
                for setback in sheet.get('geometric_setbacks', []):
                    setback['component_type'] = 'setback'
                    setback['component_id'] = f"setback_{len(components)}"
                    setback['component_name'] = setback.get('name', 'Setback')
                    components.append(setback)

    if not components:
        error("No components found in input file")
        sys.exit(1)

    # Setup Bedrock clients
    log(f"Connecting to AWS Bedrock in {args.region}")
    bedrock_agent, bedrock_runtime = setup_bedrock_client(args.region, BEDROCK_API_KEY)

    # Process components
    results = process_components(
        bedrock_agent,
        bedrock_runtime,
        components,
        args.kb_id,
        args.model_id,
        args.max_results
    )

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = components_path.parent / f"{components_path.stem}_compliance_bkb.json"

    # Save results
    log(f"Writing compliance results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    summary = results['metadata']['status_summary']
    log("\n" + "="*70)
    log("COMPLIANCE CHECK SUMMARY (Bedrock KB)")
    log("="*70)
    log(f"Total components: {results['metadata']['total_components']}")
    for status, count in summary.items():
        log(f"  {status}: {count}")
    log("="*70)

    return 0


if __name__ == '__main__':
    sys.exit(main())

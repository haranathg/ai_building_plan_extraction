"""
llm_enrichment_layer.py
-----------------------
Modular LLM enhancement layer that sits between extraction and compliance checking.

Pipeline Integration:
    Step 1: extract_compliance_components.py → structured JSON
    Step 2: llm_enrichment_layer.py → enriched JSON (THIS MODULE)
    Step 3: compliance_kb_matcher.py → matched rules
    Step 4: pdf_report_generator.py → final PDF report

This module is designed to be called programmatically or as a CLI tool.
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars already set

# Try importing both LLM providers
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# =============================================================================
# LLM Enrichment Engine
# =============================================================================

class LLMEnrichmentEngine:
    """
    Lightweight LLM enrichment that adds intelligent metadata to extracted components.
    Supports both Anthropic Claude and OpenAI models.
    Designed to integrate seamlessly into existing pipelines.
    """

    def __init__(self, api_key: str = None, provider: str = "auto", model: str = None):
        """
        Initialize LLM enrichment engine.

        Args:
            api_key: API key (auto-detected if None)
            provider: 'anthropic', 'openai', or 'auto' (default: auto-detect)
            model: Model name (uses defaults if None)
        """
        self.provider = provider
        self.max_tokens = 4096

        # Auto-detect provider if not specified
        if provider == "auto":
            if api_key:
                # If key provided, try to guess from format
                if api_key.startswith("sk-ant-"):
                    self.provider = "anthropic"
                elif api_key.startswith("sk-"):
                    self.provider = "openai"
            else:
                # Check environment variables (prioritize OpenAI since it's more commonly available)
                if os.environ.get("OPENAI_API_KEY"):
                    self.provider = "openai"
                    api_key = os.environ.get("OPENAI_API_KEY")
                elif os.environ.get("ANTHROPIC_API_KEY"):
                    self.provider = "anthropic"
                    api_key = os.environ.get("ANTHROPIC_API_KEY")

        # Initialize the appropriate client
        if self.provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise ImportError("anthropic library not installed. Run: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model or "claude-sonnet-4-20250514"
            print(f"🤖 Using Anthropic Claude ({self.model})")

        elif self.provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("openai library not installed. Run: pip install openai")
            self.client = OpenAI(api_key=api_key)
            self.model = model or "gpt-4o-mini"
            print(f"🤖 Using OpenAI ({self.model})")
        else:
            raise ValueError(f"Unknown provider: {self.provider}. Use 'anthropic' or 'openai'")

    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Make a call to the LLM API with error handling."""
        try:
            if self.provider == "anthropic":
                return self._call_anthropic(prompt, system_prompt)
            elif self.provider == "openai":
                return self._call_openai(prompt, system_prompt)
        except Exception as e:
            print(f"⚠️  LLM API error: {e}")
            return "{}"

    def _call_anthropic(self, prompt: str, system_prompt: str = "") -> str:
        """Call Anthropic Claude API."""
        messages = [{"role": "user", "content": prompt}]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt if system_prompt else None,
            messages=messages
        )

        return response.content[0].text

    def _call_openai(self, prompt: str, system_prompt: str = "") -> str:
        """Call OpenAI API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        return response.choices[0].message.content
    
    def _extract_json(self, response: str) -> Dict:
        """Extract JSON from Claude's response, handling markdown formatting."""
        response_clean = response.strip()
        
        # Remove markdown code blocks
        if "```json" in response_clean:
            response_clean = response_clean.split("```json")[1].split("```")[0].strip()
        elif "```" in response_clean:
            response_clean = response_clean.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(response_clean)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            return {}
    
    def infer_sheet_metadata(self, sheet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Infer additional metadata about a sheet for better downstream processing.
        Returns enhanced sheet metadata.
        """
        system_prompt = """You are an architectural drawing analyzer. Infer metadata about this sheet.
Return JSON with:
{
  "drawing_type": "floor_plan|site_plan|elevation|section|detail|roof_plan|foundation",
  "drawing_subtype": "first_floor|second_floor|front_elevation|etc",
  "confidence": 0.0-1.0,
  "primary_purpose": "brief description",
  "compliance_categories": ["setbacks", "room_sizing", "egress", "accessibility", "fire_safety"],
  "review_priority": "high|medium|low",
  "extraction_quality": "excellent|good|fair|poor"
}"""
        
        # Prepare minimal sheet info for LLM
        sheet_summary = {
            "sheet_number": sheet.get("sheet_number"),
            "title": sheet.get("sheet_title", ""),
            "scale": sheet.get("scale"),
            "room_count": len(sheet.get("rooms", [])),
            "has_setbacks": len(sheet.get("setbacks", [])) > 0,
            "has_parking": len(sheet.get("parking", [])) > 0,
            "has_accessibility": len(sheet.get("accessibility", [])) > 0,
            "has_fire_safety": len(sheet.get("fire_safety", [])) > 0,
            "has_structural": len(sheet.get("structural_elements", [])) > 0,
            "has_mep": len(sheet.get("mep_elements", [])) > 0
        }
        
        prompt = f"Analyze this sheet and infer metadata:\n\n{json.dumps(sheet_summary, indent=2)}"
        
        response = self._call_llm(prompt, system_prompt)
        metadata = self._extract_json(response)
        
        return metadata
    
    def categorize_components(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize all extracted components by compliance domain.
        Useful for routing to specific KB checks.
        """
        system_prompt = """You are a building code expert. Categorize components by compliance domain.
Return JSON with component counts and categories:
{
  "by_compliance_domain": {
    "zoning": {"components": ["setbacks", "lot_coverage"], "count": 5},
    "building_code": {"components": ["rooms", "stairs", "openings"], "count": 23},
    "fire_safety": {"components": ["fire_safety"], "count": 8},
    "accessibility": {"components": ["accessibility"], "count": 3},
    "structural": {"components": ["structural_elements"], "count": 12}
  },
  "critical_components": ["list of components needing priority review"],
  "missing_common_components": ["components typically expected but not found"]
}"""
        
        summary = {
            "total_sheets": components["summary"]["total_sheets"],
            "total_rooms": components["summary"]["total_rooms"],
            "total_setbacks": components["summary"]["total_setbacks"],
            "total_parking": components["summary"]["total_parking"],
            "total_fire_safety": components["summary"]["total_fire_safety"],
            "total_accessibility": components["summary"]["total_accessibility"],
            "room_types": components["summary"]["room_types"]
        }
        
        prompt = f"Categorize these components:\n\n{json.dumps(summary, indent=2)}"
        
        response = self._call_llm(prompt, system_prompt)
        categorization = self._extract_json(response)
        
        return categorization
    
    def generate_component_labels(self, components_list: List[Dict], 
                                   component_type: str) -> List[Dict[str, Any]]:
        """
        Generate human-readable labels and context for components.
        Useful for report generation later.
        """
        if not components_list:
            return []
        
        system_prompt = f"""You are labeling {component_type} components for a compliance report.
For each component, add:
- readable_label: Human-friendly name
- compliance_context: Why this matters for compliance
- review_notes: What to check

Return JSON array matching input length."""
        
        # Limit to first 20 components to avoid token limits
        sample = components_list[:20]
        
        prompt = f"Label these {component_type} components:\n\n{json.dumps(sample, indent=2)}"
        
        response = self._call_llm(prompt, system_prompt)
        labels = self._extract_json(response)
        
        # Ensure we return a list
        if not isinstance(labels, list):
            labels = [labels] if labels else []
        
        return labels
    
    def reconcile_conflicts(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify and resolve conflicts or inconsistencies in extracted data.
        """
        system_prompt = """You are a data quality analyst for architectural drawings.
Identify conflicts, missing data, or inconsistencies.
Return JSON:
{
  "conflicts": [{"issue": "description", "severity": "high|medium|low", "resolution": "suggestion"}],
  "missing_data": ["list of expected but missing elements"],
  "quality_score": 0.0-1.0,
  "confidence_level": "high|medium|low"
}"""
        
        # Check for common conflicts
        checks = {
            "total_rooms": components["summary"]["total_rooms"],
            "sheets_with_rooms": sum(1 for s in components["sheets"] if s.get("rooms")),
            "has_site_plan": any(s.get("lot_info") for s in components["sheets"]),
            "has_accessibility_features": components["summary"]["total_accessibility"] > 0,
            "has_fire_safety": components["summary"]["total_fire_safety"] > 0
        }
        
        prompt = f"Analyze for conflicts:\n\n{json.dumps(checks, indent=2)}"
        
        response = self._call_llm(prompt, system_prompt)
        reconciliation = self._extract_json(response)
        
        return reconciliation
    
    def enrich_components(self, components_json: Dict[str, Any], 
                         operations: List[str] = None) -> Dict[str, Any]:
        """
        Main enrichment function. Runs specified operations on extracted components.
        
        Args:
            components_json: Output from extract_compliance_components.py
            operations: List of operations to run. Options:
                - "infer_metadata": Add sheet-level metadata
                - "categorize": Categorize by compliance domain
                - "label": Add human-readable labels
                - "reconcile": Identify conflicts
                - "all": Run all operations (default)
        
        Returns:
            Enhanced components dict with new "llm_enrichment" section
        """
        if operations is None or "all" in operations:
            operations = ["infer_metadata", "categorize", "label", "reconcile"]
        
        print("🧠 LLM Enrichment Layer")
        print("=" * 60)
        
        enriched = components_json.copy()
        enriched["llm_enrichment"] = {}
        
        # Operation 1: Infer sheet metadata
        if "infer_metadata" in operations:
            print("📋 Inferring sheet metadata...")
            sheet_metadata = []
            for sheet in components_json["sheets"]:
                metadata = self.infer_sheet_metadata(sheet)
                sheet_metadata.append({
                    "sheet_number": sheet["sheet_number"],
                    "metadata": metadata
                })
                print(f"   Sheet {sheet['sheet_number']}: {metadata.get('drawing_type', 'unknown')}")
            
            enriched["llm_enrichment"]["sheet_metadata"] = sheet_metadata
        
        # Operation 2: Categorize components
        if "categorize" in operations:
            print("\n🏷️  Categorizing components...")
            categorization = self.categorize_components(components_json)
            enriched["llm_enrichment"]["categorization"] = categorization
            
            if categorization.get("by_compliance_domain"):
                for domain, info in categorization["by_compliance_domain"].items():
                    print(f"   {domain}: {info.get('count', 0)} components")
        
        # Operation 3: Generate labels (for rooms only, to save tokens)
        if "label" in operations:
            print("\n📝 Generating component labels...")
            all_rooms = []
            for sheet in components_json["sheets"]:
                all_rooms.extend(sheet.get("rooms", []))
            
            if all_rooms:
                room_labels = self.generate_component_labels(all_rooms, "room")
                enriched["llm_enrichment"]["room_labels"] = room_labels
                print(f"   Generated labels for {len(room_labels)} rooms")
        
        # Operation 4: Reconcile conflicts
        if "reconcile" in operations:
            print("\n🔍 Reconciling conflicts...")
            reconciliation = self.reconcile_conflicts(components_json)
            enriched["llm_enrichment"]["reconciliation"] = reconciliation
            
            quality_score = reconciliation.get("quality_score", 0.0)
            print(f"   Data quality: {quality_score:.2f}/1.0")
            
            if reconciliation.get("conflicts"):
                print(f"   Found {len(reconciliation['conflicts'])} conflicts")
        
        print("\n✅ Enrichment complete")
        
        return enriched


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="LLM Enrichment Layer - Add intelligent metadata to extracted components"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSON from extract_compliance_components.py"
    )
    parser.add_argument(
        "--output",
        help="Output path for enriched JSON (optional, defaults to *_enriched.json)"
    )
    parser.add_argument(
        "--api-key",
        help="API key (auto-detects ANTHROPIC_API_KEY or OPENAI_API_KEY from env)"
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "anthropic", "openai"],
        default="auto",
        help="LLM provider to use (default: auto-detect)"
    )
    parser.add_argument(
        "--model",
        help="Model name (default: claude-sonnet-4 or gpt-4o-mini)"
    )
    parser.add_argument(
        "--operations",
        nargs="+",
        choices=["infer_metadata", "categorize", "label", "reconcile", "all"],
        default=["all"],
        help="Enrichment operations to run"
    )

    args = parser.parse_args()

    # Load input
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"📂 Loading: {input_path}")
    with open(input_path, "r") as f:
        components = json.load(f)

    # Run enrichment (auto-detects API key and provider)
    engine = LLMEnrichmentEngine(
        api_key=args.api_key,
        provider=args.provider,
        model=args.model
    )
    enriched = engine.enrich_components(components, args.operations)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(input_path.stem + "_enriched.json")
    
    # Save enriched output
    with open(output_path, "w") as f:
        json.dump(enriched, f, indent=2)
    
    print(f"\n💾 Enriched data saved: {output_path}")
    print(f"📊 Original components + LLM enrichment layer added")


if __name__ == "__main__":
    main()

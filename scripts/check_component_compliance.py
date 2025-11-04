"""
check_component_compliance.py
------------------------------
Component-based compliance checking against Neo4j + Pinecone rules.

This script reads the enhanced component JSON (from extract_compliance_components.py)
and evaluates each component against relevant building code rules.

Usage:
    python3 scripts/check_component_compliance.py \
        --components data/House-Floor-Plans-vector_components.json

Optional flags:
    --pinecone-index planning-rules  # override index name
    --top-k 2                        # top rules per component type
    --writeback                      # write results to Neo4j
    --output path/to/output.json     # custom output path

Output:
    Writes <plan>_compliance.json with detailed compliance findings.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from neo4j import GraphDatabase
from pinecone import Pinecone
from tqdm import tqdm

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# =============================================================================
# Logging
# =============================================================================

def log(msg: str) -> None:
    print(f"[INFO] {msg}")


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class RuleCandidate:
    """A candidate rule matched to a component."""
    rule_id: str
    source: str  # "pinecone" or "neo4j_keyword"
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleDetail:
    """Full rule details from Neo4j."""
    rule_id: str
    section_id: Optional[str]
    section_title: Optional[str]
    requirement: Optional[str]
    topic: Optional[str]
    attribute: Optional[str]
    value: Any
    zones: List[str]


@dataclass
class ComplianceEvaluation:
    """Result of evaluating a component against a rule."""
    component_id: str
    component_type: str
    component_name: str
    rule_id: str
    section_id: Optional[str]
    section_title: Optional[str]
    requirement: str
    topic: Optional[str]
    expected_value: Any
    actual_value: Any
    status: str  # PASS, FAIL, REVIEW, NOT_APPLICABLE, NO_APPLICABLE_RULES
    confidence: float
    notes: List[str]
    zones: List[str]
    source: str


# =============================================================================
# Component Type Mapping
# =============================================================================

COMPONENT_TYPE_KEYWORDS = {
    "room": ["bedroom", "bathroom", "kitchen", "living", "dining", "garage", "laundry"],
    "setback": ["setback", "boundary", "property line", "clearance"],
    "opening": ["door", "window", "opening", "egress", "exit"],
    "parking": ["parking", "garage", "carport", "driveway"],
    "stair": ["stair", "ramp", "elevator", "circulation"],
    "fire_safety": ["fire", "smoke", "sprinkler", "alarm", "extinguisher"],
    "accessibility": ["accessible", "ada", "disability", "handicap"],
    "height": ["height", "ceiling", "elevation", "level"],
    "envelope": ["building", "footprint", "area", "coverage", "far"],
    # Site plan components
    "lot": ["lot", "parcel", "site", "lot size", "lot area", "minimum lot"],
    "water": ["water", "creek", "river", "stream", "pond", "lake", "riparian", "waterway"],
    "adjacent": ["adjacent", "neighboring", "adjoining property"]
}


# =============================================================================
# Database Connections
# =============================================================================

def get_neo4j_driver() -> Any:
    """Connect to Neo4j database."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")

    missing = [k for k, v in {"NEO4J_URI": uri, "NEO4J_USER": user, "NEO4J_PASSWORD": pwd}.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing Neo4j environment vars: {', '.join(missing)}")

    return GraphDatabase.driver(uri, auth=(user, pwd))


def get_pinecone_client() -> Optional[Pinecone]:
    """Connect to Pinecone vector database."""
    key = os.getenv("PINECONE_API_KEY")
    if not key:
        log("Warning: PINECONE_API_KEY not set, skipping Pinecone queries")
        return None
    return Pinecone(api_key=key)


def get_openai_client() -> Optional[OpenAI]:
    """Connect to OpenAI for embeddings."""
    key = os.getenv("OPENAI_API_KEY")
    if not key or OpenAI is None:
        log("Warning: OPENAI_API_KEY not set, embeddings disabled")
        return None
    return OpenAI(api_key=key)


# =============================================================================
# LLM Relevance Check
# =============================================================================

def check_rule_relevance(
    component_type: str,
    component_data: Dict[str, Any],
    rule: RuleDetail,
    openai_client: Optional[OpenAI]
) -> tuple[bool, float, str]:
    """
    Use LLM to determine if a rule is actually relevant to a component.

    Returns:
        (is_relevant, confidence, reasoning)
    """
    if not openai_client:
        # Without LLM, assume all retrieved rules are relevant
        return (True, 0.5, "LLM unavailable, defaulting to relevant")

    # Build component description
    component_desc = f"{component_type}: {component_data.get('name', 'unnamed')}"
    if component_type == "room":
        if component_data.get("area"):
            component_desc += f", area={component_data['area']} sq ft"
        if component_data.get("room_type"):
            component_desc += f", type={component_data['room_type']}"
    elif component_type in ["setback", "geometric_setback"]:
        component_desc += f", direction={component_data.get('direction', 'unknown')}"
        component_desc += f", distance={component_data.get('avg_distance', component_data.get('distance', 'unknown'))} units"
    elif component_type == "opening":
        component_desc += f", type={component_data.get('opening_type', 'unknown')}"
        component_desc += f", width={component_data.get('width', 'unknown')} ft"
        if component_data.get("is_egress"):
            component_desc += ", egress=true"
    elif component_type == "parking":
        component_desc += f", type={component_data.get('space_type', 'unknown')}"
        component_desc += f", dimensions={component_data.get('width', '?')}x{component_data.get('length', '?')} ft"

    # Build rule description
    rule_desc = f"Rule {rule.rule_id}: {rule.requirement}"
    if rule.topic:
        rule_desc += f" (Topic: {rule.topic})"

    # Create prompt
    prompt = f"""You are a building code compliance expert. Determine if the following building code rule is applicable and relevant to check against the given building component.

Component:
{component_desc}

Rule:
{rule_desc}

Question: Is this rule actually applicable and relevant for checking this specific component?

Consider:
- Does the rule's requirement logically apply to this type of component?
- Is the rule about something this component can actually satisfy or violate?
- Would a human building plan reviewer check this component against this rule?

Examples of IRRELEVANT matches:
- Checking a "window" against "open space network connectivity"
- Checking a "living room" against "riparian wetland setbacks" (unless property is near water)
- Checking a "door" against "temporary entertainment events"

Examples of RELEVANT matches:
- Checking a "bedroom" against "minimum room area requirements"
- Checking a "setback" against "boundary clearance requirements"
- Checking an "egress door" against "minimum door width requirements"

Respond in JSON format:
{{
  "relevant": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200
        )

        result_text = response.choices[0].message.content.strip()

        # Try to parse JSON response
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return (
                result.get("relevant", False),
                result.get("confidence", 0.5),
                result.get("reasoning", "No reasoning provided")
            )
        else:
            # Fallback: check if response contains "relevant" or "not relevant"
            is_relevant = "relevant" in result_text.lower() and "not relevant" not in result_text.lower()
            return (is_relevant, 0.5, result_text[:200])

    except Exception as exc:
        log(f"LLM relevance check error: {exc}")
        # On error, default to relevant to avoid filtering out valid rules
        return (True, 0.3, f"LLM error: {str(exc)[:100]}")


# =============================================================================
# Embedding & Vector Search
# =============================================================================

def embed_text(openai_client: Optional[OpenAI], text: str, cache: Dict[str, List[float]],
               model: str = "text-embedding-3-small") -> Optional[List[float]]:
    """Generate embedding for text using OpenAI."""
    if not openai_client:
        return None

    key = (model, text)
    if key in cache:
        return cache[key]

    try:
        result = openai_client.embeddings.create(input=text, model=model)
        embedding = result.data[0].embedding
        cache[key] = embedding
        return embedding
    except Exception as exc:
        log(f"Embedding error: {exc}")
        return None


def cosine_sim(a: Sequence[float], b: Sequence[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_vec, b_vec = np.array(a), np.array(b)
    denom = (np.linalg.norm(a_vec) * np.linalg.norm(b_vec)) + 1e-9
    return float(np.dot(a_vec, b_vec) / denom)


def query_pinecone_for_component(
    component_type: str,
    component_data: Dict[str, Any],
    pinecone_client: Pinecone,
    openai_client: Optional[OpenAI],
    index_name: str,
    top_k: int,
    embed_cache: Dict[str, List[float]]
) -> List[RuleCandidate]:
    """Query Pinecone for relevant rules for a component."""
    if not pinecone_client or not openai_client:
        return []

    # Build query text from component
    query_parts = [component_type, component_data.get("name", "")]
    if component_type == "room":
        query_parts.append(f"area {component_data.get('area', '')} sq ft")
    elif component_type in ["setback", "geometric_setback"]:
        query_parts.append(f"{component_data.get('direction', '')} setback")

    query_text = " ".join(str(p) for p in query_parts if p)

    # Generate embedding
    embedding = embed_text(openai_client, query_text, embed_cache)
    if not embedding:
        return []

    # Query Pinecone
    try:
        idx = pinecone_client.Index(index_name)
        response = idx.query(vector=embedding, top_k=top_k, include_metadata=True)
    except Exception as exc:
        log(f"Pinecone query failed: {exc}")
        return []

    # Parse results
    candidates = []
    for match in response.get("matches", []):
        metadata = match.get("metadata") or {}
        rule_id = metadata.get("rule_id") or metadata.get("id") or match.get("id")
        if rule_id:
            candidates.append(RuleCandidate(
                rule_id=str(rule_id),
                source="pinecone",
                score=float(match.get("score", 0.0)),
                metadata=metadata
            ))

    return candidates


# =============================================================================
# Neo4j Rule Queries
# =============================================================================

def search_rules_by_keywords(
    driver: Any,
    component_type: str,
    keywords: Sequence[str],
    limit: int = 3
) -> List[str]:
    """Search Neo4j for rules matching keywords."""
    # Build keyword list
    type_keywords = COMPONENT_TYPE_KEYWORDS.get(component_type, [])
    all_keywords = list(set([kw.upper() for kw in keywords] + [kw.upper() for kw in type_keywords]))

    if not all_keywords:
        return []

    query = """
    WITH $keywords AS keywords
    MATCH (r:Rule)
    WHERE any(kw IN keywords WHERE
        kw <> '' AND (
            toUpper(coalesce(r.requirement,'')) CONTAINS kw OR
            toUpper(coalesce(r.topic,'')) CONTAINS kw OR
            toUpper(coalesce(r.section_title,'')) CONTAINS kw OR
            toUpper(coalesce(r.attribute,'')) CONTAINS kw
        )
    )
    RETURN DISTINCT r.id AS rule_id
    LIMIT $limit
    """

    with driver.session() as session:
        rows = session.run(query, keywords=all_keywords, limit=limit)
        return [row["rule_id"] for row in rows if row.get("rule_id")]


def fetch_rules_by_ids(driver: Any, rule_ids: Sequence[str]) -> Dict[str, RuleDetail]:
    """Fetch full rule details from Neo4j by rule IDs."""
    if not rule_ids:
        return {}

    query = """
    MATCH (r:Rule)
    WHERE r.id IN $ids
    OPTIONAL MATCH (r)-[:APPLIES_TO]->(z:Zone)
    RETURN r.id AS rule_id,
           r.section_id AS section_id,
           r.section_title AS section_title,
           r.requirement AS requirement,
           r.topic AS topic,
           r.attribute AS attribute,
           r.value AS value,
           collect(DISTINCT z.name) AS zones
    """

    details = {}
    with driver.session() as session:
        result = session.run(query, ids=list(rule_ids))
        for row in result:
            rid = row.get("rule_id")
            if rid:
                details[rid] = RuleDetail(
                    rule_id=rid,
                    section_id=row.get("section_id"),
                    section_title=row.get("section_title"),
                    requirement=row.get("requirement"),
                    topic=row.get("topic"),
                    attribute=row.get("attribute"),
                    value=row.get("value"),
                    zones=[z for z in row.get("zones") or [] if z]
                )

    return details


# =============================================================================
# Component-Specific Evaluation Logic
# =============================================================================

def evaluate_room_component(
    component: Dict[str, Any],
    rule: RuleDetail,
    candidate: RuleCandidate
) -> Optional[ComplianceEvaluation]:
    """Evaluate a room component against a rule."""
    room_type = component.get("room_type", "")
    area = component.get("area")
    width = component.get("width")
    length = component.get("length")

    # Check if rule applies to this room type
    requirement_upper = (rule.requirement or "").upper()
    if room_type.upper() not in requirement_upper and "BEDROOM" not in requirement_upper:
        return None  # Rule doesn't apply

    # Extract expected value from rule
    expected_value = rule.value
    attribute = (rule.attribute or "").lower()

    # Determine what to check
    actual_value = None
    status = "REVIEW"
    notes = []

    if "area" in attribute or "size" in attribute:
        actual_value = area
        if area and expected_value:
            try:
                min_area = float(expected_value)
                if area >= min_area:
                    status = "PASS"
                    notes.append(f"Room area {area} sq ft meets minimum {min_area} sq ft")
                else:
                    status = "FAIL"
                    notes.append(f"Room area {area} sq ft below minimum {min_area} sq ft")
            except (ValueError, TypeError):
                notes.append("Could not parse minimum area requirement")

    elif "dimension" in attribute or "width" in attribute:
        actual_value = width or length
        if actual_value and expected_value:
            try:
                min_dim = float(expected_value)
                if actual_value >= min_dim:
                    status = "PASS"
                    notes.append(f"Dimension {actual_value} ft meets minimum {min_dim} ft")
                else:
                    status = "FAIL"
                    notes.append(f"Dimension {actual_value} ft below minimum {min_dim} ft")
            except (ValueError, TypeError):
                notes.append("Could not parse minimum dimension requirement")

    else:
        notes.append("Rule attribute not directly measurable from extracted data")

    return ComplianceEvaluation(
        component_id=f"room_{component.get('name', 'unknown')}",
        component_type="room",
        component_name=component.get("name", ""),
        rule_id=rule.rule_id,
        section_id=rule.section_id,
        section_title=rule.section_title,
        requirement=rule.requirement or "",
        topic=rule.topic,
        expected_value=expected_value,
        actual_value=actual_value,
        status=status,
        confidence=candidate.score or 0.5,
        notes=notes,
        zones=rule.zones,
        source=candidate.source
    )


def evaluate_setback_component(
    component: Dict[str, Any],
    rule: RuleDetail,
    candidate: RuleCandidate,
    is_geometric: bool = False
) -> Optional[ComplianceEvaluation]:
    """Evaluate a setback component against a rule."""
    direction = component.get("direction", "unknown")
    distance = component.get("avg_distance" if is_geometric else "distance")

    # Check if rule applies to this setback direction
    requirement_upper = (rule.requirement or "").upper()
    direction_upper = direction.upper()

    # Match direction
    if "FRONT" in direction_upper and "FRONT" not in requirement_upper:
        if "SIDE" not in requirement_upper and "REAR" not in requirement_upper:
            return None

    # Extract minimum setback from rule
    expected_value = rule.value
    status = "REVIEW"
    notes = []

    if distance is not None and expected_value:
        try:
            min_setback = float(expected_value)
            if distance >= min_setback:
                status = "PASS"
                notes.append(f"{direction} setback {distance:.1f} ft meets minimum {min_setback} ft")
            else:
                status = "FAIL"
                notes.append(f"{direction} setback {distance:.1f} ft below minimum {min_setback} ft")
        except (ValueError, TypeError):
            notes.append("Could not parse minimum setback requirement")
    else:
        notes.append("Setback distance or requirement value missing")

    source_type = "geometric_setback" if is_geometric else "annotated_setback"

    return ComplianceEvaluation(
        component_id=f"setback_{direction}",
        component_type=source_type,
        component_name=f"{direction} setback",
        rule_id=rule.rule_id,
        section_id=rule.section_id,
        section_title=rule.section_title,
        requirement=rule.requirement or "",
        topic=rule.topic,
        expected_value=expected_value,
        actual_value=distance,
        status=status,
        confidence=candidate.score or 0.7,
        notes=notes,
        zones=rule.zones,
        source=candidate.source
    )


def evaluate_opening_component(
    component: Dict[str, Any],
    rule: RuleDetail,
    candidate: RuleCandidate
) -> Optional[ComplianceEvaluation]:
    """Evaluate an opening (door/window) against a rule."""
    opening_type = component.get("opening_type", "")
    width = component.get("width")
    is_egress = component.get("is_egress", False)

    requirement_upper = (rule.requirement or "").upper()

    # Check if rule applies
    if opening_type == "door" and "DOOR" not in requirement_upper:
        return None
    if is_egress and "EGRESS" not in requirement_upper and "EXIT" not in requirement_upper:
        return None

    expected_value = rule.value
    status = "REVIEW"
    notes = []

    if width is not None and expected_value:
        try:
            min_width = float(expected_value)
            if width >= min_width:
                status = "PASS"
                notes.append(f"{opening_type} width {width} ft meets minimum {min_width} ft")
            else:
                status = "FAIL"
                notes.append(f"{opening_type} width {width} ft below minimum {min_width} ft")
        except (ValueError, TypeError):
            notes.append("Could not parse minimum width requirement")

    return ComplianceEvaluation(
        component_id=f"opening_{opening_type}_{component.get('location', ['0','0'])[0]}",
        component_type="opening",
        component_name=f"{opening_type} {'(egress)' if is_egress else ''}",
        rule_id=rule.rule_id,
        section_id=rule.section_id,
        section_title=rule.section_title,
        requirement=rule.requirement or "",
        topic=rule.topic,
        expected_value=expected_value,
        actual_value=width,
        status=status,
        confidence=candidate.score or 0.6,
        notes=notes,
        zones=rule.zones,
        source=candidate.source
    )


def evaluate_parking_component(
    component: Dict[str, Any],
    rule: RuleDetail,
    candidate: RuleCandidate
) -> Optional[ComplianceEvaluation]:
    """Evaluate a parking space against a rule."""
    width = component.get("width")
    length = component.get("length")
    accessible = component.get("accessible", False)

    requirement_upper = (rule.requirement or "").upper()

    # Check if rule applies to accessible parking
    if accessible and "ACCESSIBLE" not in requirement_upper and "ADA" not in requirement_upper:
        return None

    expected_value = rule.value
    attribute = (rule.attribute or "").lower()
    status = "REVIEW"
    notes = []

    if "width" in attribute and width is not None and expected_value:
        try:
            min_width = float(expected_value)
            if width >= min_width:
                status = "PASS"
                notes.append(f"Parking width {width} ft meets minimum {min_width} ft")
            else:
                status = "FAIL"
                notes.append(f"Parking width {width} ft below minimum {min_width} ft")
        except (ValueError, TypeError):
            notes.append("Could not parse minimum width")

    elif "length" in attribute and length is not None and expected_value:
        try:
            min_length = float(expected_value)
            if length >= min_length:
                status = "PASS"
                notes.append(f"Parking length {length} ft meets minimum {min_length} ft")
            else:
                status = "FAIL"
                notes.append(f"Parking length {length} ft below minimum {min_length} ft")
        except (ValueError, TypeError):
            notes.append("Could not parse minimum length")

    return ComplianceEvaluation(
        component_id=f"parking_{component.get('space_type', 'unknown')}",
        component_type="parking",
        component_name=f"{component.get('space_type', '')} {'(accessible)' if accessible else ''}",
        rule_id=rule.rule_id,
        section_id=rule.section_id,
        section_title=rule.section_title,
        requirement=rule.requirement or "",
        topic=rule.topic,
        expected_value=expected_value,
        actual_value={"width": width, "length": length},
        status=status,
        confidence=candidate.score or 0.6,
        notes=notes,
        zones=rule.zones,
        source=candidate.source
    )


def evaluate_lot_info_component(
    component: Dict[str, Any],
    rule: RuleDetail,
    candidate: RuleCandidate
) -> Optional[ComplianceEvaluation]:
    """Evaluate lot information against a rule."""
    lot_number = component.get("lot_number")
    lot_area = component.get("lot_area")
    lot_area_unit = component.get("lot_area_unit", "m²")
    boundary_dims = component.get("boundary_dimensions", [])

    expected_value = rule.value
    attribute = (rule.attribute or "").lower()
    requirement_upper = (rule.requirement or "").upper()
    status = "REVIEW"
    notes = []

    # Check minimum lot size requirements
    if "area" in attribute or "SIZE" in requirement_upper:
        if lot_area and expected_value:
            try:
                min_area = float(expected_value)
                if lot_area >= min_area:
                    status = "PASS"
                    notes.append(f"Lot area {lot_area} {lot_area_unit} meets minimum {min_area} {lot_area_unit}")
                else:
                    status = "FAIL"
                    notes.append(f"Lot area {lot_area} {lot_area_unit} below minimum {min_area} {lot_area_unit}")
            except (ValueError, TypeError):
                notes.append("Could not parse minimum area requirement")
        else:
            notes.append("Lot area not specified on plan")

    return ComplianceEvaluation(
        component_id=f"lot_{lot_number or 'unknown'}",
        component_type="lot_info",
        component_name=f"Lot {lot_number}" if lot_number else "Site Lot",
        rule_id=rule.rule_id,
        section_id=rule.section_id,
        section_title=rule.section_title,
        requirement=rule.requirement or "",
        topic=rule.topic,
        expected_value=expected_value,
        actual_value={"area": lot_area, "unit": lot_area_unit, "dimensions_count": len(boundary_dims)},
        status=status,
        confidence=candidate.score or 0.6,
        notes=notes,
        zones=rule.zones,
        source=candidate.source
    )


def evaluate_water_feature_component(
    component: Dict[str, Any],
    rule: RuleDetail,
    candidate: RuleCandidate
) -> Optional[ComplianceEvaluation]:
    """Evaluate water feature compliance (e.g., setbacks from creeks)."""
    feature_type = component.get("feature_type", "")
    feature_name = component.get("name", "")

    requirement_upper = (rule.requirement or "").upper()
    expected_value = rule.value
    status = "REVIEW"
    notes = []

    # Check if this rule applies to this type of water feature
    if "CREEK" in requirement_upper and feature_type != "creek":
        return None
    if "RIVER" in requirement_upper and feature_type != "river":
        return None

    # Water feature rules typically require manual review for environmental compliance
    notes.append(f"{feature_type.title()} '{feature_name}' identified on plan")
    notes.append("Environmental regulations and setback requirements should be verified")

    return ComplianceEvaluation(
        component_id=f"water_{feature_type}_{feature_name.replace(' ', '_')}",
        component_type="water_feature",
        component_name=feature_name,
        rule_id=rule.rule_id,
        section_id=rule.section_id,
        section_title=rule.section_title,
        requirement=rule.requirement or "",
        topic=rule.topic,
        expected_value=expected_value,
        actual_value={"type": feature_type, "name": feature_name},
        status=status,
        confidence=candidate.score or 0.5,
        notes=notes,
        zones=rule.zones,
        source=candidate.source
    )


# =============================================================================
# Main Processing Logic
# =============================================================================

def process_components(
    components_data: Dict[str, Any],
    driver: Any,
    pinecone_client: Optional[Pinecone],
    openai_client: Optional[OpenAI],
    pinecone_index: str,
    top_k: int
) -> List[ComplianceEvaluation]:
    """Process all components and evaluate against rules."""
    evaluations = []
    embed_cache = {}

    for sheet in components_data.get("sheets", []):
        sheet_num = sheet.get("sheet_number", 1)

        # Process rooms
        for room in tqdm(sheet.get("rooms", []), desc=f"Sheet {sheet_num} - Rooms"):
            candidates = []

            # Query Pinecone
            if pinecone_client:
                candidates.extend(query_pinecone_for_component(
                    "room", room, pinecone_client, openai_client,
                    pinecone_index, top_k, embed_cache
                ))

            # Query Neo4j by keywords
            keywords = [room.get("room_type", ""), room.get("name", "")]
            neo4j_rules = search_rules_by_keywords(driver, "room", keywords, limit=top_k)
            for rid in neo4j_rules:
                if rid not in {c.rule_id for c in candidates}:
                    candidates.append(RuleCandidate(rule_id=rid, source="neo4j_keyword"))

            # Fetch rule details and evaluate
            if candidates:
                rule_ids = [c.rule_id for c in candidates]
                rules = fetch_rules_by_ids(driver, rule_ids)

                for candidate in candidates:
                    if candidate.rule_id in rules:
                        rule = rules[candidate.rule_id]

                        # Check relevance with LLM
                        is_relevant, relevance_conf, reasoning = check_rule_relevance(
                            "room", room, rule, openai_client
                        )

                        if not is_relevant:
                            log(f"  Filtered irrelevant rule {rule.rule_id} for room {room.get('name')}: {reasoning}")
                            continue

                        eval_result = evaluate_room_component(room, rule, candidate)
                        if eval_result:
                            evaluations.append(eval_result)

        # Process geometric setbacks
        for setback in tqdm(sheet.get("geometric_setbacks", []), desc=f"Sheet {sheet_num} - Setbacks"):
            candidates = []

            # Query Pinecone
            if pinecone_client:
                candidates.extend(query_pinecone_for_component(
                    "setback", setback, pinecone_client, openai_client,
                    pinecone_index, top_k, embed_cache
                ))

            # Query Neo4j
            keywords = ["setback", setback.get("direction", "")]
            neo4j_rules = search_rules_by_keywords(driver, "setback", keywords, limit=top_k)
            for rid in neo4j_rules:
                if rid not in {c.rule_id for c in candidates}:
                    candidates.append(RuleCandidate(rule_id=rid, source="neo4j_keyword"))

            # Evaluate
            if candidates:
                rules = fetch_rules_by_ids(driver, [c.rule_id for c in candidates])
                for candidate in candidates:
                    if candidate.rule_id in rules:
                        rule = rules[candidate.rule_id]

                        # Check relevance
                        is_relevant, relevance_conf, reasoning = check_rule_relevance(
                            "geometric_setback", setback, rule, openai_client
                        )

                        if not is_relevant:
                            log(f"  Filtered irrelevant rule {rule.rule_id} for setback {setback.get('direction')}: {reasoning}")
                            continue

                        eval_result = evaluate_setback_component(setback, rule, candidate, is_geometric=True)
                        if eval_result:
                            evaluations.append(eval_result)

        # Process openings
        for opening in tqdm(sheet.get("openings", []), desc=f"Sheet {sheet_num} - Openings"):
            candidates = []

            if pinecone_client:
                candidates.extend(query_pinecone_for_component(
                    "opening", opening, pinecone_client, openai_client,
                    pinecone_index, top_k, embed_cache
                ))

            keywords = [opening.get("opening_type", ""), "egress" if opening.get("is_egress") else ""]
            neo4j_rules = search_rules_by_keywords(driver, "opening", keywords, limit=top_k)
            for rid in neo4j_rules:
                if rid not in {c.rule_id for c in candidates}:
                    candidates.append(RuleCandidate(rule_id=rid, source="neo4j_keyword"))

            if candidates:
                rules = fetch_rules_by_ids(driver, [c.rule_id for c in candidates])
                for candidate in candidates:
                    if candidate.rule_id in rules:
                        rule = rules[candidate.rule_id]

                        # Check relevance
                        is_relevant, relevance_conf, reasoning = check_rule_relevance(
                            "opening", opening, rule, openai_client
                        )

                        if not is_relevant:
                            log(f"  Filtered irrelevant rule {rule.rule_id} for opening {opening.get('opening_type')}: {reasoning}")
                            continue

                        eval_result = evaluate_opening_component(opening, rule, candidate)
                        if eval_result:
                            evaluations.append(eval_result)

        # Process parking
        for parking in tqdm(sheet.get("parking", []), desc=f"Sheet {sheet_num} - Parking"):
            candidates = []

            if pinecone_client:
                candidates.extend(query_pinecone_for_component(
                    "parking", parking, pinecone_client, openai_client,
                    pinecone_index, top_k, embed_cache
                ))

            keywords = ["parking", parking.get("space_type", ""), "accessible" if parking.get("accessible") else ""]
            neo4j_rules = search_rules_by_keywords(driver, "parking", keywords, limit=top_k)
            for rid in neo4j_rules:
                if rid not in {c.rule_id for c in candidates}:
                    candidates.append(RuleCandidate(rule_id=rid, source="neo4j_keyword"))

            if candidates:
                rules = fetch_rules_by_ids(driver, [c.rule_id for c in candidates])
                for candidate in candidates:
                    if candidate.rule_id in rules:
                        rule = rules[candidate.rule_id]

                        # Check relevance
                        is_relevant, relevance_conf, reasoning = check_rule_relevance(
                            "parking", parking, rule, openai_client
                        )

                        if not is_relevant:
                            log(f"  Filtered irrelevant rule {rule.rule_id} for parking: {reasoning}")
                            continue

                        eval_result = evaluate_parking_component(parking, rule, candidate)
                        if eval_result:
                            evaluations.append(eval_result)

        # Process lot information
        lot_info = sheet.get("lot_info")
        if lot_info:
            candidates = []

            if pinecone_client:
                candidates.extend(query_pinecone_for_component(
                    "lot_info", lot_info, pinecone_client, openai_client,
                    pinecone_index, top_k, embed_cache
                ))

            keywords = ["lot", "site", "parcel", "area", "minimum lot size"]
            neo4j_rules = search_rules_by_keywords(driver, "lot", keywords, limit=top_k)
            for rid in neo4j_rules:
                if rid not in {c.rule_id for c in candidates}:
                    candidates.append(RuleCandidate(rule_id=rid, source="neo4j_keyword"))

            if candidates:
                rules = fetch_rules_by_ids(driver, [c.rule_id for c in candidates])
                for candidate in candidates:
                    if candidate.rule_id in rules:
                        rule = rules[candidate.rule_id]

                        is_relevant, relevance_conf, reasoning = check_rule_relevance(
                            "lot_info", lot_info, rule, openai_client
                        )

                        if not is_relevant:
                            log(f"  Filtered irrelevant rule {rule.rule_id} for lot info: {reasoning}")
                            continue

                        eval_result = evaluate_lot_info_component(lot_info, rule, candidate)
                        if eval_result:
                            evaluations.append(eval_result)

        # Process water features
        for water_feature in sheet.get("water_features", []):
            candidates = []

            if pinecone_client:
                candidates.extend(query_pinecone_for_component(
                    "water_feature", water_feature, pinecone_client, openai_client,
                    pinecone_index, top_k, embed_cache
                ))

            keywords = ["water", "creek", "river", "stream", "setback", "riparian", "environmental"]
            neo4j_rules = search_rules_by_keywords(driver, "water", keywords, limit=top_k)
            for rid in neo4j_rules:
                if rid not in {c.rule_id for c in candidates}:
                    candidates.append(RuleCandidate(rule_id=rid, source="neo4j_keyword"))

            if candidates:
                rules = fetch_rules_by_ids(driver, [c.rule_id for c in candidates])
                for candidate in candidates:
                    if candidate.rule_id in rules:
                        rule = rules[candidate.rule_id]

                        is_relevant, relevance_conf, reasoning = check_rule_relevance(
                            "water_feature", water_feature, rule, openai_client
                        )

                        if not is_relevant:
                            log(f"  Filtered irrelevant rule {rule.rule_id} for water feature: {reasoning}")
                            continue

                        eval_result = evaluate_water_feature_component(water_feature, rule, candidate)
                        if eval_result:
                            evaluations.append(eval_result)

    return evaluations


# =============================================================================
# Output Generation
# =============================================================================

def build_compliance_report(
    plan_name: str,
    evaluations: List[ComplianceEvaluation]
) -> Dict[str, Any]:
    """Build the compliance report JSON."""
    status_counts = defaultdict(int)
    for eval in evaluations:
        status_counts[eval.status] += 1

    # Serialize evaluations
    eval_dicts = []
    for eval in evaluations:
        eval_dicts.append({
            "component_id": eval.component_id,
            "component_type": eval.component_type,
            "component_name": eval.component_name,
            "rule_id": eval.rule_id,
            "section_id": eval.section_id,
            "section_title": eval.section_title,
            "requirement": eval.requirement,
            "topic": eval.topic,
            "expected_value": eval.expected_value,
            "actual_value": eval.actual_value,
            "status": eval.status,
            "confidence": round(eval.confidence, 3),
            "notes": eval.notes,
            "zones": eval.zones,
            "source": eval.source
        })

    return {
        "plan_name": plan_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_evaluations": len(evaluations),
            "status_breakdown": dict(status_counts),
            "pass_rate": round(status_counts["PASS"] / len(evaluations) * 100, 1) if evaluations else 0
        },
        "evaluations": eval_dicts
    }


# =============================================================================
# CLI Entry Point
# =============================================================================

def load_environment() -> None:
    """Load environment variables from .env file."""
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"

    if load_dotenv and env_path.exists():
        load_dotenv(env_path)
        log(f"Loaded environment from {env_path}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Component-based compliance checking")
    parser.add_argument("--components", required=True, help="Path to components JSON")
    parser.add_argument("--pinecone-index", default=os.getenv("PINECONE_INDEX", "planning-rules"))
    parser.add_argument("--top-k", type=int, default=2, help="Top rules per component")
    parser.add_argument("--output", help="Output path for compliance JSON")
    parser.add_argument("--writeback", action="store_true", help="Write results to Neo4j")
    return parser.parse_args()


def main():
    """Main execution."""
    args = parse_args()
    load_environment()

    # Load components
    components_path = Path(args.components)
    if not components_path.exists():
        raise FileNotFoundError(f"Components file not found: {components_path}")

    log(f"Loading components from {components_path.name}...")
    with components_path.open() as f:
        components_data = json.load(f)

    plan_name = components_data.get("pdf_name", components_path.stem)

    # Initialize connections
    log("Connecting to databases...")
    driver = get_neo4j_driver()
    pinecone_client = get_pinecone_client()
    openai_client = get_openai_client()

    if not pinecone_client:
        log("⚠️  Proceeding with Neo4j keyword search only (no Pinecone)")

    # Process components
    log("Evaluating components against rules...")
    evaluations = process_components(
        components_data,
        driver,
        pinecone_client,
        openai_client,
        args.pinecone_index,
        args.top_k
    )

    # Build report
    log("Building compliance report...")
    report = build_compliance_report(plan_name, evaluations)

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = components_path.with_name(components_path.stem.replace("_components", "_compliance.json"))

    with output_path.open("w") as f:
        json.dump(report, f, indent=2)

    log(f"✅ Compliance report saved to {output_path}")
    log(f"\nSummary:")
    log(f"  Total Evaluations: {report['summary']['total_evaluations']}")
    log(f"  Status Breakdown: {report['summary']['status_breakdown']}")
    log(f"  Pass Rate: {report['summary']['pass_rate']}%")

    driver.close()


if __name__ == "__main__":
    main()

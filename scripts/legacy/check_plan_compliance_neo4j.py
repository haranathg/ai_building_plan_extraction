"""
check_plan_compliance_neo4j.py
-------------------------------
Analyse an extracted plan JSON, identify key plan components, retrieve
relevant rules from Pinecone + Neo4j, and synthesise compliance judgements.

Usage:
    python3 scripts/check_plan_compliance_neo4j.py \
        --plan data/House-Floor-Plans-vector_output.json \
        --writeback

Optional flags:
    --pinecone-index planning-rules  # override index name
    --top-k 5                        # candidates per component
    --max-components 12              # cap components evaluated

Output:
    Writes <plan>_compliance.json with component-by-component findings.
    Optionally writes plan → rule relationships back into Neo4j.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from neo4j import GraphDatabase
from pinecone import Pinecone
from tqdm import tqdm

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


# -------------------------------------------------------------
# Logging helper
# -------------------------------------------------------------
def log(msg: str) -> None:
    print(f"[INFO] {msg}")


# -------------------------------------------------------------
# Data models
# -------------------------------------------------------------
@dataclass
class Component:
    component_id: str
    name: str
    sheet_number: int
    matched_keyword: str
    context: str
    raw_text: str
    embedding: Optional[List[float]] = None
    candidate_rules: List["RuleCandidate"] = field(default_factory=list)


@dataclass
class RuleCandidate:
    rule_id: str
    source: str
    pinecone_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleDetail:
    rule_id: str
    section_id: Optional[str]
    section_title: Optional[str]
    requirement: Optional[str]
    topic: Optional[str]
    attribute: Optional[str]
    value: Any
    zones: List[str]


# -------------------------------------------------------------
# Connections
# -------------------------------------------------------------
def get_neo4j_driver() -> Any:
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")
    missing = [k for k, v in {"NEO4J_URI": uri, "NEO4J_USER": user, "NEO4J_PASSWORD": pwd}.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required Neo4j environment vars: {', '.join(missing)}")
    return GraphDatabase.driver(uri, auth=(user, pwd))


def get_pinecone_client() -> Optional[Pinecone]:
    key = os.getenv("PINECONE_API_KEY")
    if not key:
        return None
    return Pinecone(api_key=key)


def get_openai_client() -> Optional[OpenAI]:
    key = os.getenv("OPENAI_API_KEY")
    if not key or OpenAI is None:
        return None
    return OpenAI(api_key=key)


# -------------------------------------------------------------
# Utility helpers
# -------------------------------------------------------------
COMPONENT_PATTERNS: Sequence[Tuple[str, Sequence[str]]] = [
    ("Bedroom", ("BEDROOM", "BED", "MASTER SUITE")),
    ("Bathroom", ("BATH", "ENSUITE", "SHOWER", "WC")),
    ("Kitchen", ("KITCHEN", "PANTRY", "COOK", "CHEF")),
    ("Dining", ("DINING", "MEALS", "BREAKFAST")),
    ("Living Area", ("LIVING", "FAMILY", "LOUNGE", "MEDIA")),
    ("Garage", ("GARAGE", "CARPORT", "CAR SPACE")),
    ("Laundry", ("LAUNDRY", "LINEN", "UTILITY")),
    ("Balcony / Deck", ("BALCONY", "DECK", "PORCH", "VERANDAH", "PATIO")),
    ("Stairs / Exit", ("STAIR", "EXIT", "EGRESS", "RAMP")),
    ("Fire Safety", ("FIRE", "HYDRANT", "SPRINKLER", "ALARM", "SMOKE")),
    ("Accessibility", ("ACCESS", "DISABILITY", "ACCESSIBLE", "AS1428")),
    ("Parking & Driveway", ("PARKING", "DRIVEWAY", "CAR", "GAR")),
    ("Structural", ("BEAM", "COLUMN", "LOAD", "STRUCTURE")),
    ("Setbacks / Envelope", ("SETBACK", "BOUNDARY", "EASEMENT")),
    ("Height & Levels", ("HEIGHT", "LEVEL", "RL", "FLOOR LEVEL")),
    ("Outdoor / Landscaping", ("LANDSCAPE", "YARD", "GARDEN")),
    ("Energy / Services", ("SOLAR", "HVAC", "MECHANICAL", "ELECTRICAL")),
]


def sanitize_text(text: str, max_len: int = 600) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 3] + "..."


def create_context(text: str, start: int, match_len: int, window: int = 220) -> str:
    if not text:
        return ""
    begin = max(0, start - window)
    end = min(len(text), start + match_len + window)
    return sanitize_text(text[begin:end], max_len=600)


def extract_plan_components(plan_data: Dict[str, Any], max_components: int = 12) -> List[Component]:
    components: List[Component] = []
    for sheet in plan_data.get("sheets", []):
        words = [blk["text"] for blk in sheet.get("text_blocks", []) if blk.get("text")]
        if not words:
            continue
        joined_original = " ".join(words)
        joined_upper = joined_original.upper()
        sheet_num = sheet.get("page_number", 0)

        seen_for_sheet: set[str] = set()
        for name, keywords in COMPONENT_PATTERNS:
            if len(components) >= max_components:
                break
            if name in seen_for_sheet:
                continue
            for keyword in keywords:
                pos = joined_upper.find(keyword)
                if pos == -1:
                    continue
                context = create_context(joined_original, pos, len(keyword))
                comp_id = f"sheet{sheet_num}_{name.replace(' ', '_').lower()}_{len(components)}"
                components.append(
                    Component(
                        component_id=comp_id,
                        name=name,
                        sheet_number=sheet_num,
                        matched_keyword=keyword,
                        context=context,
                        raw_text=joined_original,
                    )
                )
                seen_for_sheet.add(name)
                break  # stop scanning keywords for this component

    if not components and plan_data.get("sheets"):
        # Fallback: provide a generic sheet overview so downstream still works.
        for sheet in plan_data["sheets"][: max_components]:
            words = [blk["text"] for blk in sheet.get("text_blocks", []) if blk.get("text")]
            joined = " ".join(words)
            comp_id = f"sheet{sheet.get('page_number', 0)}_overview"
            components.append(
                Component(
                    component_id=comp_id,
                    name=f"Sheet {sheet.get('page_number', 0)} Overview",
                    sheet_number=sheet.get("page_number", 0),
                    matched_keyword="GENERAL",
                    context=sanitize_text(joined),
                    raw_text=joined,
                )
            )
    return components[:max_components]


def cosine_sim(a: Sequence[float], b: Sequence[float]) -> float:
    a_vec, b_vec = np.array(a), np.array(b)
    denom = (np.linalg.norm(a_vec) * np.linalg.norm(b_vec)) + 1e-9
    return float(np.dot(a_vec, b_vec) / denom)


def embed_text(openai_client: Optional[OpenAI], text: str, cache: Dict[str, List[float]], model: str = "text-embedding-3-small") -> Optional[List[float]]:
    if not openai_client:
        return None
    key = (model, text)
    if key in cache:
        return cache[key]
    try:
        result = openai_client.embeddings.create(input=text, model=model)
        embedding = result.data[0].embedding
    except Exception as exc:  # pragma: no cover
        log(f"Embedding error: {exc}")
        return None
    cache[key] = embedding
    return embedding


# -------------------------------------------------------------
# Pinecone + Neo4j lookups
# -------------------------------------------------------------
def query_pinecone_for_component(
    component: Component,
    pinecone_client: Pinecone,
    openai_client: Optional[OpenAI],
    index_name: str,
    top_k: int,
    embed_cache: Dict[str, List[float]],
) -> List[RuleCandidate]:
    if not pinecone_client:
        return []

    idx = pinecone_client.Index(index_name)
    text_for_embedding = f"{component.name} context: {component.context}"
    if component.embedding is None:
        component.embedding = embed_text(openai_client, text_for_embedding, embed_cache)
    if component.embedding is None:
        log(f"Skipping Pinecone query for {component.name}: no embedding available.")
        return []

    try:
        response = idx.query(vector=component.embedding, top_k=top_k, include_metadata=True)
    except Exception as exc:  # pragma: no cover
        log(f"Pinecone query failed for {component.name}: {exc}")
        return []

    candidates: List[RuleCandidate] = []
    for match in response.get("matches", []):
        metadata = match.get("metadata") or {}
        rule_id = metadata.get("rule_id") or metadata.get("id") or match.get("id")
        if not rule_id:
            continue
        candidates.append(
            RuleCandidate(
                rule_id=str(rule_id),
                source="pinecone",
                pinecone_score=float(match.get("score", 0.0)),
                metadata=metadata,
            )
        )
    return candidates


def search_rule_ids_by_keywords(driver: Any, keywords: Sequence[str], limit: int = 5) -> List[str]:
    sanitized = [kw.strip().upper() for kw in keywords if kw and kw.strip()]
    if not sanitized:
        return []

    query = """
    WITH $keywords AS keywords
    MATCH (r:Rule)
    WHERE any(kw IN keywords WHERE
        kw <> '' AND (
            toUpper(coalesce(r.requirement,'')) CONTAINS kw OR
            toUpper(coalesce(r.topic,'')) CONTAINS kw OR
            toUpper(coalesce(r.section_title,'')) CONTAINS kw OR
            toUpper(coalesce(r.section_path,'')) CONTAINS kw OR
            toUpper(coalesce(r.attribute,'')) CONTAINS kw
        )
    )
    RETURN DISTINCT r.id AS rule_id
    LIMIT $limit
    """
    with driver.session() as session:
        rows = session.run(query, keywords=sanitized, limit=limit)
        return [row["rule_id"] for row in rows if row.get("rule_id")]


def fetch_rules_by_ids(driver: Any, rule_ids: Sequence[str]) -> Dict[str, RuleDetail]:
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
    with driver.session() as session:
        rows = session.run(query, ids=list(rule_ids))

    details: Dict[str, RuleDetail] = {}
    for row in rows:
        rid = row.get("rule_id")
        if not rid:
            continue
        details[rid] = RuleDetail(
            rule_id=rid,
            section_id=row.get("section_id"),
            section_title=row.get("section_title"),
            requirement=row.get("requirement"),
            topic=row.get("topic"),
            attribute=row.get("attribute"),
            value=row.get("value"),
            zones=[z for z in row.get("zones") or [] if z],
        )
    return details


# -------------------------------------------------------------
# Evaluation logic
# -------------------------------------------------------------
def normalise_value(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def evaluate_rule_against_component(
    component: Component,
    rule: RuleDetail,
    candidate: RuleCandidate,
    openai_client: Optional[OpenAI],
    embed_cache: Dict[str, List[float]],
) -> Dict[str, Any]:
    component_text_upper = component.context.upper()

    value_terms = [term.upper() for term in normalise_value(rule.value)]
    attribute_term = (rule.attribute or "").upper()
    requirement_text = rule.requirement or ""

    matched_values = [term for term in value_terms if term and term in component_text_upper]
    attribute_matched = bool(attribute_term and attribute_term in component_text_upper)

    # Semantic support
    if component.embedding is None:
        component.embedding = embed_text(openai_client, f"{component.name} context: {component.context}", embed_cache)

    semantic_score = None
    if openai_client and component.embedding is not None and requirement_text:
        rule_embedding = embed_text(openai_client, requirement_text, embed_cache)
        if rule_embedding is not None:
            semantic_score = cosine_sim(component.embedding, rule_embedding)

    pinecone_score = candidate.pinecone_score if candidate.pinecone_score is not None else None
    confidence = max([score for score in [pinecone_score, semantic_score] if score is not None], default=0.0)

    status = "REVIEW"
    notes: List[str] = []

    if matched_values and (attribute_term == "" or attribute_matched):
        status = "PASS"
        notes.append(f"Matched values: {', '.join(matched_values)}")
    elif matched_values or attribute_matched:
        status = "PARTIAL"
        if matched_values:
            notes.append(f"Matched values: {', '.join(matched_values)}")
        if attribute_matched:
            notes.append(f"Matched attribute term '{rule.attribute}'")
    else:
        status = "REVIEW"
        if confidence > 0.75:
            notes.append("High semantic similarity but no explicit value match in plan text.")
        else:
            notes.append("No explicit reference to required values found in plan context.")

    if semantic_score is not None:
        notes.append(f"Semantic score: {semantic_score:.2f}")
    if pinecone_score is not None:
        notes.append(f"Pinecone score: {pinecone_score:.2f}")
    if rule.zones:
        notes.append(f"Applicable zones: {', '.join(rule.zones)}")

    return {
        "rule_id": rule.rule_id,
        "section_id": rule.section_id,
        "section_title": rule.section_title,
        "requirement": rule.requirement,
        "topic": rule.topic,
        "attribute": rule.attribute,
        "value": normalise_value(rule.value),
        "status": status,
        "confidence": round(confidence, 3),
        "matched_terms": matched_values,
        "notes": notes,
        "zones": rule.zones,
        "source": candidate.source,
    }


# -------------------------------------------------------------
# Writeback
# -------------------------------------------------------------
def writeback_results(driver: Any, plan_name: str, components: Sequence[Dict[str, Any]]) -> None:
    with driver.session() as session:
        for component in components:
            for rule in component.get("rules", []):
                session.run(
                    """
                    MERGE (p:Plan {name:$plan})
                    MATCH (r:Rule {id:$rule_id})
                    MERGE (p)-[rel:CHECKED_AGAINST]->(r)
                    SET rel.status = $status,
                        rel.score = $confidence,
                        rel.component = $component,
                        rel.notes = $notes
                    """,
                    plan=plan_name,
                    rule_id=rule["rule_id"],
                    status=rule["status"],
                    confidence=rule["confidence"],
                    component=component["name"],
                    notes="; ".join(rule.get("notes", [])),
                )
    log(f"Neo4j writeback complete for plan '{plan_name}'.")


# -------------------------------------------------------------
# Environment bootstrap
# -------------------------------------------------------------
def load_environment() -> None:
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    env_loaded = False
    if load_dotenv and env_path.exists():
        env_loaded = load_dotenv(env_path)
        if env_loaded:
            log(f"Loaded environment variables from {env_path}.")
        else:
            log("python-dotenv could not load .env; will try manual parsing.")
    elif not env_path.exists():
        log("No .env file found to load environment variables.")
    else:
        log("python-dotenv not installed; attempting manual .env parsing.")

    if not env_loaded and env_path.exists():
        with env_path.open() as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
        log(f"Environment variables populated from {env_path} via manual loader.")


# -------------------------------------------------------------
# Reporting
# -------------------------------------------------------------
def build_report_payload(
    plan_name: str,
    components: Sequence[Component],
    component_evaluations: Dict[str, List[Dict[str, Any]]],
    pinecone_index: Optional[str],
    used_pinecone: bool,
) -> Dict[str, Any]:
    serialised_components: List[Dict[str, Any]] = []
    status_counts = defaultdict(int)
    total_rules = 0

    for component in components:
        rules = component_evaluations.get(component.component_id, [])
        total_rules += len(rules)
        for rule in rules:
            status_counts[rule["status"]] += 1

        serialised_components.append(
            {
                "component_id": component.component_id,
                "name": component.name,
                "sheet_number": component.sheet_number,
                "matched_keyword": component.matched_keyword,
                "context": component.context,
                "rules": rules,
            }
        )

    summary = {
        "total_components": len(components),
        "components_with_rules": sum(1 for comp in serialised_components if comp["rules"]),
        "total_rule_evaluations": total_rules,
        "status_breakdown": dict(status_counts),
        "pinecone_index": pinecone_index if used_pinecone else None,
    }

    return {
        "plan": plan_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "components": serialised_components,
    }


# -------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Component-level compliance check against Neo4j + Pinecone rules.")
    parser.add_argument("--plan", required=True, help="Path to extracted plan JSON (output of extract_vector_plan.py).")
    parser.add_argument("--writeback", action="store_true", help="Persist plan → rule evaluation edges back to Neo4j.")
    parser.add_argument("--pinecone-index", default=os.getenv("PINECONE_INDEX", "planning-rules"), help="Pinecone index to query.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of rule candidates to retrieve per component.")
    parser.add_argument("--max-components", type=int, default=12, help="Maximum plan components to evaluate.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    load_environment()

    plan_path = Path(args.plan)
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan JSON not found: {plan_path}")
    plan_name = plan_path.stem.replace("_output", "")

    log(f"Loading plan data from {plan_path} ...")
    with plan_path.open() as f:
        plan_data = json.load(f)

    log("Extracting plan components ...")
    components = extract_plan_components(plan_data, max_components=args.max_components)
    if not components:
        log("No components detected in plan; nothing to evaluate.")
        return
    log(f"Identified {len(components)} component(s) for compliance checks.")

    log("Initialising service clients ...")
    driver = get_neo4j_driver()
    openai_client = get_openai_client()
    pinecone_client = get_pinecone_client()
    used_pinecone = pinecone_client is not None
    if openai_client:
        log("OpenAI embeddings enabled.")
    else:
        log("OpenAI embeddings disabled (missing OPENAI_API_KEY).")
    if pinecone_client:
        log(f"Pinecone client initialised (index '{args.pinecone_index}').")
    else:
        log("Pinecone client not available; falling back to Neo4j keyword search only.")

    embed_cache: Dict[str, List[float]] = {}

    # Query Pinecone (if available) and gather candidate rule IDs
    log("Collecting candidate rules for each component ...")
    for component in tqdm(components, desc="Components"):
        candidates: List[RuleCandidate] = []
        if pinecone_client:
            candidates.extend(
                query_pinecone_for_component(
                    component,
                    pinecone_client,
                    openai_client,
                    args.pinecone_index,
                    args.top_k,
                    embed_cache,
                )
            )

        keyword_candidates = search_rule_ids_by_keywords(
            driver,
            keywords=[component.name, component.matched_keyword],
            limit=max(3, args.top_k - len(candidates)),
        )
        for rid in keyword_candidates:
            if rid not in {cand.rule_id for cand in candidates}:
                candidates.append(RuleCandidate(rule_id=rid, source="keyword", pinecone_score=None))

        component.candidate_rules = candidates
        if not candidates:
            log(f"No candidate rules identified for component '{component.name}' (sheet {component.sheet_number}).")

    unique_rule_ids = {cand.rule_id for comp in components for cand in comp.candidate_rules}
    log(f"Fetching {len(unique_rule_ids)} unique rule(s) from Neo4j ...")
    rule_details = fetch_rules_by_ids(driver, list(unique_rule_ids))

    log("Evaluating rules against plan components ...")
    component_evaluations: Dict[str, List[Dict[str, Any]]] = {}
    for component in tqdm(components, desc="Evaluations"):
        evaluations: List[Dict[str, Any]] = []
        for candidate in component.candidate_rules:
            detail = rule_details.get(candidate.rule_id)
            if not detail:
                continue
            evaluation = evaluate_rule_against_component(
                component,
                detail,
                candidate,
                openai_client,
                embed_cache,
            )
            evaluations.append(evaluation)
        component_evaluations[component.component_id] = evaluations

    out_path = plan_path.with_name(plan_path.stem.replace("_output", "_compliance.json"))
    log(f"Saving structured compliance report to {out_path} ...")
    report_payload = build_report_payload(plan_name, components, component_evaluations, args.pinecone_index, used_pinecone)
    with out_path.open("w") as f:
        json.dump(report_payload, f, indent=2)
    log(f"Compliance report saved → {out_path.name}")

    if args.writeback:
        log("Writing back results to Neo4j ...")
        writeback_results(driver, plan_name, report_payload["components"])

    driver.close()

    summary = report_payload["summary"]
    log(
        "Summary → Components: {total_components}, With rules: {components_with_rules}, "
        "Evaluations: {total_rule_evaluations}, Status counts: {status_breakdown}".format(**summary)
    )


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])

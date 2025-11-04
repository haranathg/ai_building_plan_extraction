"""
check_plan_compliance_neo4j.py
-------------------------------
Compliance checking between vector plan JSON and Neo4j rule KB,
with optional Pinecone / OpenAI scoring.

Usage:
    python3 check_plan_compliance_neo4j.py \
        --plan House-Floor-Plans-vector_output.json \
        [--pinecone] [--writeback]

Dependencies:
    pip install neo4j pinecone-client openai tqdm numpy
"""

import os, sys, json, argparse, numpy as np
from pathlib import Path
from tqdm import tqdm
from neo4j import GraphDatabase
from pinecone import Pinecone
from openai import OpenAI
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# -------------------------------------------------------------
# Logging helper
# -------------------------------------------------------------
def log(msg): print(f"[INFO] {msg}")

# -------------------------------------------------------------
# Connections
# -------------------------------------------------------------
def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd  = os.getenv("NEO4J_PASSWORD")
    missing = [k for k, v in {"NEO4J_URI": uri, "NEO4J_USER": user, "NEO4J_PASSWORD": pwd}.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required Neo4j environment vars: {', '.join(missing)}")
    return GraphDatabase.driver(uri, auth=(user, pwd))

def get_pinecone():
    key = os.getenv("PINECONE_API_KEY")
    return Pinecone(api_key=key) if key else None

def get_openai():
    key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=key) if key else None

# -------------------------------------------------------------
# Fetch rules & relationships
# -------------------------------------------------------------
def fetch_rules_graph(tx):
    q = """
    MATCH (r:Rule)-[:HAS_CONDITION]->(c:Condition)
    OPTIONAL MATCH (r)-[:HAS_DEPENDENCY]->(dep:Rule)
    RETURN DISTINCT r.id AS rule_id,
                    r.description AS description,
                    collect(DISTINCT c.description) AS conditions,
                    collect(DISTINCT dep.id) AS depends_on
    """
    return [dict(r) for r in tx.run(q)]

def load_rules_from_neo4j(driver):
    with driver.session() as s:
        try:
            rules = s.execute_read(fetch_rules_graph)
        except AttributeError:
            rules = s.read_transaction(fetch_rules_graph)
    log(f"Loaded {len(rules)} rules from Neo4j.")
    return rules

# -------------------------------------------------------------
# Similarity utilities
# -------------------------------------------------------------
def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)

def embed_text(openai_client, text, model="text-embedding-3-small"):
    """Return embedding vector for given text."""
    try:
        return openai_client.embeddings.create(input=text, model=model).data[0].embedding
    except Exception as e:
        log(f"Embedding error: {e}")
        return None

# -------------------------------------------------------------
# Compliance Evaluation
# -------------------------------------------------------------
def evaluate_rules(plan_data, rules, openai_client=None, pinecone_client=None, pinecone_index="building-rules-index"):
    plan_text = " ".join(
        blk["text"].upper()
        for s in plan_data.get("sheets", [])
        for blk in s["text_blocks"]
    )

    # Get plan embedding once (for similarity)
    plan_emb = None
    if openai_client:
        plan_emb = embed_text(openai_client, plan_text)

    results = []
    for rule in tqdm(rules, desc="Evaluating rules"):
        matched = [c for c in rule["conditions"] if c.upper() in plan_text]
        status = "PASS" if matched else "REVIEW"
        score = 0.0

        # Direct match = high confidence
        if matched:
            score = 0.95
        elif openai_client and plan_emb:
            # Compute semantic similarity between plan text and rule
            rule_text = f"{rule['description']} " + " ".join(rule["conditions"])
            rule_emb = embed_text(openai_client, rule_text)
            if rule_emb:
                score = round(float(cosine_sim(plan_emb, rule_emb)), 3)
                status = "PASS" if score > 0.8 else "REVIEW"

        # Optional Pinecone backup (for fast approximate similarity)
        if pinecone_client and not openai_client:
            try:
                idx = pinecone_client.Index(pinecone_index)
                res = idx.query(vector=plan_text, top_k=1, include_metadata=True)
                if res and res["matches"]:
                    score = float(res["matches"][0]["score"])
                    status = "PASS" if score > 0.8 else "REVIEW"
            except Exception as e:
                log(f"Pinecone similarity error: {e}")

        results.append({
            "rule_id": rule["rule_id"],
            "description": rule["description"],
            "depends_on": rule["depends_on"],
            "status": status,
            "matched_conditions": matched,
            "score": round(score, 3)
        })
    return results

# -------------------------------------------------------------
# Writeback results to Neo4j
# -------------------------------------------------------------
def writeback_results(driver, plan_name, results):
    with driver.session() as s:
        for r in results:
            s.run("""
                MERGE (p:Plan {name:$plan})
                MATCH (rule:Rule {id:$rule_id})
                MERGE (p)-[rel:CHECKED_AGAINST]->(rule)
                SET rel.status = $status,
                    rel.score = $score,
                    rel.details = $details
            """, plan=plan_name, rule_id=r["rule_id"],
                 status=r["status"], score=r["score"],
                 details=", ".join(r["matched_conditions"]))
    log(f"Neo4j writeback complete for plan '{plan_name}'.")

# -------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------
def load_environment():
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    env_loaded = False
    if load_dotenv:
        if env_path.exists():
            env_loaded = load_dotenv(env_path)
            if env_loaded:
                log(f"Loaded environment variables from {env_path}.")
            else:
                log("python-dotenv could not load .env; will try manual parsing.")
        else:
            log("No .env file found to load environment variables.")
    else:
        log("python-dotenv not installed; attempting manual .env parsing.")

    if not env_loaded and env_path.exists():
        with env_path.open() as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
        log(f"Environment variables populated from {env_path} via manual loader.")
        env_loaded = True
    return env_loaded


def main():
    parser = argparse.ArgumentParser(description="Compliance check with Neo4j KB + optional scoring.")
    parser.add_argument("--plan", required=True, help="Path to extracted plan JSON.")
    parser.add_argument("--writeback", action="store_true", help="Write results back to Neo4j.")
    parser.add_argument("--pinecone", action="store_true", help="Use Pinecone fallback.")
    args = parser.parse_args()

    load_environment()

    plan_path = Path(args.plan)
    plan_name = plan_path.stem.replace("_output", "")
    log(f"Loading plan data from {plan_path} ...")
    with open(plan_path) as f:
        plan_data = json.load(f)

    log("Initializing Neo4j driver ...")
    try:
        driver = get_neo4j_driver()
    except EnvironmentError as e:
        log(f"Neo4j configuration error → {e}")
        sys.exit(1)

    log("Fetching rules from Neo4j ...")
    try:
        rules = load_rules_from_neo4j(driver)
    except Exception as e:
        log(f"Neo4j fetch error → {e}")
        driver.close()
        sys.exit(1)

    openai_client = get_openai()
    if openai_client:
        log("OpenAI embeddings enabled.")
    else:
        log("OpenAI embeddings disabled (missing OPENAI_API_KEY).")

    pinecone_client = get_pinecone() if args.pinecone else None
    if args.pinecone:
        if pinecone_client:
            log("Pinecone fallback enabled.")
        else:
            log("Pinecone fallback requested but PINECONE_API_KEY not set; continuing without it.")

    log("Evaluating rule compliance ...")
    results = evaluate_rules(plan_data, rules, openai_client, pinecone_client)

    # Save report
    out_path = plan_path.with_name(plan_path.stem.replace("_output", "_compliance.json"))
    log(f"Saving compliance report to {out_path} ...")
    with open(out_path, "w") as f:
        json.dump({"results": results}, f, indent=2)
    log(f"Compliance report saved → {out_path.name}")

    if args.writeback:
        log("Writing results back to Neo4j ...")
        writeback_results(driver, plan_name, results)

    driver.close()
    passed = len([r for r in results if r["status"] == "PASS"])
    review = len([r for r in results if r["status"] == "REVIEW"])
    scored = [r["score"] for r in results if r["score"] > 0]
    avg_score = round(float(np.mean(scored)), 3) if scored else 0.0
    log(f"Summary → PASS: {passed}, REVIEW: {review}, AVG Score: {avg_score}")

if __name__ == "__main__":
    main()

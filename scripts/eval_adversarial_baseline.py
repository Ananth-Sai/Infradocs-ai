"""
Adversarial Baseline Evaluation — Plain Dense Pipeline Only
============================================================
Runs 5 adversarial questions through:
  1. Plain dense vector search (ChromaDB cosine, no BM25, no hybrid)
  2. Gemini generation from retrieved context

Records: retrieved chunks, distances, sources, generated answer.
Prints a diagnostic report showing where retrieval or generation broke.

Usage:
    python eval_adversarial_baseline.py
"""

import os
import sys
import json
import time

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from index import search, build_index
from answer import generate_with_fallback, PROMPT_TEMPLATE

# --- The 5 Adversarial Questions ---
ADVERSARIAL_SET = [
    {
        "id": "ADV-1",
        "type": "Multi-hop (cross-doc)",
        "question": (
            "If a canary deployment's error rate spikes and triggers a rollback, "
            "but the failing service also throws ERR_VAULT_LEASE_REVOKED errors, "
            "what two things need to happen to fully recover?"
        ),
        "expected_answer": (
            "Two things: (1) Traffic automatically reverts to the previous stable revision "
            "(automatic rollback when HTTP 5xx > 1% over 5 min), AND (2) the pod must be "
            "restarted or an ESO sync triggered to resolve the revoked Vault lease."
        ),
        "required_sources": ["deployment_guide.md", "troubleshooting_and_faq.md"],
    },
    {
        "id": "ADV-2",
        "type": "Paraphrase (zero vocab overlap)",
        "question": (
            "Our team's authentication credentials keep dying after about an hour "
            "and nobody can stay logged in. What's going on and how do we fix it?"
        ),
        "expected_answer": (
            "Session tokens (Ed25519-signed JWTs) have a strict validity of 60 minutes. "
            "On expiry you get ERR_AUTH_EXPIRED_JWT (HTTP 401). Fix: exchange the refresh "
            "token at /v2/auth/refresh. Refresh tokens expire after 14 days of inactivity."
        ),
        "required_sources": ["platform_overview.md", "troubleshooting_and_faq.md"],
    },
    {
        "id": "ADV-3",
        "type": "Distractor-heavy",
        "question": "What happens to database connections when secrets are rotated?",
        "expected_answer": (
            "Static secrets (like DB credentials) rotate every 30 days. If a service "
            "fails to refresh its Vault lease within 5 min, it gets ERR_VAULT_LEASE_REVOKED "
            "(HTTP 503). Fix: restart the pod or trigger ESO sync. NOT related to PostgreSQL failover."
        ),
        "required_sources": ["deployment_guide.md", "troubleshooting_and_faq.md"],
    },
    {
        "id": "ADV-4",
        "type": "Implicit reasoning (arithmetic)",
        "question": (
            "A Standard Tier customer is sending 25 requests per second sustained. "
            "Will they get rate-limited?"
        ),
        "expected_answer": (
            "Yes, sustained 25 req/s = 1,500 req/min, which exceeds Standard Tier's "
            "1,200 req/min quota. Short bursts are fine (under 100 req/s burst cap), "
            "but sustained 25/s will trigger ERR_RATE_LIMIT_EXCEEDED (HTTP 429)."
        ),
        "required_sources": ["platform_overview.md"],
    },
    {
        "id": "ADV-5",
        "type": "Terse + abbreviation",
        "question": "Does InfraDocs Cloud Platform support mutual TLS?",
        "expected_answer": (
            "Yes — mTLS is supported for service-to-service communication, listed under "
            "Authentication & Access Control alongside OIDC and SAML 2.0."
        ),
        "required_sources": ["platform_overview.md"],
    },
]


def run_baseline():
    """Run all adversarial questions through plain dense search + Gemini."""
    # Ensure index exists
    build_index("docs")

    results = []
    top_k = 5

    for item in ADVERSARIAL_SET:
        print(f"\n{'='*70}")
        print(f"[{item['id']}] {item['type']}")
        print(f"Q: {item['question']}")
        print(f"{'='*70}")

        # Step 1: Plain dense search only
        t0 = time.time()
        retrieved = search(item["question"], top_k=top_k)
        t_retrieval = (time.time() - t0) * 1000

        # Check which required sources were actually retrieved
        retrieved_sources = set(r["source"] for r in retrieved)
        required = set(item["required_sources"])
        sources_found = required & retrieved_sources
        sources_missing = required - retrieved_sources

        print(f"\n  Retrieval ({t_retrieval:.0f}ms):")
        for i, r in enumerate(retrieved, 1):
            print(f"    Chunk {i}: [{r['source']}] dist={r['distance']:.4f}")
            print(f"             {r['text'][:120]}...")

        print(f"\n  Source coverage: {len(sources_found)}/{len(required)}")
        if sources_missing:
            print(f"  [MISS] MISSING sources: {sources_missing}")
        else:
            print(f"  [OK] All required sources retrieved")

        # Step 2: Generate answer from retrieved context
        context = "\n\n".join(
            f"[source: {r['source']}]\n{r['text']}" for r in retrieved
        )
        prompt = PROMPT_TEMPLATE.format(context=context, question=item["question"])

        t1 = time.time()
        generated_answer = generate_with_fallback(prompt)
        t_generation = time.time() - t1

        print(f"\n  Generated Answer ({t_generation:.2f}s):")
        print(f"    {generated_answer[:500]}")

        print(f"\n  Expected Answer:")
        print(f"    {item['expected_answer']}")

        result = {
            "id": item["id"],
            "type": item["type"],
            "question": item["question"],
            "retrieved_chunks": [
                {
                    "source": r["source"],
                    "distance": round(r["distance"], 4),
                    "text_preview": r["text"][:200],
                }
                for r in retrieved
            ],
            "sources_required": item["required_sources"],
            "sources_retrieved": list(retrieved_sources),
            "sources_missing": list(sources_missing),
            "retrieval_complete": len(sources_missing) == 0,
            "generated_answer": generated_answer,
            "expected_answer": item["expected_answer"],
            "retrieval_ms": round(t_retrieval, 1),
            "generation_s": round(t_generation, 2),
        }
        results.append(result)

    # --- Summary ---
    print(f"\n\n{'='*70}")
    print("ADVERSARIAL BASELINE SUMMARY (Plain Dense Search)")
    print(f"{'='*70}")

    retrieval_pass = sum(1 for r in results if r["retrieval_complete"])
    print(f"\nRetrieval coverage: {retrieval_pass}/{len(results)} questions had all required sources in top-{top_k}")

    for r in results:
        status = "[OK]" if r["retrieval_complete"] else "[FAIL]"
        print(f"  {status} [{r['id']}] {r['type']}")
        if r["sources_missing"]:
            print(f"       Missing: {r['sources_missing']}")
        dists = [c["distance"] for c in r["retrieved_chunks"]]
        print(f"       Distances: {[round(d, 3) for d in dists]}")

    # Save detailed results to JSON
    output_path = "eval_adversarial_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to: {output_path}")
    print("Review the generated answers manually against expected answers.")
    print("Then we can re-run with hybrid_search to compare.\n")


if __name__ == "__main__":
    run_baseline()

# v2_edge_cases — v1 baseline (24 Qs) + 10 new edge-case questions
# Purpose: stress-test multi-hop reasoning, near-miss hallucination,
#          subtle detail recall, and cross-doc synthesis.

from eval_sets.v1_baseline import EVAL_SET as V1_SET

EDGE_CASES = [
    # ---------- Multi-hop / Cross-doc (Answerable) ----------
    # Requires combining deployment_guide (secret rotation every 30 days)
    # + troubleshooting (ERR_VAULT_LEASE_REVOKED = lease not refreshed within 5 min).
    {
        "question": "If a microservice fails to refresh its Vault lease during one of the 30-day automatic secret rotations, what HTTP error will the client receive and how is it resolved?",
        "expected_answer": "The client receives ERR_VAULT_LEASE_REVOKED (HTTP 503). Restarting the pod or triggering an ESO sync resolves the condition.",
        "expected_source": "troubleshooting_and_faq.md",
        "answerable": True,
    },
    # Requires platform_overview (RBAC roles) + platform_overview (NIS handles auth).
    {
        "question": "Which service assigns principals to the four default RBAC roles in ICP?",
        "expected_answer": "The Nexus Identity Service (NIS) enforces authentication, and the four default RBAC roles are Viewer, Operator, SecurityAdmin, and SuperAdmin.",
        "expected_source": "platform_overview.md",
        "answerable": True,
    },
    # Requires deployment_guide (canary Phases 1-3) — asking for Phase 2 specifics,
    # which v1 never tested directly.
    {
        "question": "What is the p99 latency threshold for Phase 2 of the canary deployment and how long does it last?",
        "expected_answer": "Phase 2 increases traffic to 50% for 30 minutes and requires p99 latency not to exceed 120ms.",
        "expected_source": "deployment_guide.md",
        "answerable": True,
    },
    # Cross-doc: platform_overview (Standard Tier limits) + troubleshooting (429 mitigation).
    {
        "question": "If a Standard Tier organization exceeds its API rate limit, what is their per-minute quota and what mitigation strategy should they use?",
        "expected_answer": "Standard Tier allows 1,200 requests per minute per organization. Clients should inspect the X-RateLimit-Reset header and implement exponential backoff with jitter.",
        "expected_source": "platform_overview.md",
        "answerable": True,
    },

    # ---------- Subtle detail (Answerable) ----------
    # Asks about the branching strategy — a minor detail easy to overlook.
    {
        "question": "What Docker image architectures does the ICP CI/CD pipeline build when code is merged to main?",
        "expected_answer": "Multi-architecture Docker images for amd64 and arm64.",
        "expected_source": "deployment_guide.md",
        "answerable": True,
    },
    # Asks about how read replicas handle DNS after failover — a small detail.
    {
        "question": "How do PostgreSQL read replicas update DNS records after electing a new leader?",
        "expected_answer": "Read replicas automatically elect a new leader and update DNS records via AWS Route53 private hosted zones.",
        "expected_source": "troubleshooting_and_faq.md",
        "answerable": True,
    },

    # ---------- Near-miss tricks (Unanswerable — sound plausible) ----------
    # Uses real ACP terminology (Flagger, Prometheus) but asks about alerting
    # config which is never mentioned in the docs.
    {
        "question": "What Prometheus alerting rules are configured for the Flagger canary deployment controller?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },
    # Mentions real concepts (NIS, OIDC) but asks about MFA which is never discussed.
    {
        "question": "How does the Nexus Identity Service enforce multi-factor authentication for SuperAdmin accounts?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },
    # Mentions real region (ap-southeast-1) but asks about failover behavior
    # that is only documented for us-east-1 / eu-central-1.
    {
        "question": "What is the replication lag between ap-southeast-1 and us-east-1?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },
    # Uses real concept (Vault, ESO) but asks about audit logging which is never covered.
    {
        "question": "What audit log format does HashiCorp Vault use when rotating secrets through the External Secrets Operator?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },
]

# Merge: all v1 questions + new edge cases
EVAL_SET = V1_SET + EDGE_CASES

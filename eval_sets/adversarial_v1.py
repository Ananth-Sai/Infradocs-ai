# eval_sets/adversarial_v1.py
#
# A separate, harder eval set — kept apart from v1_baseline.py rather than
# merged into it, following the same "don't edit a locked set" convention.
# These questions specifically target weaknesses plain top-k dense retrieval
# is known to have: combining facts across 2 documents (multi-hop), and
# distinguishing between two similar-sounding facts within the same
# document (near-miss).
#
# Run this against the PLAIN pipeline first (answer.py as it currently is,
# no hybrid/rerank). Get a real baseline score before touching Slice 5.

ADVERSARIAL_SET = [
    {
        "question": (
            "An Enterprise-tier client is sending 550 requests per second. "
            "Will they hit the burst limit, and if so, what HTTP error and "
            "recommended remediation should they expect?"
        ),
        "expected_answer": (
            "Yes — the Enterprise tier burst limit is 500 requests/sec, so "
            "550 req/sec exceeds it. This triggers ERR_RATE_LIMIT_EXCEEDED "
            "(HTTP 429). The client should inspect the X-RateLimit-Reset "
            "header and implement exponential backoff with jitter."
        ),
        "expected_source": ["platform_overview.md", "troubleshooting_and_faq.md"],
        "answerable": True,
        "type": "multi_hop",
    },
    {
        "question": (
            "If a microservice's Vault lease isn't refreshed during "
            "automated secret rotation, what error does it hit, and how "
            "does that relate to the rotation schedule?"
        ),
        "expected_answer": (
            "Static secrets are automatically rotated every 30 days via Vault and "
            "the External Secrets Operator. If a service fails to refresh "
            "its Vault lease within 5 minutes of expiration during that "
            "rotation, it hits ERR_VAULT_LEASE_REVOKED (HTTP 503)."
        ),
        "expected_source": ["deployment_guide.md", "troubleshooting_and_faq.md"],
        "answerable": True,
        "type": "multi_hop",
    },
    {
        "question": (
            "If eu-central-1 experiences degraded performance with p95 "
            "latency at 600ms, what severity level and response SLA "
            "applies, and does this affect async replication to us-east-1?"
        ),
        "expected_answer": (
            "This is a Severity 2 incident (single-region degradation, "
            "p95 latency exceeding 500ms), with an initial response SLA "
            "under 1 hour. The docs don't state that regional degradation "
            "affects replication lag — replication lag is described "
            "separately (averaging under 45ms) with no stated causal link "
            "to regional performance incidents. A correct answer should "
            "not assert replication is affected."
        ),
        "expected_source": ["platform_overview.md", "troubleshooting_and_faq.md"],
        "answerable": True,
        "type": "multi_hop",
    },
    {
        "question": (
            "During Phase 2 of a canary rollout, if p99 latency exceeds "
            "120ms, does the system automatically roll back to the "
            "previous stable revision?"
        ),
        "expected_answer": (
            "Not necessarily, per the docs. Automatic rollback is "
            "explicitly tied only to HTTP 5xx responses exceeding 1% over "
            "a 5-minute moving window. Exceeding the Phase 2 latency "
            "threshold (120ms) is described as a gate that prevents "
            "promotion to Phase 3, but the docs do not state that "
            "exceeding it alone triggers an automatic rollback. A correct "
            "answer should not conflate the two."
        ),
        "expected_source": ["deployment_guide.md"],
        "answerable": True,
        "type": "near_miss",
    },
    {
        "question": (
            "What escalation path applies if the Nexus Identity Service "
            "goes down in the ap-southeast-1 region?"
        ),
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
        "type": "adversarial_unanswerable",
    },
]

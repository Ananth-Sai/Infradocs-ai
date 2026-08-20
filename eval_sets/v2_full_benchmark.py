# eval_sets/v2_full_benchmark.py
#
# Comprehensive 32-Question Evaluation Benchmark
# Combines:
#   - 18 Answerable baseline single-hop questions (v1_baseline)
#   - 6 Standard out-of-domain unanswerable questions (v1_baseline)
#   - 4 Adversarial multi-hop and near-miss questions (adversarial_v1)
#   - 4 Adversarial unanswerable / pseudo-causal trap questions (adversarial_v1 + new traps)

EVAL_SET = [
    # =========================================================================
    # 1. BASELINE SINGLE-HOP QUESTIONS (deployment_guide.md)
    # =========================================================================
    {
        "question": "What tools power the GitOps deployment workflow in ICP?",
        "expected_answer": "ArgoCD and GitHub Actions.",
        "expected_source": "deployment_guide.md",
        "answerable": True,
    },
    {
        "question": "Which Kubernetes versions are used for production target clusters?",
        "expected_answer": "EKS v1.30 and GKE v1.29.",
        "expected_source": "deployment_guide.md",
        "answerable": True,
    },
    {
        "question": "What are the requirements and duration for Phase 1 of canary deployment?",
        "expected_answer": "10% traffic split for 15 minutes with an error rate threshold below 0.1%.",
        "expected_source": "deployment_guide.md",
        "answerable": True,
    },
    {
        "question": "What triggers an automatic rollback during a canary deployment?",
        "expected_answer": "If HTTP 5xx responses exceed 1% over a 5-minute moving window.",
        "expected_source": "deployment_guide.md",
        "answerable": True,
    },
    {
        "question": "How frequently are static secrets like database credentials rotated?",
        "expected_answer": "Every 30 days.",
        "expected_source": "deployment_guide.md",
        "answerable": True,
    },
    {
        "question": "What encryption algorithm is used for secrets at rest in ICP?",
        "expected_answer": "AES-256-GCM using AWS KMS / GCP Cloud KMS customer-managed keys (CMK).",
        "expected_source": "deployment_guide.md",
        "answerable": True,
    },

    # =========================================================================
    # 2. BASELINE SINGLE-HOP QUESTIONS (platform_overview.md)
    # =========================================================================
    {
        "question": "What role does the eu-central-1 region play in ICP architecture?",
        "expected_answer": "European Union dedicated data plane with GDPR-compliant data residency isolation.",
        "expected_source": "platform_overview.md",
        "answerable": True,
    },
    {
        "question": "What is the average replication lag between us-east-1 and eu-central-1?",
        "expected_answer": "Under 45 milliseconds.",
        "expected_source": "platform_overview.md",
        "answerable": True,
    },
    {
        "question": "What identity service enforces authentication in ICP?",
        "expected_answer": "Nexus Identity Service (NIS).",
        "expected_source": "platform_overview.md",
        "answerable": True,
    },
    {
        "question": "What is the validity duration of session tokens and refresh tokens?",
        "expected_answer": "Session tokens are valid for 60 minutes; refresh tokens expire after 14 days of inactivity.",
        "expected_source": "platform_overview.md",
        "answerable": True,
    },
    {
        "question": "What are the four default roles in InfraDocs Cloud Platform RBAC?",
        "expected_answer": "Viewer, Operator, SecurityAdmin, and SuperAdmin.",
        "expected_source": "platform_overview.md",
        "answerable": True,
    },
    {
        "question": "What are the rate limits for the Enterprise Tier API?",
        "expected_answer": "10,000 requests per minute per organization with a burst limit of 500 requests/sec.",
        "expected_source": "platform_overview.md",
        "answerable": True,
    },

    # =========================================================================
    # 3. BASELINE SINGLE-HOP QUESTIONS (troubleshooting_and_faq.md)
    # =========================================================================
    {
        "question": "What endpoint should clients call to exchange an expired token?",
        "expected_answer": "/v2/auth/refresh",
        "expected_source": "troubleshooting_and_faq.md",
        "answerable": True,
    },
    {
        "question": "How should a client mitigate an ERR_RATE_LIMIT_EXCEEDED HTTP 429 error?",
        "expected_answer": "Inspect the X-RateLimit-Reset header and implement exponential backoff with jitter.",
        "expected_source": "troubleshooting_and_faq.md",
        "answerable": True,
    },
    {
        "question": "What causes an ERR_VAULT_LEASE_REVOKED HTTP 503 error?",
        "expected_answer": "The microservice fails to refresh its Vault lease within 5 minutes of expiration during secret rotation.",
        "expected_source": "troubleshooting_and_faq.md",
        "answerable": True,
    },
    {
        "question": "What is the initial response SLA for a Severity 1 Critical Outage?",
        "expected_answer": "Under 15 minutes with 24/7 paging to the primary On-Call SRE team.",
        "expected_source": "troubleshooting_and_faq.md",
        "answerable": True,
    },
    {
        "question": "What tool manages PostgreSQL cluster failover?",
        "expected_answer": "Patroni with Raft-based consensus.",
        "expected_source": "troubleshooting_and_faq.md",
        "answerable": True,
    },
    {
        "question": "What is the maximum expected downtime during an ungraceful PostgreSQL primary failure?",
        "expected_answer": "28 seconds.",
        "expected_source": "troubleshooting_and_faq.md",
        "answerable": True,
    },

    # =========================================================================
    # 4. ADVERSARIAL MULTI-HOP & NEAR-MISS QUESTIONS (adversarial_v1)
    # =========================================================================
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

    # =========================================================================
    # 5. STANDARD OUT-OF-DOMAIN UNANSWERABLES (v1_baseline)
    # =========================================================================
    {
        "question": "What is InfraDocs Cloud's policy on remote work and expense reimbursement?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },
    {
        "question": "How do you configure Azure DevOps pipelines for ICP deployments?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },
    {
        "question": "What is the pricing model for storing objects in the S3 cold storage tier?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },
    {
        "question": "How do I upgrade MySQL read replicas in the Sydney region?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },
    {
        "question": "What are the guidelines for filing PTO during on-call rotations?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },
    {
        "question": "Which version of Java is required to run the local telemetry agent?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
    },

    # =========================================================================
    # 6. ADVERSARIAL PSEUDO-CAUSAL TRAPS (Unanswerable / Must Not Hallucinate)
    # =========================================================================
    {
        "question": "What escalation path applies if the Nexus Identity Service goes down in the ap-southeast-1 region?",
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
        "type": "adversarial_unanswerable",
    },
    {
        "question": (
            "If a pod fails its Vault lease refresh during automated secret rotation, "
            "does Patroni trigger an automatic PostgreSQL failover to a read replica?"
        ),
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
        "type": "adversarial_pseudo_causal_trap",
    },
    {
        "question": (
            "Can an Operator-role user bypass the Standard Tier 1,200 req/min API rate limit "
            "during a Severity 1 incident?"
        ),
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
        "type": "adversarial_pseudo_causal_trap",
    },
    {
        "question": (
            "Does ICP use Ed25519 signatures to sign Docker images built on GitHub Actions "
            "for ARM64 architecture?"
        ),
        "expected_answer": None,
        "expected_source": None,
        "answerable": False,
        "type": "adversarial_pseudo_causal_trap",
    },
]

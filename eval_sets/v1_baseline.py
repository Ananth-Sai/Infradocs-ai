# LOCKED BASELINE — Never edit this file after first run
# This is your reference point. If you want to make changes, create v2_*.py instead.

EVAL_SET = [
    # --- deployment_guide.md (Answerable) ---
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

    # --- platform_overview.md (Answerable) ---
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

    # --- troubleshooting_and_faq.md (Answerable) ---
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

    # --- Unanswerable / Out of Domain (Refusal Checks) ---
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
]
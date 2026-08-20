# InfraDocs Cloud Platform: Deployment & CI/CD Guide

## 1. Deployment Pipelines
All ICP microservices follow a GitOps deployment workflow powered by ArgoCD and GitHub Actions.
- Target Clusters: Production workloads run on managed Kubernetes (EKS v1.30 and GKE v1.29).
- Branching Strategy: Commits merged into the `main` branch automatically trigger integration tests and build multi-architecture Docker images (amd64 and arm64).

## 2. Canary Deployment Strategy
Production rollouts use progressive traffic shifting with Flagger and Prometheus metrics:
- Phase 1 (Canary 10%): Initial traffic split for 15 minutes. Error rate threshold must remain below 0.1%.
- Phase 2 (Canary 50%): Increased traffic split for 30 minutes if p99 latency does not exceed 120ms.
- Phase 3 (Full 100%): Complete promotion to primary pods.
- Automatic Rollback: If HTTP 5xx responses exceed 1% over a 5-minute moving window, traffic automatically reverts to the previous stable revision.

## 3. Secrets Management
Secrets are managed using HashiCorp Vault integrated with Kubernetes External Secrets Operator (ESO).
- Static secrets (e.g. database credentials) are automatically rotated every 30 days.
- Encryption: All secrets at rest are encrypted with AES-256-GCM using AWS KMS / GCP Cloud KMS customer-managed keys (CMK).
- Hardcoding secrets in environment variables or configuration files is strictly blocked by pre-commit git hooks.

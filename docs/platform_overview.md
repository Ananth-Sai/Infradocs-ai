# InfraDocs Cloud Platform: Architecture & Core Services

## 1. Overview
InfraDocs Cloud Platform (ICP) is a globally distributed cloud management platform designed for enterprise workload orchestration. ICP provides automated infrastructure provisioning, multi-cloud governance, and real-time observability.

## 2. Global Infrastructure and Regions
ICP operates across three primary geographic regions:
- `us-east-1` (North Virginia): Primary control plane and multi-tenant telemetry cluster.
- `eu-central-1` (Frankfurt): European Union dedicated data plane with GDPR-compliant data residency isolation.
- `ap-southeast-1` (Singapore): Asia-Pacific edge routing and caching tier.

Data replication between `us-east-1` and `eu-central-1` occurs asynchronously with an average replication lag of under 45 milliseconds.

## 3. Authentication & Access Control
Authentication in ICP is enforced through the Nexus Identity Service (NIS).
- Supported protocols: OIDC (OpenID Connect), SAML 2.0, and mTLS for service-to-service communication.
- Session Tokens: Issued as Ed25519-signed JWTs with a strict validity duration of 60 minutes. Refresh tokens expire after 14 days of inactivity.
- Role-Based Access Control (RBAC): Every principal must belong to one of four default roles: `Viewer`, `Operator`, `SecurityAdmin`, or `SuperAdmin`.

## 4. API Rate Limits & Quotas
All API endpoints under `https://api.infradocs.io/v2/` enforce strict rate limiting based on the client's tier:
- Standard Tier: 1,200 requests per minute per organization (burst limit: 100 requests/sec).
- Enterprise Tier: 10,000 requests per minute per organization (burst limit: 500 requests/sec).
- Rate limit headers returned: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` (Unix epoch timestamp).

# InfraDocs Cloud Platform: Troubleshooting & FAQ

## 1. Common Error Codes & Mitigations
- `ERR_AUTH_EXPIRED_JWT (HTTP 401)`: The client access token has expired (default lifetime is 60 minutes). The client application should exchange its refresh token at `/v2/auth/refresh` to obtain a fresh token.
- `ERR_RATE_LIMIT_EXCEEDED (HTTP 429)`: The organization quota has been reached. Clients should inspect the `X-RateLimit-Reset` header and implement exponential backoff with jitter.
- `ERR_VAULT_LEASE_REVOKED (HTTP 503)`: Occurs during automated secret rotation if the microservice fails to refresh its Vault lease within 5 minutes of expiration. Restarting the pod or triggering an ESO sync resolves the condition.

## 2. SLA & Incident Severity Levels
- Severity 1 (Critical Outage): Global control plane unavailable or data loss risk. Initial response SLA: under 15 minutes. 24/7 paging to the primary On-Call SRE team.
- Severity 2 (Degraded Performance): Single region degradation or elevated latency exceeding 500ms p95. Initial response SLA: under 1 hour.
- Severity 3 (Minor Bug / Non-critical feature): Workaround available. Initial response SLA: 1 business day.

## 3. Database Failover Procedures
PostgreSQL cluster failover is managed by Patroni with Raft-based consensus.
- Maximum expected downtime during ungraceful primary node failure is 28 seconds.
- Read replicas automatically elect a new leader and update DNS records via AWS Route53 private hosted zones.

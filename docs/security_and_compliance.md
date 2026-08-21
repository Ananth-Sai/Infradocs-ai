# Security & Compliance Policy

## 1. Data Encryption Standards
* **At-Rest Encryption**: All customer databases, backups, and block storage volumes are encrypted using **AES-256** keys managed via AWS KMS / HashiCorp Vault.
* **In-Transit Encryption**: Mandatory **TLS 1.3** is enforced on all external endpoints. Any legacy TLS 1.0/1.1 connections are automatically dropped at the Cloudflare edge proxy.

## 2. Authentication & Access Control
* **Multi-Factor Authentication (MFA)**: Hardware security keys (FIDO2 / WebAuthn) or TOTP authenticator apps are strictly required for all administrative access. SMS-based 2FA is prohibited due to SIM-swapping risks.
* **Password Expiration**: Passwords must be at least 16 characters long and expire every 90 days for privileged service accounts.

## 3. Compliance Certifications & Audit Logs
* The platform maintains annual certifications for **SOC 2 Type II**, **ISO/IEC 27001**, and **HIPAA Security Rule** compliance.
* Audit logs are immutable and retained in encrypted S3 Glacier storage for a mandatory period of **365 days** before deletion.

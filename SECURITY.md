# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

**We take security seriously.** If you discover a security vulnerability, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please email:
- **Email:** security@eckhardt-marketing.de
- **Subject:** [SECURITY] TechCare Bot - [Brief Description]

### What to Include

Please include:
1. **Description** of the vulnerability
2. **Steps to reproduce** (proof of concept)
3. **Impact assessment** (what can an attacker do?)
4. **Affected versions**
5. **Suggested fix** (if you have one)

### Response Time

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days
- **Fix Timeline:** Depends on severity
  - Critical: Within 24-48 hours
  - High: Within 7 days
  - Medium: Within 30 days
  - Low: Next release

### Disclosure Policy

- We follow **coordinated disclosure**
- We will notify you when the fix is released
- Please give us **90 days** before public disclosure
- We will credit you in the release notes (if desired)

### Severity Levels

**Critical:**
- Remote Code Execution (RCE)
- Authentication bypass
- Privilege escalation to admin

**High:**
- Data exposure (PII, API keys)
- SQL Injection
- Command Injection

**Medium:**
- XSS (if applicable)
- CSRF
- Denial of Service

**Low:**
- Information disclosure (non-sensitive)
- Minor security misconfigurations

### Security Best Practices for Users

1. **Always update** to the latest version
2. **Never share** your `.env` file or API keys
3. **Use strong API keys** from Anthropic
4. **Keep backups** before using repair tools
5. **Review commands** before approving with GO REPAIR
6. **Run in isolated environment** for testing

### Security Features

TechCare Bot includes:
- ✅ PII Detection & Anonymization (Microsoft Presidio)
- ✅ GO REPAIR execution lock (no autonomous repairs)
- ✅ Input validation (Pydantic schemas)
- ✅ No `shell=True` in subprocess calls
- ✅ Changelog for audit trail
- ✅ ToS acceptance with disclaimer

### Dependencies

We monitor dependencies for known vulnerabilities using:
```bash
pip-audit
```

If you find a vulnerable dependency, please report it.

### Hall of Fame

We recognize security researchers who help us:

- *No reports yet*

Thank you for helping keep TechCare Bot secure! 🔒

---

**Last Updated:** 2026-02-17

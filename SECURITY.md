# Security Policy

## Supported Versions

The following versions of Linite are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| latest (main) | ✅ Supported |
| older releases | ❌ Not supported |

We recommend always using the latest version from the `main` branch.

---

## Reporting a Vulnerability

We take the security of Linite seriously. If you believe you have found a security vulnerability, **please do not open a public GitHub issue.**

### How to Report

1. **Open a [GitHub Security Advisory](../../security/advisories/new)** — this is the preferred method and keeps the report private.
2. Alternatively, email the maintainers directly (see the project's `README.md` for contact information).

### What to Include

Please provide as much of the following as possible to help us triage and reproduce the issue:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Affected component(s) (e.g., `core/execution_engine.py`, package manager detection, etc.)
- Potential impact (privilege escalation, arbitrary command execution, data exposure, etc.)
- Any suggested mitigations or patches

### Response Timeline

| Stage | Target Timeframe |
|-------|-----------------|
| Initial acknowledgement | Within **48 hours** |
| Triage & severity assessment | Within **5 business days** |
| Fix or mitigation | Within **30 days** for critical issues |
| Public disclosure | Coordinated with reporter after fix is released |

---

## Security Considerations

Linite executes package manager commands (e.g., `apt`, `dnf`, `pacman`, `flatpak`, `snap`) on the user's system. Please keep the following in mind:

- **Script Export:** Exported installation scripts should be reviewed before execution on any system.
- **Package Sources:** Linite installs software from official distribution repositories and Flatpak/Snap sources. Always verify that your system repositories are trusted and up to date.
- **Privilege Escalation:** Some installations require `sudo`. Linite only requests elevated privileges when required by the underlying package manager.
- **Profile Files:** Custom profile TOML files loaded from external sources should be treated with caution, as they define packages to be installed.

---

## Disclosure Policy

We follow a **coordinated disclosure** model. We ask that you give us reasonable time to address a vulnerability before public disclosure. We will credit reporters in the release notes unless anonymity is requested.

---

## Out of Scope

The following are generally **not** considered security vulnerabilities within Linite's scope:

- Vulnerabilities in upstream packages installed by Linite (report these to the respective upstream projects)
- Issues requiring physical access to the machine
- Social engineering attacks
- Theoretical attacks without a practical proof of concept

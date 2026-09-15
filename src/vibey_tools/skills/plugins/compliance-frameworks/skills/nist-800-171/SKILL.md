---
name: nist-800-171
description: Use when working with NIST SP 800-171 CUI protection, DoD contracts, federal contractor compliance, or the 110 controls assessment. Helps navigate the 14 control families, assess compliance gaps, build remediation plans, and prepare SPRS score submissions. Trigger on any mention of CUI, 800-171, DFARS 252.204-7012, self-assessment, or contractor cybersecurity requirements.
---

# NIST SP 800-171 — CUI Protection for Non-Federal Systems

## What This Skill Does

This skill guides you through NIST SP 800-171 Revision 2 compliance: assessing, implementing, and documenting the 110 security requirements for protecting Controlled Unclassified Information (CUI) in non-federal systems and organizations. It covers all 14 control families, SPRS scoring, POA&M management, and the path to CMMC Level 2 compliance.

---

## Framework Overview

NIST SP 800-171r2 defines 110 security requirements organized into 14 families. These protect CUI handled by non-federal contractors and subcontractors under DFARS 252.204-7012. Unlike FISMA (which governs federal agencies), 800-171 governs contractors who process, store, or transmit CUI on behalf of the federal government.

**Key documents:**
- NIST SP 800-171r2 — the requirements standard
- NIST SP 800-171A — assessment procedures (the "how to audit" companion)
- DoD Assessment Methodology — scoring guidance for SPRS submission
- DFARS 252.204-7012 / 7019 / 7020 / 7021 — contract clauses that invoke 800-171

---

## The 14 Control Families

### 1. Access Control (AC) — 3.1.x — 22 controls
Limit system access to authorized users, devices, and processes. Enforce least privilege, separate duties, control remote access sessions, and manage mobile/wireless/external connections.

**Critical controls:**
- 3.1.1 — Limit access to authorized users and devices
- 3.1.2 — Limit access to permitted transactions and functions
- 3.1.5 — Employ least privilege including privileged accounts
- 3.1.12 — Monitor and control remote access sessions
- 3.1.13 — Encrypt remote access sessions cryptographically
- 3.1.17 — Protect wireless access with authentication and encryption


### 2. Awareness and Training (AT) — 3.2.x — 3 controls
Ensure managers, admins, and users understand security risks. Provide role-based training. Train on insider threat indicators.

- 3.2.1 — Security awareness for all system users
- 3.2.2 — Role-based training for security responsibilities
- 3.2.3 — Insider threat recognition and reporting

### 3. Audit and Accountability (AU) — 3.3.x — 9 controls
Create, retain, and protect audit logs. Ensure user actions are traceable. Alert on logging failures. Correlate events across systems.

**Critical controls:**
- 3.3.1 — Create and retain audit logs
- 3.3.2 — Ensure actions are uniquely traceable to users
- 3.3.5 — Correlate audit records for investigation
- 3.3.8 — Protect audit information from unauthorized access/modification

### 4. Configuration Management (CM) — 3.4.x — 9 controls
Establish baselines, enforce secure configurations, track changes, apply least functionality. Control user-installed software.

- 3.4.1 — Establish and maintain baseline configurations
- 3.4.2 — Enforce security configuration settings
- 3.4.6 — Least functionality (only essential capabilities)
- 3.4.8 — Application allowlisting/denylisting

### 5. Identification and Authentication (IA) — 3.5.x — 11 controls
Identify and authenticate users, processes, and devices before granting access. Enforce MFA. Manage passwords and credentials securely.

**Critical controls:**
- 3.5.1 — Identify all system users and devices
- 3.5.2 — Authenticate identities before granting access
- 3.5.3 — MFA for privileged accounts (local and network) and all non-privileged network accounts
- 3.5.10 — Store and transmit only cryptographically protected passwords


### 6. Incident Response (IR) — 3.6.x — 3 controls
Establish operational incident handling: preparation, detection, containment, recovery. Track and report incidents. Test the capability.

- 3.6.1 — Establish incident handling capability
- 3.6.2 — Track, document, and report incidents
- 3.6.3 — Test incident response capability

### 7. Maintenance (MA) — 3.7.x — 6 controls
Control maintenance activities, tools, and personnel. Require MFA for remote maintenance sessions. Sanitize equipment before off-site maintenance.

- 3.7.3 — Sanitize CUI from equipment before off-site maintenance
- 3.7.5 — MFA for nonlocal (remote) maintenance sessions

### 8. Media Protection (MP) — 3.8.x — 9 controls
Protect, limit access to, mark, and sanitize system media containing CUI. Control transport of media. Encrypt CUI on portable storage.

- 3.8.1 — Physically protect and securely store CUI media
- 3.8.3 — Sanitize or destroy media before disposal/reuse
- 3.8.6 — Encrypt CUI on digital media during transport

### 9. Personnel Security (PS) — 3.9.x — 2 controls
Screen individuals before granting system access. Protect systems during and after terminations and transfers.

- 3.9.1 — Screen individuals prior to access authorization
- 3.9.2 — Protect systems during terminations and transfers (revoke access promptly)

### 10. Physical Protection (PE) — 3.10.x — 6 controls
Limit physical access to authorized individuals. Monitor facilities. Escort visitors. Maintain physical access audit logs. Enforce CUI safeguards at alternate work sites.

- 3.10.1 — Limit physical access to authorized individuals
- 3.10.2 — Monitor physical facility and infrastructure
- 3.10.6 — Enforce CUI safeguards at alternate work sites (remote workers)

### 11. Risk Assessment (RA) — 3.11.x — 3 controls
Periodically assess risk. Scan for vulnerabilities. Remediate in accordance with risk assessments.

- 3.11.1 — Periodic organizational risk assessment
- 3.11.2 — Vulnerability scanning (periodic and when new vulns identified)
- 3.11.3 — Remediate vulnerabilities per risk assessment prioritization


### 12. Security Assessment (CA) — 3.12.x — 4 controls
Periodically assess security controls. Develop and implement POA&Ms. Monitor controls on an ongoing basis. Maintain system security plans.

- 3.12.1 — Periodically assess security control effectiveness
- 3.12.2 — Develop and implement plans of action (POA&Ms)
- 3.12.3 — Ongoing monitoring of security control effectiveness
- 3.12.4 — Develop and maintain system security plan (SSP)

### 13. System and Communications Protection (SC) — 3.13.x — 16 controls
Monitor and protect communications at boundaries. Architect for security. Encrypt CUI in transit and at rest. Prevent split tunneling. Use FIPS-validated cryptography.

**Critical controls:**
- 3.13.1 — Boundary protection: monitor/control at external and key internal boundaries
- 3.13.5 — DMZ/subnetworks for publicly accessible components
- 3.13.6 — Deny-by-default network communications
- 3.13.8 — Encrypt CUI in transit (TLS, VPN)
- 3.13.11 — FIPS-validated cryptography for CUI confidentiality
- 3.13.16 — Protect CUI at rest

### 14. System and Information Integrity (SI) — 3.14.x — 7 controls
Identify and correct flaws. Protect against malicious code. Monitor for attacks and unauthorized use. Update malicious code protections.

- 3.14.1 — Identify, report, and correct system flaws timely
- 3.14.2 — Malicious code protection at designated locations
- 3.14.6 — Monitor inbound and outbound traffic for attacks
- 3.14.7 — Identify unauthorized use of systems

---

## SPRS Score System

The **Supplier Performance Risk System (SPRS)** score represents a contractor's self-assessed compliance posture. DoD contractors must submit scores via SPRS before award and maintain them.

**Scoring methodology (DoD Assessment Methodology v1.2.1):**
- Maximum score: **110** (full compliance)
- Each of the 110 controls has a point value (most are 1 point; some multi-part controls are worth more)
- Start at 110; deduct points for each unmet control
- Negative scores are possible and reportable
- Formula: `SPRS Score = 110 - (sum of deductions for non-compliant controls)`

**Point deduction values:**
- 1-point controls: most basic controls
- 3-point controls: high-impact controls (MFA, encryption, audit logging, boundary protection)
- 5-point controls: critical controls (SSP, incident response capability)

**SPRS submission requirements:**
- Submit at: https://www.sprs.csd.disa.mil
- Required before contract award (DFARS 252.204-7019)
- Must reflect current state at time of submission
- DoD can request the supporting SSP for verification (DFARS 252.204-7020)


---

## Self-Assessment Methodology

### Step 1: Define System Boundary
- Identify all systems, networks, devices, and cloud services that process, store, or transmit CUI
- Document enclave boundary (what's in scope vs. out of scope)
- Map data flows for CUI: where does it enter, move, rest, and exit?
- Include all connected systems that could impact CUI confidentiality

### Step 2: Develop the System Security Plan (SSP)
- Document system name, purpose, boundary, and environment
- For each of the 110 controls: state MET, NOT MET, or NOT APPLICABLE with justification
- Describe how each met control is implemented (with specifics, not boilerplate)
- Required by 3.12.4; also required for DoD review under DFARS 252.204-7020

### Step 3: Collect Evidence
For each control, gather one or more of:
- **Examine:** Policies, procedures, configuration screenshots, system logs, network diagrams
- **Interview:** System owners, admins, security personnel (document responses)
- **Test:** Run scans, attempt access, verify configurations functionally

### Step 4: Gap Analysis
- List all NOT MET controls
- Categorize by family and by effort to remediate (quick win vs. major project)
- Calculate current SPRS score
- Identify highest-deduction gaps to prioritize

### Step 5: Build the POA&M
For each gap:
- Control ID and description
- Current weakness/deficiency
- Planned remediation action
- Milestones with target completion dates
- Responsible party
- Resources required (cost estimate)

### Step 6: Submit and Maintain
- Submit SPRS score reflecting current state (not target state)
- Update SSP and POA&M as controls are implemented
- Resubmit SPRS score after significant changes

---

## POA&M Structure

A Plan of Actions and Milestones documents unmet controls and the roadmap to address them.

**Required fields per POA&M item:**
```
Control ID:        3.5.3
Requirement:       Use multifactor authentication for local and network access to privileged accounts
Weakness:          MFA is not enforced for local privileged access on 12 workstations
Severity:          High (3-point deduction)
Scheduled Completion: 2024-03-31
Milestones:
  - 2024-01-15: Evaluate MFA solutions (Duo, Entra ID MFA, Okta)
  - 2024-02-15: Pilot deployment to 3 admin workstations
  - 2024-03-15: Full rollout to all privileged accounts
  - 2024-03-31: Evidence collected and SSP updated
Responsible Party: IT Manager
Resources:         $X licensing cost, 40 hours implementation
```


---

## Common Control Deficiencies and Remediation Patterns

### MFA Not Deployed (3.5.3) — High Impact
**Problem:** Password-only authentication for admin accounts.
**Remediation:** Deploy Microsoft Entra ID MFA, Duo Security, or Okta. Enforce Conditional Access policies requiring MFA for all privileged account access. Enforce for all network access to non-privileged accounts as well.
**Evidence:** MFA enrollment reports, Conditional Access policy screenshots, login audit logs.

### No Formal SSP (3.12.4) — High Impact
**Problem:** No documented System Security Plan.
**Remediation:** Use the NIST SP 800-171 SSP template. Document every control with implementation details, not just "yes/no." Include system boundary diagram.
**Evidence:** Completed SSP document with revision history.

### Vulnerability Scanning Not Occurring (3.11.2) — Medium Impact
**Problem:** No scheduled vulnerability scans.
**Remediation:** Deploy Tenable Nessus, Rapid7, or Qualys. Schedule authenticated scans weekly/monthly. Track findings in POA&M.
**Evidence:** Scan reports with timestamps, remediation tracking records.

### Audit Logging Gaps (3.3.1, 3.3.2) — High Impact
**Problem:** Logs not retained; user actions not traceable.
**Remediation:** Configure SIEM (Splunk, Microsoft Sentinel, Elastic). Ensure logs include user ID, timestamp, action, and outcome. Retain logs per policy (typically 1-3 years).
**Evidence:** SIEM configuration, log retention policy, sample log queries.

### Encryption at Rest Missing (3.13.16) — High Impact
**Problem:** CUI stored on unencrypted drives or in unencrypted databases.
**Remediation:** Enable BitLocker (Windows), FileVault (macOS), or cloud provider encryption (AWS KMS, Azure Disk Encryption). Encrypt database columns or tablespaces containing CUI.
**Evidence:** Encryption configuration screenshots, key management documentation.

### No Incident Response Plan (3.6.1) — High Impact
**Problem:** No documented IR procedures.
**Remediation:** Write an IRP covering: preparation, detection, containment, eradication, recovery, and lessons learned. Assign IR roles. Test annually with tabletop exercise.
**Evidence:** IRP document, tabletop exercise records, incident log.

### Least Privilege Not Enforced (3.1.5) — Medium Impact
**Problem:** Users have excessive permissions; no privileged account separation.
**Remediation:** Conduct access review. Remove unnecessary admin rights. Require separate admin accounts for privileged tasks. Implement PAM tools (CyberArk, BeyondTrust) for enterprise environments.
**Evidence:** Access review records, account inventory, PAM configuration.

---

## Relationship to CMMC Level 2

CMMC (Cybersecurity Maturity Model Certification) Level 2 requires full compliance with all 110 NIST SP 800-171 controls. There is a direct one-to-one mapping.

**CMMC 2.0 structure:**
- Level 1: 17 practices (basic cyber hygiene, FCI protection)
- Level 2: 110 practices = all 110 NIST 800-171 controls (CUI protection)
- Level 3: 110 + 24 additional NIST 800-172 practices (advanced/critical CUI)

**Assessment requirements for Level 2:**
- Self-assessment: Allowed for some Level 2 contracts (DFARS 252.204-7019)
- C3PAO third-party assessment: Required for contracts that require Level 2 certification
- Government-led (DIBCAC): Required for Level 3 and high-priority Level 2

**If you are working toward CMMC Level 2:** achieving full 110-control compliance with NIST 800-171 IS CMMC Level 2 compliance. No additional controls are needed beyond what 800-171 requires.


---

## Quick-Reference: All 110 Controls by Family

| Family | ID Range | Count | Key Concerns |
|--------|----------|-------|--------------|
| Access Control | 3.1.1–3.1.22 | 22 | Least privilege, remote access, MFA, wireless |
| Awareness & Training | 3.2.1–3.2.3 | 3 | User training, role-based training, insider threat |
| Audit & Accountability | 3.3.1–3.3.9 | 9 | Log creation, retention, protection, correlation |
| Config Management | 3.4.1–3.4.9 | 9 | Baselines, change control, least functionality |
| Identification & Auth | 3.5.1–3.5.11 | 11 | MFA, password policy, credential storage |
| Incident Response | 3.6.1–3.6.3 | 3 | IRP, tracking, testing |
| Maintenance | 3.7.1–3.7.6 | 6 | Controlled maintenance, remote maintenance MFA |
| Media Protection | 3.8.1–3.8.9 | 9 | Physical protection, sanitization, transport encryption |
| Personnel Security | 3.9.1–3.9.2 | 2 | Screening, termination procedures |
| Physical Protection | 3.10.1–3.10.6 | 6 | Physical access, monitoring, alternate work sites |
| Risk Assessment | 3.11.1–3.11.3 | 3 | Risk assessments, vuln scanning, remediation |
| Security Assessment | 3.12.1–3.12.4 | 4 | Control assessments, POA&M, SSP, monitoring |
| System & Comms Protection | 3.13.1–3.13.16 | 16 | Boundary protection, encryption in transit/at rest, FIPS |
| System & Info Integrity | 3.14.1–3.14.7 | 7 | Patch management, AV/EDR, monitoring, flaw remediation |

---

## Assessment Conversation Starters

When a user asks about 800-171 compliance, start by asking:

1. **"Do you have a System Security Plan (SSP) that documents all 110 controls?"**
   - No SSP = start there; it is both 3.12.4 and the foundation for scoring

2. **"Have you defined your CUI boundary — what systems touch CUI?"**
   - Undefined boundary = you can't scope the assessment correctly

3. **"What is your current SPRS score, and when was it last submitted?"**
   - This reveals overall posture and whether they are contractually compliant

4. **"Which families have the most NOT MET controls?"**
   - Common answers: IA (MFA), SC (encryption), AU (logging), CA (no SSP/POA&M)

5. **"Do you have a POA&M tracking open gaps with dates?"**
   - No POA&M = cannot demonstrate active remediation effort to auditors

---

## Evidence Checklist for Common Controls

**For MFA (3.5.3):**
- [ ] MFA enrollment report (100% of privileged accounts)
- [ ] MFA enrollment report (100% of non-privileged accounts for network access)
- [ ] Conditional Access or equivalent policy screenshot
- [ ] Exception process if any accounts are excluded

**For Encryption in Transit (3.13.8):**
- [ ] Network diagram showing where TLS is enforced
- [ ] TLS configuration (minimum TLS 1.2, cipher suites)
- [ ] VPN configuration for remote access
- [ ] Certificate inventory

**For Audit Logging (3.3.1):**
- [ ] Log retention policy (minimum period defined)
- [ ] SIEM/log aggregation configuration
- [ ] Evidence logs include: user ID, timestamp, event, outcome
- [ ] Alert configuration for anomalous events

**For Vulnerability Management (3.11.2, 3.14.1):**
- [ ] Vulnerability scan schedule and tool configuration
- [ ] Most recent scan report
- [ ] Remediation SLAs (critical within X days)
- [ ] Patch management policy and records


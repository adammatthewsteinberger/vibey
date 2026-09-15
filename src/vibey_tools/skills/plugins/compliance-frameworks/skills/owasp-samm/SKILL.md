---
name: owasp-samm
description: Use when assessing software security maturity, planning security program improvements, conducting OWASP SAMM assessments, or building a security champion program. Triggers on software assurance maturity model, AppSec program, security roadmap, security maturity assessment, SAMM scoring, or requests to improve developer security practices. Also use when someone asks how to build or measure their application security program.
---

# OWASP SAMM v2 — Software Assurance Maturity Model

## What This Skill Does

This skill guides you through OWASP SAMM v2 assessments: scoring your current security maturity, identifying quick wins and structural gaps, building 6-month and 12-month improvement roadmaps, and integrating security practices into Agile/DevSecOps workflows. It covers all 15 security practices across the 5 business functions.

---

## SAMM v2 Structure Overview

OWASP SAMM v2 organizes software security into a three-tier hierarchy:

```
5 Business Functions
  └── 3 Security Practices per function = 15 Practices total
        └── 2 Streams per practice = 30 Streams total
              └── 3 Maturity Levels per stream (0 = not started, 1 = foundational, 2 = structured, 3 = optimized)
```

**Overall score:** Average maturity across all 15 practices, ranging 0.0–3.0.

**Typical scores:**
- 0.0–0.5: Security is informal or absent
- 0.5–1.0: Beginning to establish basic practices
- 1.0–1.5: Foundational practices in place; inconsistently applied
- 1.5–2.0: Structured practices; most teams follow them
- 2.0–2.5: Mature, consistent, measured security program
- 2.5–3.0: Optimizing; continuous improvement; industry-leading

---

## Business Function 1: Governance

### Practice G1: Strategy and Metrics
Establish security objectives, strategy, and metrics to track program effectiveness.

**Level 1 (Foundational):** Identify security champion or owner. Understand which regulations apply. Track a few basic metrics (e.g., number of vulnerabilities found in pen tests).

**Level 2 (Structured):** Documented security strategy aligned to business risk. KPIs for security program (MTTR for vulns, % of apps with pen test, training completion). Security objectives communicated across teams.

**Level 3 (Optimized):** Security metrics tied to business outcomes. Continuous improvement cycle driven by data. Security strategy reviewed and updated annually with executive sponsorship.

### Practice G2: Policy and Compliance
Develop and enforce security policies. Track compliance with internal and external requirements.

**Level 1:** Basic security policies documented (acceptable use, password policy). Awareness of applicable compliance frameworks (SOC 2, PCI, HIPAA, etc.).

**Level 2:** Comprehensive policy set published, version-controlled, and reviewed annually. Compliance tracking dashboard. Policy exceptions process with approval and risk acceptance.

**Level 3:** Automated compliance monitoring. Policies continuously updated to address new threats and regulations. Audit trail of policy adherence.

### Practice G3: Education and Guidance
Provide security training and guidance to developers, architects, and operations.

**Level 1:** Annual security awareness training for all staff. Basic secure coding guidelines available.

**Level 2:** Role-based security training (developers get OWASP Top 10 training; architects get threat modeling training; ops gets configuration security training). Security champion program established in development teams.

**Level 3:** Hands-on, application-specific training (e.g., secure coding workshops for your tech stack). Continuous learning through lunch & learns, capture-the-flag, brown bags. Security champions are empowered and recognized.


---

## Business Function 2: Design

### Practice D1: Threat Assessment
Identify threats to applications and systems as part of the design process.

**Level 1:** Ad hoc threat identification for high-risk features. At least a basic question list: "What could go wrong? Who might attack this? What data is sensitive?"

**Level 2:** Structured threat modeling process (STRIDE, PASTA, or attack tree) for all new features and significant changes. Threats documented and linked to security requirements. Threat models reviewed by security team.

**Level 3:** Threat modeling is fully integrated into design sprints. Automated tooling assists (e.g., OWASP Threat Dragon, Microsoft TMT). Historical threat data feeds future models. Risk-ranked threat catalog maintained.

### Practice D2: Security Requirements
Define and track security requirements as a first-class concern in feature development.

**Level 1:** Security requirements exist for the most critical features (authentication, authorization, encryption). Checked manually during code review.

**Level 2:** Security requirements library aligned to OWASP ASVS or internal standards. Requirements attached to user stories in sprint backlog. Definition of Done includes security requirement sign-off.

**Level 3:** Automated requirements traceability. Security requirements derived from threat models and compliance obligations. Metrics on requirement coverage and fulfillment.

### Practice D3: Security Architecture
Design systems with security as a structural concern, not an add-on.

**Level 1:** Security architecture principles documented (e.g., least privilege, defense in depth, input validation, fail securely). Applied informally.

**Level 2:** Reference architectures for common patterns (authentication, API security, data storage, microservices). Architecture review for new systems and significant changes. Security architects involved in design decisions.

**Level 3:** Security architecture governance process. Architecture decisions recorded (ADRs). Reusable security components and libraries provided to developers. Continuous architecture review as systems evolve.

---

## Business Function 3: Implementation

### Practice I1: Secure Build
Integrate security into the build and CI/CD pipeline.

**Level 1:** Basic dependency management (know what third-party libraries you use). Some developers use linters. Source control in use for all code.

**Level 2:** Static Application Security Testing (SAST) integrated into CI pipeline. Software Composition Analysis (SCA) for third-party dependency vulnerabilities. Build fails (or alerts) on high-severity findings. Secrets scanning active (no hardcoded credentials).

**Level 3:** SAST, SCA, secrets scanning, and IaC security scanning all integrated and blocking on critical/high. Developers receive actionable security findings at commit time. Security findings tracked and measured over time. Build pipeline itself is secured and audited.

**Key tools:**
- SAST: Semgrep, SonarQube, CodeQL, Checkmarx, Snyk Code
- SCA: Snyk, OWASP Dependency-Check, Dependabot, JFrog Xray
- Secrets: GitGuardian, TruffleHog, detect-secrets
- IaC: Checkov, tfsec, KICS, Terrascan

### Practice I2: Secure Deployment
Harden deployment processes and infrastructure configurations.

**Level 1:** Environment separation (dev/staging/prod). No production secrets in source code. Basic change management for production deployments.

**Level 2:** Infrastructure as Code (IaC) with security configuration checks. Container image scanning before deployment. Deployment approvals required for production. Environment configurations audited against CIS Benchmarks.

**Level 3:** Immutable infrastructure. All deployments via automated, audited pipeline. Runtime security monitoring (CWPP, Falco). Zero-trust network architecture. Automated drift detection and remediation.

### Practice I3: Defect Management
Track, prioritize, and remediate security defects systematically.

**Level 1:** Security bugs tracked in the same system as functional bugs. Critical security vulnerabilities are prioritized above feature work.

**Level 2:** Security defect SLAs defined by severity (Critical: 24h; High: 7 days; Medium: 30 days; Low: 90 days). Security backlog visible to engineering leadership. Trend metrics tracked (are we finding and fixing more over time?).

**Level 3:** Automated vulnerability management workflow (scanner finds → ticket created → assigned → tracked to closure). Root cause analysis for recurring vulnerability classes. Vulnerability density metrics by team and application.


---

## Business Function 4: Verification

### Practice V1: Architecture Assessment
Verify that application architecture meets security requirements and threat model findings.

**Level 1:** Informal security review of major new systems or significant architecture changes. Checklist-based: authentication handled correctly? Authorization enforced? Sensitive data encrypted?

**Level 2:** Formal architecture review process with documented findings and sign-off. Security architect involvement in design reviews. Architecture review aligned to threat model.

**Level 3:** Continuous architecture review integrated with change management. Automated architecture compliance checking (e.g., policy-as-code for cloud infrastructure). Findings fed back into design standards.

### Practice V2: Requirements-Driven Testing
Test security requirements, not just functionality.

**Level 1:** Pen tester or security team reviews the application for OWASP Top 10 vulnerabilities. Security test cases exist for authentication and authorization.

**Level 2:** Security test cases written from security requirements and threat model. Security testing integrated into QA process. DAST (Dynamic Application Security Testing) running against staging environments.

**Level 3:** Comprehensive security test suite covering OWASP ASVS verification requirements. Security regression tests prevent re-introduction of fixed vulnerabilities. Fuzz testing for critical input handlers.

**Key tools:**
- DAST: OWASP ZAP, Burp Suite, Invicti, Detectify
- API testing: Postman with security tests, OWASP ZAP API scan
- Fuzz testing: AFL++, libFuzzer, RESTler

### Practice V3: Security Testing
Conduct dedicated security testing beyond functional testing.

**Level 1:** Annual penetration test by internal team or third party. OWASP Top 10 coverage. Critical findings remediated before next release.

**Level 2:** Annual external penetration test + ongoing internal testing. Bug bounty or vulnerability disclosure program considered. Pre-release security reviews for major features. DAST running continuously against staging.

**Level 3:** Continuous automated security testing in CI/CD (SAST + DAST + SCA). Regular penetration tests with retesting of remediated findings. Bug bounty program active. Red team exercises for critical systems. Security chaos engineering.

---

## Business Function 5: Operations

### Practice O1: Incident Management
Detect, respond to, and learn from security incidents in production.

**Level 1:** Incident response plan exists. Security events logged. Basic alerting for obvious attacks (failed logins, malware alerts). On-call process includes security escalation path.

**Level 2:** SIEM with tuned detection rules. IR runbooks for common incident types. Post-incident reviews conducted. Incident metrics tracked (MTTD, MTTR). Security team notified within defined SLA.

**Level 3:** Advanced threat detection (UEBA, behavioral analytics). Purple team exercises to validate detection capability. Automated response playbooks (SOAR). Threat intelligence integration. Regular IR drills and red team exercises.

### Practice O2: Environment Management
Maintain secure configurations across all environments throughout the software lifecycle.

**Level 1:** Hardened base images for servers and containers. Basic configuration management (manual or scripted). Known default credentials changed.

**Level 2:** CIS Benchmark compliance for all infrastructure. Configuration drift detection (Chef InSpec, AWS Config, Azure Policy). Automated patching or patch tracking with SLAs. Vulnerability scanning of production infrastructure.

**Level 3:** Policy-as-code enforcement across all environments. Immutable infrastructure eliminates configuration drift. Continuous compliance monitoring with automated remediation. Cloud security posture management (CSPM) tools deployed.

### Practice O3: Operational Management
Integrate security into operational processes: change management, access management, data management.

**Level 1:** Access reviews conducted periodically. Sensitive data locations identified. Basic data retention policy.

**Level 2:** Privileged access management (PAM). Data classification applied to production data. Operational runbooks include security considerations. Vendor access reviewed and limited.

**Level 3:** Just-in-time privileged access. Automated data discovery and classification. Security integrated into all operational runbooks. Supply chain security practices (software bill of materials, SBOM). Operational security KPIs measured and reported.


---

## Assessment Methodology

### Conducting a SAMM Assessment

**Step 1: Scope definition**
- Define which applications and teams are in scope
- Decide if this is an organization-wide assessment or application-specific
- Identify key stakeholders to interview (dev leads, security team, ops, management)

**Step 2: Evidence gathering**
For each of the 15 practices, collect evidence:
- Policy/process documents
- Tool configurations and outputs
- Training records
- Meeting notes, retrospective records
- Metrics and dashboards

**Step 3: Score each practice (0–3)**
For each practice and stream, determine the level achieved:
- Level 0: Practice not performed
- Level 1: Ad hoc; informally performed; not consistently applied
- Level 2: Defined process; consistently applied; documented
- Level 3: Measured; optimized; continuously improved

**A level is only achieved if ALL activities at that level are consistently performed.** Partial credit is not typical in strict SAMM assessments, though some organizations use fractional scores.

**Step 4: Produce the scorecard**
Create a radar chart or heatmap showing scores by business function and practice. This becomes the baseline for improvement planning.

**Step 5: Gap analysis and roadmap**
- Identify the highest-value improvements (biggest risk reduction per unit of effort)
- Build a phased roadmap (6-month and 12-month targets)
- Focus on raising the floor (Level 0 → 1) before optimizing (Level 2 → 3)

---

## SAMM Score Reference: 15 Practices Summary Table

| Function | Practice | Stream A Focus | Stream B Focus |
|----------|----------|----------------|----------------|
| Governance | Strategy & Metrics | Security strategy | Metrics & reporting |
| Governance | Policy & Compliance | Policy framework | Compliance management |
| Governance | Education & Guidance | Training programs | Security champions |
| Design | Threat Assessment | Threat modeling | Attack surface analysis |
| Design | Security Requirements | Requirements definition | Supplier security |
| Design | Security Architecture | Architecture design | Technology management |
| Implementation | Secure Build | Build process security | Software dependency mgmt |
| Implementation | Secure Deployment | Deployment hardening | Secret management |
| Implementation | Defect Management | Defect tracking | Metrics & feedback |
| Verification | Architecture Assessment | Architecture validation | Compliance verification |
| Verification | Requirements-Driven Testing | Test cases from requirements | Regression testing |
| Verification | Security Testing | Pen testing | Automated scanning |
| Operations | Incident Management | Incident detection | Incident response |
| Operations | Environment Management | Configuration hardening | Patch management |
| Operations | Operational Management | Operational processes | Change management |

---

## Starting Points by Organization Type

### Startup (< 50 engineers, pre-SOC2/compliance pressure)
**Realistic starting score:** 0.2–0.5 across most practices

**Priority Level 1 quick wins (do these first):**
1. G3 — Security awareness training: 1-hour OWASP Top 10 session for all developers
2. I1 — Secure build: Add Dependabot/Snyk to GitHub repos; add secrets scanning
3. I3 — Defect management: Create a security label in Jira; agree on severity SLAs
4. O1 — Incident management: Write a 1-page IRP; know who to call when something goes wrong
5. V3 — Security testing: Schedule one annual pen test

**6-month target score:** 1.0 across most practices

### Growing SaaS (50–200 engineers, SOC2 in progress or complete)
**Realistic starting score:** 0.8–1.2

**Priority Level 2 improvements:**
1. G2 — Policy and compliance: Full policy set; annual review cycle
2. D1 — Threat assessment: Introduce threat modeling for all significant new features
3. I1 — Secure build: SAST and SCA integrated into CI pipeline with blocking on critical
4. V3 — Security testing: DAST running against staging; annual pen test with retest
5. O2 — Environment management: CIS Benchmark compliance for cloud infrastructure

**12-month target score:** 1.5 across most practices; 2.0 in highest-risk areas

### Enterprise (200+ engineers, mature DevSecOps, regulated industry)
**Realistic starting score:** 1.5–2.0

**Priority Level 3 improvements:**
1. I1 — Secure build: All security gates in pipeline; findings tracked and measured
2. V3 — Security testing: Bug bounty or continuous pen testing; red team exercises
3. O1 — Incident management: SOAR automation; MTTD/MTTR measured and improving
4. D1 — Threat assessment: Automated threat modeling tooling; historical threat catalog
5. G1 — Strategy & metrics: Security metrics in executive dashboards; OKRs for security


---

## Security Champions Program (G3 — Level 2)

The Security Champions program is one of the highest-ROI investments for growing organizations. It scales security expertise across engineering teams without requiring a security engineer on every team.

### What a Security Champion Does
- Acts as the security point of contact for their development team
- Reviews PRs for security-sensitive changes (auth, crypto, input validation, authorization)
- Raises security concerns in sprint planning and design reviews
- Helps triage security scanner findings
- Bridges between the security team and the development team
- Stays current on threats relevant to your tech stack

### What a Security Champion is NOT
- They are NOT a full-time security role
- They are NOT responsible for all security — the security team still owns the program
- They should NOT be expected to be a penetration tester

### Building the Program
1. **Identify volunteers:** Ask for developers with security interest, not reluctant assignees
2. **Define time commitment:** Typically 10-20% of their time; must be acknowledged by their manager
3. **Training:** Provide application security training (OWASP, SANS DEV courses, Secure Code Warrior)
4. **Regular syncs:** Monthly champion meeting to share findings, threats, and wins
5. **Recognition:** Feature champions in company communications; conference attendance as a perk
6. **Metrics:** Track security findings caught by champions vs. discovered later

---

## Integrating SAMM with Agile/Scrum Sprints

Security practices can be embedded into existing Agile ceremonies without creating separate security overhead.

### Sprint Planning
- Security requirements appear as acceptance criteria on user stories
- "Threat model reviewed" as a Definition of Ready criterion for security-sensitive stories
- Security champion reviews backlog for high-risk items

### Sprint Execution
- SAST, SCA, secrets scanning run on every commit (automated, fast feedback)
- Developers fix security findings in the same sprint they introduce them
- Security champion available for pairing on security-sensitive code

### Sprint Review / Demo
- Security-sensitive features demonstrate how security controls work (show the auth, show the audit log)
- Security defects shown alongside functional bugs in velocity metrics

### Sprint Retrospective
- "Did any security issues come up this sprint? How did we handle them?"
- Security improvement tasks added to team backlog

### Definition of Done (Security Additions)
- [ ] SAST scan passed (no new high/critical findings unreviewed)
- [ ] Dependencies checked (no new high/critical CVEs unreviewed)
- [ ] Security requirements from story met
- [ ] Sensitive data handling reviewed
- [ ] Security champion notified for security-sensitive changes

---

## Relationship to Other Frameworks

| Framework | Relationship to SAMM |
|-----------|---------------------|
| NIST SSDF (SP 800-218) | Similar structure; SSDF is NIST's software security framework; strong SAMM-SSDF mapping available |
| ISO 27001 | SAMM complements ISO 27001 Annex A controls related to SDLC (A.8.25–A.8.31 in 27001:2022) |
| BSIMM | BSIMM (Building Security In Maturity Model) is an observational model of what companies DO; SAMM is prescriptive about what they SHOULD do; often used together |
| CMMC / NIST 800-171 | SAMM addresses software assurance; CMMC addresses system/network security; complementary, not overlapping |
| PCI DSS | SAMM directly supports PCI DSS Req 6 (secure systems and software) and Req 11 (security testing) |
| SOC 2 | SAMM Level 1-2 practices align to SOC 2 CC8 (change management), CC7 (monitoring), and CC5 (control activities) |
| OWASP ASVS | ASVS defines verification requirements for applications; SAMM V2 (Requirements-Driven Testing) uses ASVS as a test case library |

---

## SAMM Roadmap Template

### 6-Month Plan (Establishing Foundations — Level 0 → 1)

| Month | Focus Area | Actions |
|-------|-----------|---------|
| 1 | Governance | Complete SAMM assessment; assign security owner; write security policy |
| 1-2 | Implementation | Add Snyk/Dependabot and secrets scanning to all repos |
| 2-3 | Verification | Schedule annual pen test; create security bug label in tracker |
| 3-4 | Operations | Write IRP; define incident severity levels; test once |
| 4-5 | Design | Run first threat modeling session on highest-risk component |
| 5-6 | Governance | Launch security champion program (2-3 volunteers); first training |

### 12-Month Plan (Deepening Practices — Level 1 → 2)

| Month | Focus Area | Actions |
|-------|-----------|---------|
| 7-8 | Implementation | Integrate SAST into CI; block on critical findings |
| 8-9 | Design | Threat modeling for all new features; security requirements in DoD |
| 9-10 | Verification | DAST against staging; security test cases for auth and authz |
| 10-11 | Operations | CIS Benchmark compliance for cloud infra; vulnerability scan production |
| 11-12 | Governance | Full policy set complete; annual review cycle; metrics dashboard |


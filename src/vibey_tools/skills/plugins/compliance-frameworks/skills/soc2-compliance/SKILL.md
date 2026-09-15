---
name: soc2-compliance
description: Use when working on SOC2 Type 1 or Type 2 readiness, TSC (Trust Services Criteria) gap analysis, policy development, or mapping controls to NIST 800-53. Covers the 5 TSC categories, minimum policy set, evidence collection, and audit preparation. Trigger on any mention of SOC2, SOC 2, Trust Services Criteria, AICPA, Type 1, Type 2, or auditor readiness.
---

# SOC 2 Compliance — Trust Services Criteria

## What This Skill Does

This skill guides you through SOC 2 Type 1 and Type 2 readiness: understanding the Trust Services Criteria (TSC), identifying the minimum required policy set, collecting evidence for auditors, and mapping SOC 2 controls to NIST 800-53. It covers common gaps in SaaS and cloud environments and provides actionable audit preparation checklists.

---

## Framework Overview

SOC 2 is an AICPA (American Institute of Certified Public Accountants) framework for reporting on the internal controls of service organizations. It is NOT a certification — it is an audit-based attestation report.

**Types of SOC 2 reports:**
- **Type 1:** Point-in-time assessment. The auditor opines that controls are suitably designed as of a specific date. Faster (2-4 months); lower cost; limited assurance.
- **Type 2:** Period-based assessment (typically 6-12 months). The auditor opines that controls are suitably designed AND operated effectively over the audit period. Higher assurance; required by most enterprise customers and regulated industries.

**Who needs SOC 2:**
- SaaS companies that handle customer data
- Cloud infrastructure and managed service providers
- Any B2B technology company responding to enterprise security questionnaires
- Companies handling healthcare, financial, or government data (often required)

**The report is:**
- Issued by a licensed CPA firm (not a consultant or certifying body)
- Scoped to specific Trust Service Categories elected by management
- Shared under NDA with customers and prospects

---

## The Five Trust Service Categories (TSC)

### Security (CC — Common Criteria) — ALWAYS REQUIRED
The foundational category. Every SOC 2 report must include Security. The Common Criteria (CC) covers logical and physical access controls, change management, risk management, and monitoring.

Security is organized into CC1–CC9 subcriteria:

**CC1: Control Environment**
- Commitment to integrity and ethical values (tone at the top)
- Board/management oversight of security program
- Organizational structure and reporting lines

**CC2: Communication and Information**
- Internal communication of security responsibilities
- External communication to relevant parties about security obligations

**CC3: Risk Assessment**
- Identify and analyze risks to achieving security objectives
- Fraud risk assessment
- Changes to systems/processes that create new risks

**CC4: Monitoring Activities**
- Ongoing and separate evaluations of controls
- Deficiency identification and remediation

**CC5: Control Activities (Policies)**
- Selection and development of controls
- Technology controls (general IT controls)
- Policy deployment and enforcement


**CC6: Logical and Physical Access Controls**
- User access provisioning, de-provisioning, and reviews
- Principle of least privilege
- Multi-factor authentication
- Physical facility access controls
- Encryption of data at rest and in transit
- Network security and segmentation

**CC7: System Operations**
- Detection and monitoring of new vulnerabilities
- System monitoring and anomaly detection
- Incident identification and response
- Change management and infrastructure reliability

**CC8: Change Management**
- Controlled change process (development → testing → production)
- Software development lifecycle controls
- Infrastructure change controls
- Emergency change procedures

**CC9: Risk Mitigation**
- Risk treatment and mitigation strategies
- Vendor/third-party risk management (subservice organizations)
- Business disruption risk

### Availability (A) — Optional
The system is available for operation and use as committed or agreed.

Covers: uptime SLA commitments, redundancy and failover, backup and recovery, capacity management, incident response for availability events, DR testing.

**Include if:** You have SLA commitments to customers; customers depend on uptime for their operations; you are a SaaS platform where downtime = customer revenue loss.

### Processing Integrity (PI) — Optional
System processing is complete, accurate, timely, and authorized.

Covers: Input validation, processing controls, error handling, output accuracy, transactional completeness, anomaly detection in processing.

**Include if:** You process financial transactions, payroll, healthcare data processing, or any workflow where processing errors have material consequences.

### Confidentiality (C) — Optional
Information designated as confidential is protected as committed or agreed.

Covers: Data classification, confidentiality agreements (NDAs), encryption of confidential data, access restrictions to confidential information, secure disposal.

**Include if:** You handle customer-designated confidential data, IP, trade secrets, or regulated data categories where confidentiality is a contractual or regulatory obligation.

### Privacy (P) — Optional
Personal information is collected, used, retained, disclosed, and disposed of in conformity with the entity's privacy notice and GAPP.

Covers: Notice and consent, data collection limitation, use/retention/disposal, access to personal data, disclosure to third parties, security of personal data.

**Include if:** You collect or process personal information and have made privacy commitments (GDPR alignment, CCPA compliance, etc.).


---

## Minimum Policy Set for SOC 2 Type 2

The following policies are required to satisfy the Common Criteria and any additional TSC categories elected. These come from the SOC2-Type2 Minimum Policy Set documentation.

### 1. Information Security Policy
The overarching policy defining the organization's approach to information security.
- Roles and responsibilities for information security
- Acceptable use rules for systems and data
- Consequences for policy violations
- Annual review and update process
- Executive sign-off and communication to all personnel

### 2. Access Control Policy
Defines who has access to what information and the procedures for granting and revoking access.
- User provisioning and de-provisioning process
- Principle of least privilege requirements
- Access review frequency (quarterly for privileged; semi-annual for standard)
- Segregation of duties requirements
- Privileged access management rules
- Remote access controls

### 3. Data Encryption Policy
Outlines how and when data is encrypted, both at rest and in transit.
- Encryption standards (AES-256 at rest; TLS 1.2+ in transit)
- Key management and rotation schedule
- Encryption requirements for portable devices and storage media
- Certificate management procedures

### 4. Incident Response Policy
Details how to respond to a security incident.
- Incident classification and severity definitions
- Roles and responsibilities (IR team)
- Incident detection and reporting procedures
- Containment, eradication, and recovery steps
- Communication plan (internal; customer notification)
- Post-incident review and lessons learned
- Retention of incident records

### 5. Disaster Recovery and Business Continuity Plan (BCP/DRP)
Outlines how the organization recovers from a disaster or significant event.
- Business impact analysis (BIA) with RTO/RPO for critical systems
- Recovery procedures per system/service
- Backup strategy and verification
- DR testing schedule (annual minimum for Type 2)
- Communication and escalation tree

### 6. Change Management Policy
Controls how changes to the IT environment are requested, approved, tested, and deployed.
- Change request and approval workflow
- Separation of duties: developers cannot deploy to production unilaterally
- Testing requirements before promotion to production
- Emergency change procedures
- Rollback procedures
- Change log maintenance

### 7. Risk Assessment Policy
Outlines how risks are identified, evaluated, and mitigated.
- Risk assessment methodology and frequency (annual minimum)
- Risk scoring criteria (likelihood × impact)
- Risk acceptance criteria
- Risk treatment options (accept, mitigate, transfer, avoid)
- Risk register ownership and maintenance

### 8. Vendor Management Policy
Governs evaluation and monitoring of third-party vendors.
- Vendor risk tiering (critical, significant, standard)
- Security due diligence requirements by tier
- Contract requirements (security obligations, audit rights, breach notification)
- Annual review of critical vendors
- Subservice organization monitoring (for SOC 2 carve-out or inclusive reports)


### 9. Data Backup Policy
Outlines how and when data is backed up, and how it can be restored.
- Backup frequency per data classification/criticality
- Backup storage location (offsite/cloud)
- Encryption of backups
- Restoration testing frequency (quarterly recommended)
- Retention periods

### 10. Network Security Policy
Documents network protection controls.
- Firewall and network segmentation requirements
- Intrusion detection/prevention systems
- Wireless network controls
- Network monitoring and alerting
- Remote access VPN requirements

### 11. Data Retention and Disposal Policy
Governs how long data is kept and how it is securely disposed of.
- Retention periods by data category
- Legal hold procedures
- Secure disposal methods (shredding, NIST 800-88 media sanitization)
- Records of destruction

### 12. Privacy Policy (if Privacy TSC selected)
Covers collection, use, retention, disclosure, and disposal of personal information.
- Data subject rights (access, deletion, correction)
- Cookie and tracking disclosures
- Third-party sharing disclosures
- Data breach notification commitments

---

## Control Mapping: SOC 2 Common Criteria to NIST 800-53

SOC 2 auditors increasingly expect organizations to be able to map their controls to established frameworks. The mapping from TSC to NIST 800-53 is published by the AICPA.

| SOC 2 Criteria | NIST 800-53 Control Families |
|----------------|------------------------------|
| CC1 (Control Environment) | PM (Program Management), AT (Awareness & Training) |
| CC2 (Communication) | PL (Planning), PM |
| CC3 (Risk Assessment) | RA (Risk Assessment), PM |
| CC4 (Monitoring) | CA (Assessment), AU (Audit) |
| CC5 (Control Activities) | PL, SA (System Acquisition), PM |
| CC6.1 (Logical Access — Identification) | IA (Identification & Authentication) |
| CC6.2 (Logical Access — Provisioning) | AC (Access Control) |
| CC6.3 (Role-Based Access) | AC |
| CC6.6 (External Threats — Boundary) | SC (System & Comms Protection), SI |
| CC6.7 (Encryption) | SC, MP (Media Protection) |
| CC6.8 (Malware Protection) | SI |
| CC7.1 (Vulnerability Management) | RA, SI, CA |
| CC7.2 (Monitoring) | AU, SI, IR |
| CC7.3–CC7.5 (Incident Response) | IR (Incident Response) |
| CC8 (Change Management) | CM (Configuration Management), SA |
| CC9 (Risk Mitigation / Vendors) | SA-9, PM |
| A1 (Availability) | CP (Contingency Planning), SC |
| PI1 (Processing Integrity) | SI, AU |
| C1 (Confidentiality) | AC, SC, MP |
| P1–P8 (Privacy) | PT (PII Processing) |


---

## Evidence Collection for Auditors

SOC 2 auditors (for Type 2) will request evidence of control operation over the entire audit period. Evidence must be dated to show it occurred during the period under review.

### Access Control Evidence
- [ ] User access list with roles — point in time + evidence of periodic review
- [ ] Terminated employee access revocation records (show prompt deprovisioning)
- [ ] MFA enrollment confirmation for all users
- [ ] Privileged access request and approval tickets
- [ ] Access review documentation (reviewer sign-off, date, actions taken)
- [ ] New employee access provisioning records

### Change Management Evidence
- [ ] Git commit history and pull request approvals showing peer review
- [ ] Deployment records (who deployed what, when, from which environment)
- [ ] Change tickets with approvals and test results
- [ ] Separation of duties evidence: developers cannot merge their own PRs
- [ ] Production deployment approvals (separate from development team)

### Security Monitoring Evidence
- [ ] Vulnerability scan reports with dates (quarterly minimum)
- [ ] Penetration test report (annual)
- [ ] SIEM/log monitoring screenshots showing active alerting
- [ ] Alert investigation records
- [ ] Patch deployment records aligned to vulnerability reports

### Vendor Management Evidence
- [ ] Vendor inventory with tier classifications
- [ ] SOC 2 reports or security questionnaire responses from critical vendors
- [ ] Vendor contracts with security clauses
- [ ] Annual review documentation

### Incident Response Evidence
- [ ] Incident log (even if no major incidents — log minor events)
- [ ] Tabletop exercise record (scenario, attendees, findings, actions)
- [ ] IRP document with version history
- [ ] For any incidents during period: incident ticket, timeline, resolution, notifications

### Business Continuity / DR Evidence
- [ ] BCP/DRP document with RTO/RPO definitions
- [ ] DR test results (restore from backup, failover test)
- [ ] Backup job success logs
- [ ] Restoration test records (did the backup actually restore?)

---

## Common SOC 2 Gaps in SaaS/Cloud Environments

### No Formal Access Review Process (CC6.2, CC6.3)
**Gap:** User access is provisioned but never reviewed; departed employees may retain access.
**Fix:** Implement quarterly access reviews in Jira, Vanta, Drata, or a spreadsheet. Document who reviewed, when, what changes were made. Automate deprovisioning via HRIS-SSO integration.

### Developers Can Deploy to Production (CC8)
**Gap:** Engineers have direct production deployment access; no separation of duties.
**Fix:** Require pull request approval from a second engineer. Restrict production deployments to CI/CD pipeline with approvals. Even for small teams, document the control: "Engineer A writes code; Engineer B reviews and approves before merge; CI/CD deploys."

### No Documented Incident Response Testing (CC7.3–CC7.5)
**Gap:** IRP exists on paper but has never been tested.
**Fix:** Conduct a tabletop exercise (even 1 hour with 3 people). Document scenario, participants, walk-through, and action items. Auditors want evidence of testing, not just the plan.

### Monitoring Without Investigation Records (CC7.2)
**Gap:** SIEM generates alerts but no records of alert investigation.
**Fix:** Create a simple alert log: date, alert type, who investigated, finding, action taken. Even "investigated, false positive, no action required" counts.

### Vendor SOC Reports Not Collected (CC9.2)
**Gap:** Critical cloud providers (AWS, Stripe, Salesforce) not included in vendor management program.
**Fix:** Download SOC 2 reports for critical subservice organizations annually (most are available via their trust portals). Document where you reviewed them and what you found.

### Backup Restoration Not Tested (A1, if Availability in scope)
**Gap:** Backups run but restoration is never verified.
**Fix:** Perform a documented restoration test at least annually. Restore to a non-production environment and confirm data integrity. Record date, what was restored, results.

---

## Readiness Assessment Checklist

Before engaging a SOC 2 auditor, verify:

**Governance**
- [ ] Information Security Policy approved and distributed
- [ ] All minimum policies exist (12 policies above)
- [ ] Risk assessment completed in last 12 months
- [ ] Security awareness training completed by all personnel

**Access Controls**
- [ ] MFA enabled for all systems in scope
- [ ] Privileged access documented and reviewed
- [ ] Terminated employees removed from all systems (documented process)
- [ ] Access provisioning follows documented approval process

**Change Management**
- [ ] Code review/PR approval process enforced in version control
- [ ] CI/CD pipeline has approval gates before production
- [ ] Change log maintained for infrastructure changes

**Monitoring**
- [ ] Security alerts configured and investigated
- [ ] Vulnerability scans running and documented
- [ ] Log retention meets audit period (12 months)

**Availability (if in scope)**
- [ ] Backup policy defined and implemented
- [ ] Restoration test completed and documented
- [ ] DR/BCP plan tested in last 12 months

**Vendors**
- [ ] Critical vendor list maintained
- [ ] SOC 2 reports collected for critical SaaS/cloud vendors


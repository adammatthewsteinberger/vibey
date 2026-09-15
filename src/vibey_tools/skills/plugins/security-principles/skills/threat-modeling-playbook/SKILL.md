---
name: threat-modeling-playbook
description: Use when conducting threat modeling, creating STRIDE analysis, running threat assessment workshops, designing secure architectures, or identifying attack vectors. Use for any security design review, architecture threat analysis, or security risk assessment. Triggers on threat model, attack surface, STRIDE, PASTA, MITRE ATT&CK, attack tree, misuse story, trust boundary, data flow diagram, "what could go wrong" security questions, or security review of a new system or feature.
---

# Threat Modeling Playbook: From STRIDE to MITRE ATT&CK

## What threat modeling is and why it exists

Threat modeling transforms security from reactive to proactive by systematically identifying what can go wrong before it does. The goal: find design-level vulnerabilities that no amount of code review or penetration testing can fully compensate for, because they are baked into the architecture.

**The core question set** (Adam Shostack's four-question framework):
1. What are we building? (Understand the system)
2. What can go wrong? (Identify threats)
3. What are we going to do about it? (Identify mitigations)
4. Did we do a good enough job? (Validate completeness)

The major methodologies are complementary, not competing — each addresses a different dimension of threat analysis. Use them together.

## STRIDE: systematic threat enumeration

**STRIDE** was developed in 1999 by Loren Kohnfelder and Praerit Garg at Microsoft. It maps six threat categories to the security property each violates.

| Threat | Violated Property | Core Question |
|--------|------------------|---------------|
| **S**poofing | Authentication | Can someone pretend to be something they are not? |
| **T**ampering | Integrity | Can someone modify data or code without authorization? |
| **R**epudiation | Non-repudiation | Can someone deny performing an action they actually performed? |
| **I**nformation Disclosure | Confidentiality | Can someone access information they should not? |
| **D**enial of Service | Availability | Can someone prevent legitimate use of the system? |
| **E**levation of Privilege | Authorization | Can someone gain capabilities they should not have? |

### How to apply STRIDE

**Step 1: Draw a Data Flow Diagram (DFD)**

A DFD has four element types:
- **External entities** (rectangles): actors outside the system boundary — users, external services, third-party APIs
- **Processes** (circles/ovals): code that transforms data — services, functions, components
- **Data stores** (parallel lines): where data rests — databases, queues, caches, files
- **Data flows** (arrows): how data moves between elements — API calls, database queries, network packets

**Step 2: Draw trust boundaries**

Trust boundaries are where the level of trust changes. Mark them with a dashed line. Common trust boundaries:
- The network perimeter (inside vs. outside the VPN/firewall)
- Between user-controlled code and server-side code
- Between services with different permission levels
- Between admin and non-admin contexts
- Between public API and internal API

**Step 3: Apply STRIDE to each element**

Not all STRIDE categories apply to all elements:

| Element Type | Applicable STRIDE |
|-------------|-------------------|
| External entity | Spoofing, Repudiation |
| Process | All six |
| Data store | Tampering, Information Disclosure, Denial of Service |
| Data flow | Tampering, Information Disclosure, Denial of Service |

**Step 4: Risk-filter the threats**

Apply simple risk scoring: Likelihood (High/Medium/Low) × Impact (High/Medium/Low). Focus on High×High and High×Medium. This addresses STRIDE's main limitation — "threat explosion" — which generates enormous numbers of threats, many low-priority.

### STRIDE in practice: worked example

**System**: A payment service that accepts card data from a mobile app, validates it, and calls an external payment processor.

Data flows:
1. Mobile app → Payment API (HTTPS)
2. Payment API → Card Validator (internal gRPC)
3. Payment API → Payment Processor (external HTTPS)
4. Payment API → Audit Log (write-only database)

Trust boundaries: mobile app / internet / internal services / external processor

STRIDE analysis on "Mobile app → Payment API":
- **Spoofing**: Can a malicious app impersonate a legitimate one? → Mitigation: certificate pinning, app attestation
- **Tampering**: Can amounts or card data be modified in transit? → Already mitigated by HTTPS with certificate validation
- **Repudiation**: Can a fraudulent user deny making a payment request? → Mitigation: request signing with user credential, audit log write
- **Information Disclosure**: Can card data be exposed in transit? → Already mitigated by TLS; also consider: are we logging card numbers in error logs?
- **Denial of Service**: Can the API be flooded? → Mitigation: rate limiting per user, per IP, per device fingerprint
- **Elevation of Privilege**: Can a regular user trigger admin-only flows? → Mitigation: scope validation on every endpoint

## PASTA: risk-centric threat modeling

**PASTA** (Process for Attack Simulation and Threat Analysis) was developed in 2012 by Tony UcedaVélez. Seven stages organized as risk-centric and attacker-centric analysis. Carnegie Mellon SEI recommends PASTA as the basis for comprehensive threat modeling.

| Stage | Name | Key Activity |
|-------|------|-------------|
| 1 | Define Business Objectives | Identify the business impact of a breach: regulatory, reputational, financial |
| 2 | Define Technical Scope | Enumerate components, dependencies, data classification |
| 3 | Decompose Application | Create DFDs, identify trust boundaries, data flows |
| 4 | Threat Analysis | Enumerate threats using intelligence (CVEs, threat feeds, MITRE ATT&CK) |
| 5 | Vulnerability Analysis | Map threats to known weaknesses in the specific tech stack |
| 6 | Attack Modeling | Build attack trees; model attacker scenarios end-to-end |
| 7 | Risk/Impact Analysis | Connect technical threats to business impact; prioritize mitigations |

**PASTA's key advantage over STRIDE**: by starting with business objectives (Stage 1) and ending with risk analysis (Stage 7), PASTA connects technical threats to business impact. Stage 7 filters STRIDE's threat explosion through a risk and impact lens, producing a prioritized, business-justified mitigation backlog.

**PASTA's key advantage over pure STRIDE**: PASTA elevates threat modeling to a strategic organizational activity. It produces output that resonates with executives and boards — not just a list of technical vulnerabilities, but a prioritized risk register with business-impact framing.

**When to use PASTA**: new system architecture review, compliance audit preparation, board-level security reporting, any context requiring explicit business impact analysis.

## LINDDUN: privacy-specific threat modeling

**LINDDUN** was developed at KU Leuven in 2011. Focuses specifically on privacy threats — use when data privacy is a primary concern.

| Threat | Meaning |
|--------|---------|
| **L**inkability | Can an attacker link two or more items of data about the same person? |
| **I**dentifiability | Can an attacker identify an individual from the data? |
| **N**on-repudiation | Can users be held accountable for their actions? (Here a THREAT — users may want deniability) |
| **D**etectability | Can an attacker detect that a data item exists, even without its content? |
| **D**isclosure | Can an attacker access the content of data? |
| **U**nawareness | Are users unaware of how their data is being collected and used? |
| **N**oncompliance | Does the system violate data protection regulations or privacy policies? |

**Critical insight**: Non-repudiation is inverted from security to privacy. In security, proving who did what is a goal. In privacy, it can be a threat — users sometimes want deniability (think: political dissidents, abuse victims, medical patients). A system that creates undeniable records of sensitive behavior may violate privacy principles even if technically "secure."

**When to use LINDDUN**: GDPR compliance design, health data systems, messaging applications with privacy expectations, any system processing personal data at scale.

## Attack trees: modeling attacker goals

**Attack trees** were popularized by Bruce Schneier in his December 1999 *Dr. Dobb's Journal* article. Root node = attacker's goal. Children = ways to achieve the goal.

**Node types**:
- **OR nodes**: children are alternatives — any one can achieve the parent goal
- **AND nodes**: all children are required co-conditions — the attacker must accomplish all of them

**Attribute propagation**: assign values to leaf nodes (cost, likelihood, difficulty, legality) and compute the cheapest or most likely path to the root. This makes attack trees analytically powerful.

**Example attack tree**: "Gain admin access to payment database"

```
[ROOT - OR] Gain admin access to payment database
├── [OR] Compromise a DBA account
│   ├── Phish DBA (cost: $200, likelihood: medium)
│   ├── Brute-force SSH (cost: $50, likelihood: low - rate limited)
│   └── Exploit password reuse from data breach (cost: $10, likelihood: high)
├── [AND] Exploit SQL injection + Escalate privileges
│   ├── Find SQL injection vulnerability (requires: pen test time)
│   └── Use DB function for OS privilege escalation (requires: specific DB version)
└── [OR] Insider threat
    ├── Bribe current DBA
    └── Compromise former DBA credentials (not yet deprovisioned)
```

Attribute propagation reveals the cheapest path: exploit password reuse from a breach costs $10 and has high likelihood — almost certainly cheaper than all other paths. This drives mitigation priorities: mandatory MFA for DBAs, breach monitoring, deprovisioning processes.

Schneier envisions AI enabling continuous automated attack tree generation — a realistic near-term application for LLMs in security tooling.

## MITRE ATT&CK: intelligence-driven threat modeling

**MITRE ATT&CK** (Adversarial Tactics, Techniques, and Common Knowledge) was developed in 2013 and made public in 2015. A continuously updated knowledge base of real-world attack patterns observed against enterprise environments.

**Structure**:
- **Tactics** (14): the "why" — the attacker's objectives at each stage (Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command and Control, Exfiltration, Impact)
- **Techniques** (188+): the "how" — specific methods used to achieve each tactic
- **Sub-techniques** (379+): more specific implementations of techniques
- **Threat actors**: groups associated with specific technique combinations

**Example**: Tactic = Credential Access → Technique = OS Credential Dumping → Sub-technique = LSASS Memory (T1003.001) → used by APT28, Lazarus Group, others

**ATT&CK vs Lockheed Martin Kill Chain**: The Kill Chain (2011) has seven linear stages (Reconnaissance, Weaponization, Delivery, Exploitation, Installation, C2, Actions on Objectives) — useful for describing the attack lifecycle to non-technical leadership and for the insight that breaking any link disrupts the entire attack. But the Kill Chain is linear and perimeter-focused, poorly covering insider threats, cloud attacks, or post-exploitation lateral movement.

**Best practice**: use Kill Chain to identify the attack **stage**; use ATT&CK to identify specific **techniques** within that stage.

### Using ATT&CK for threat modeling

For each system component, ask: which ATT&CK techniques apply to this component's attack surface?

For a Kubernetes cluster, relevant techniques include:
- T1609 (Container Administration Command): exec into containers
- T1610 (Deploy Container): deploy malicious container as persistence
- T1613 (Container and Resource Discovery): enumerate pods, services
- T1552.007 (Container API credentials): steal service account tokens
- T1078.001 (Default Accounts): use default service accounts

Map each technique to relevant mitigations from ATT&CK's mitigation library, then to specific controls in your environment.

## Practical STRIDE in Agile sprints

For teams that need threat modeling at development velocity, not just at architecture-review time:

**Lightweight STRIDE per user story (5-10 minutes)**:

1. Draw the trust boundary around the story: what inputs come from outside this boundary?
2. Apply only relevant STRIDE categories (not all six every time):
   - User input involved? → Spoofing, Tampering, Elevation of Privilege
   - Sensitive data stored or transmitted? → Information Disclosure
   - External calls made? → Spoofing, Tampering
   - Resource-intensive operation? → Denial of Service
3. For each confirmed threat, create a **misuse story**: "As an attacker, I want to [threat] so that I can [impact]."
4. Add confirmed threats to the security backlog as acceptance criteria or separate security stories.

**Misuse story format**:
```
As a [type of attacker],
I want to [specific attack action],
So that I can [business impact].

Mitigation: [specific control to add/verify]
Acceptance Criteria: [how to verify the mitigation works]
```

Example misuse story:
```
As an unauthenticated external attacker,
I want to enumerate valid usernames by observing different response times for 
  existing vs non-existing accounts during login,
So that I can reduce the search space for a credential stuffing attack.

Mitigation: Constant-time comparison for all authentication responses regardless 
  of whether the username exists.
Acceptance Criteria: Response time variance between valid/invalid usernames 
  is < 5ms under load testing.
```

## Full threat model document structure

For architecture-level reviews (new systems, major changes, compliance requirements):

1. **Scope**: what is in scope, what is explicitly out of scope, which threat actors are in scope
2. **Architecture diagram**: components, data flows, external integrations, deployment topology
3. **Trust boundaries**: explicit enumeration with rationale for each boundary
4. **Asset inventory**: what data is stored/processed, classification, regulatory scope
5. **Threat enumeration**: STRIDE per element, organized by risk level
6. **Risk rating**: likelihood × impact for each threat (CVSS base score where applicable; EPSS for exploitation probability)
7. **Mitigations**: specific controls mapped to each threat
8. **Residual risk**: threats that cannot be fully mitigated, accepted risk documented with owner and review date
9. **Security backlog**: prioritized list of mitigations not yet implemented

## Risk rating: using CVSS and EPSS together

**CVSS** (Common Vulnerability Scoring System) measures severity 0.0-10.0. Limitations: base scores are often treated as final severity when temporal and environmental metrics are rarely applied; does not capture vulnerability chaining; measures severity, not risk.

**EPSS** (Exploit Prediction Scoring System): predicts exploitation probability within 30 days based on real-world exploit activity. Critical complement to CVSS.

**The key insight**: a CVSS 6.8 vulnerability with 94% EPSS probability may be more urgent than a CVSS 9.8 with 2% EPSS probability that has never been exploited in the wild.

**Combined formula for threat modeling**: Risk = CVSS severity × EPSS exploitation probability × Asset value × (1 - Control effectiveness)

## Common threat modeling mistakes

**Threat explosion without prioritization**: STRIDE generates many threats; without risk filtering, the output is an unusable list. Always apply likelihood × impact before presenting results.

**Forgetting the Return threat**: threat models often focus on external attacks and miss insider threats, supply chain threats, and operational failures.

**Static threat models**: threat models have a shelf life. Architectural changes, new integrations, and new threat intelligence all require revisits. Schedule quarterly reviews for production systems.

**Confusing assets with components**: the asset is the data, not the database. The database is the component that protects (or exposes) the asset. Threats are ultimately to assets, not to components.

**Skipping the Trust Boundary step**: trust boundaries are where most interesting threats live — they are the seams where different levels of trust meet. A DFD without explicit trust boundaries is a drawing, not a threat model.

**Not translating to business impact**: technical threat models that cannot be translated to business terms (revenue at risk, regulatory exposure, reputation damage) fail to drive organizational prioritization. PASTA Stage 7 solves this; even lightweight STRIDE should include a one-sentence business impact for each High-risk threat.

## Quick-reference: when to use which methodology

| Situation | Recommended approach |
|-----------|---------------------|
| New feature in a sprint, need fast analysis | Lightweight STRIDE per user story |
| New system architecture design | STRIDE + attack trees for high-risk components |
| Comprehensive architecture review for compliance | PASTA |
| System processes personal data (GDPR, HIPAA) | Add LINDDUN to STRIDE |
| Evaluating detection/monitoring coverage | MITRE ATT&CK mapping |
| Executive/board security briefing | PASTA Stage 7 output |
| Red team planning | Attack trees + MITRE ATT&CK |
| Post-incident review to update threat model | MITRE ATT&CK technique identification + threat model update |

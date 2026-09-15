---
name: ai-era-security
description: "Use when securing AI systems, LLM applications, agentic AI, or evaluating AI security frameworks. Triggers on OWASP LLM Top 10, OWASP Agentic Top 10, MITRE ATLAS, NIST AI RMF, EU AI Act, prompt injection, agentic security, MCP security, post-quantum cryptography, or any AI/ML security question. Also use for modern security framework updates: NIST CSF 2.0, CIS Controls v8.1, FIDO2/passkeys, CNAPP, or software supply chain security (SLSA/Sigstore/SBOM)."
---

# AI-Era Security: Principal Architect's Field Guide (June 2026)

## Quick-Reference Principle
Traditional security fundamentals are the bedrock. AI-era security is a genuine extension, not a rebrand. The data/instruction boundary collapse (prompt injection), autonomous action (agentic AI), and models as supply-chain artifacts all require layering new controls on top of — not instead of — the proven foundations.

Three clocks are running simultaneously:
1. **Post-quantum migration** — NIST finalized FIPS 203/204/205 in Aug 2024; "harvest-now-decrypt-later" makes key-agreement migration urgent today
2. **EU AI Act high-risk obligations** land Aug 2, 2026
3. **Agentic AI is already in your environment** — treat every agent as a non-human identity with least privilege and a human sponsor

---

## SECTION 1 — Modern Framework Updates (What Changed 2024–2025)

### NIST CSF 2.0 (Feb 26, 2024)
First major revision since 2014. Headline change: sixth core function **Govern (GV)** added to Identify, Protect, Detect, Respond, Recover.

- 6 functions / 22 categories / 106 subcategories
- Govern (GV) contains 31 of 106 subcategories (~29%) covering organizational context, risk strategy, roles, policy, oversight, supply-chain risk management
- **Doubled supply-chain subcategories (GV.SC) from 5 to 10** (10 of 106, ~9.4%)
- Scope expanded from critical infrastructure to all organizations
- CSF 2.0 is now the lingua franca mapping to ISO 27001, CIS Controls, and NIST 800-53

**Why it matters:** Governance and C-SCRM are now first-class board-level concerns, not IT concerns.

### CIS Controls v8.1 (June 25, 2024)
Iterative update aligning to NIST CSF 2.0.

- 18 Controls, 153 Safeguards, 3 Implementation Groups (IG1/IG2/IG3)
- New **Governance** security function added
- New **Documentation** asset class added
- Per the CIS Community Defense Model, full implementation defends against ~86% of MITRE ATT&CK (sub-)techniques
- Best starting point for operational hardening — more prescriptive than CSF

### ISO/IEC 27001:2022
Restructured Annex A into 4 themes (Organizational, People, Physical, Technological) and 93 controls total, with 11 new controls including:
- Threat intelligence
- Cloud security
- Data leakage prevention (DLP)
- Secure coding

Transition deadline: certifications against the 2013 version expired during the transition window ending in 2025.

### Modern IAM Gold Standards
- **Phishing-resistant MFA gold standard: FIDO2/WebAuthn and PKI (PIV/CAC).** CISA explicitly names these as gold standard; SMS, OTP, and push are phishable.
- **Prompt bombing appeared in 14% of incidents** per Verizon 2025 DBIR, and was the most common MFA-bypass technique, appearing in >20% of social-engineering breaches involving MFA bypass.
- **NIST SP 800-63-4 (finalized 2025)** makes phishing-resistant authentication mandatory at AAL3 (hardware-bound, non-exportable keys; syncable passkeys are NOT permitted at AAL3). The mechanism: **origin binding** — the authenticator cryptographically refuses to respond to a spoofed domain.
- **Passkeys:** device-bound for privileged/admin; synced for general workforce. Natively supported across Apple/Google/Microsoft.
- **Zero standing privileges** with just-in-time, time-boxed elevation (JIT PAM). Gold-standard vendor: CyberArk.

### CNAPP Consolidation
CNAPP (Cloud-Native Application Protection Platform) unifies CSPM + CWPP + CIEM + DSPM + KSPM + IaC scanning.

Market leaders:
- **Wiz** (agentless, Security Graph; acquired by Google for ~$32B, closed 2026)
- **Palo Alto Prisma/Cortex Cloud**
- **CrowdStrike Falcon Cloud Security**
- **Microsoft Defender for Cloud**
- **Orca Security**

DSPM (Data Security Posture Management) discovers/classifies sensitive data (PII/PHI/PCI), maps data flows and exposure paths, and ties data risk to identity and infrastructure context.

### Software Supply Chain Security
The mature, vendor-neutral stack:
- **SLSA** (Supply-chain Levels for Software Artifacts, v1.0) — build provenance; target SLSA Level 3+
- **Sigstore** (Cosign for signing, Fulcio for keyless OIDC-based certs, Rekor transparency log) — artifact signing
- **SBOMs** (SPDX/CycloneDX) — component inventory
- **in-toto/DSSE** — attestation envelopes

Scale of threat: **Sonatype discovered 454,648 new malicious open-source packages in 2025** (cumulative: 877,522+ since 2019). Threats evolved from "spam and stunts" into "sustained, industrialized campaigns."

**Critical rule: pin dependencies by commit SHA, not tag.**

Watershed events: GhostAction GitHub Actions compromise, Ultralytics PyPI compromise.

### Ransomware Resilience
**3-2-1-1-0 backup rule:** 3 copies, 2 media types, 1 offsite, 1 offline/immutable/air-gapped, 0 errors after verification.

---

## SECTION 2 — AI Threat Landscape

### Adversarial ML Taxonomy (NIST AI 100-2)
- **Evasion attacks** — craft inputs to fool a deployed model
- **Poisoning attacks** — corrupt training data or model weights
- **Model inversion** — reconstruct training data from model outputs
- **Model extraction** — replicate proprietary model functionality through queries
- **Membership inference** — determine whether specific data was in the training set

### Prompt Injection (OWASP LLM01 — #1 for second consecutive edition)
**Root cause: LLMs process instructions and data in the same channel with no separation.**

Two forms:
- **Direct prompt injection** — user manipulates the prompt (e.g., DAN-style jailbreaks, system prompt override)
- **Indirect/XPIA (Cross-Prompt Injection Attack)** — malicious instructions hidden in documents, web pages, emails, or tool outputs that the model ingests

XPIA is especially dangerous because it requires no user interaction — the model fetches and executes attacker-controlled content autonomously.

### Training-Data Poisoning (OWASP LLM04)
- **Backdoored "sleeper agent" models** — behave normally until triggered by a specific input
- **Poisoned LoRA adapters** — the "PoisonGPT" technique: inject false factual claims via fine-tuning
- Treat Hugging Face downloads as untrusted supply chain — scan for unsafe deserialization (pickle) and backdoors; prefer **safetensors**

### RAG Poisoning / False RAG Entry Injection
- Poison vector databases used for retrieval-augmented generation
- False RAG entry injection: inject adversarial content that gets retrieved as "authoritative" context
- Added to MITRE ATLAS in Spring 2025

### Agent Hijacking and Tool Misuse
See Section 4 (OWASP Agentic Top 10) and Section 5 (real-world incidents).

---

## SECTION 3 — AI Security Frameworks (2024–2026 Canon)

### NIST AI RMF 1.0 (NIST AI 100-1, Jan 2023)
The de facto US AI governance vocabulary. Four functions:
1. **Govern** — culture, policies, accountability
2. **Map** — categorize AI risks in context
3. **Measure** — assess and analyze risk
4. **Manage** — prioritize, respond, monitor

### NIST AI 600-1 (Generative AI Profile, July 26, 2024)
A cross-sectoral profile issued per Executive Order 14110. Defines **12 GAI risk categories** including:
- Confabulation/hallucination
- Dangerous/CBRN information
- Data privacy
- Harmful bias
- Intellectual property
- **Prompt injection and data poisoning (§2.9)** — explicitly named as information security risks
- **Supply-chain/value-chain integrity (§2.12)**

### MITRE ATLAS v5.1.0 (November 2025)
The adversarial AI ATT&CK analog.

Current scope:
- **16 tactics, 84 techniques, 56 sub-techniques, 32 mitigations, 42 case studies**
- Spring 2025: added GenAI techniques — RAG Poisoning, False RAG Entry Injection, LLM Prompt Crafting, AI Supply Chain Compromise
- October 2025: Zenity Labs collaboration added 14 agent-focused techniques

**Usage rule: OWASP for risk prioritization; ATLAS for technique mapping and red-teaming.**

### OWASP LLM Top 10 (2025 Edition)
Two new entries vs. 2023/24 (marked *new*):

| # | Risk |
|---|------|
| LLM01 | Prompt Injection |
| LLM02 | Sensitive Information Disclosure |
| LLM03 | Supply Chain |
| LLM04 | Data & Model Poisoning |
| LLM05 | Improper Output Handling |
| LLM06 | Excessive Agency |
| LLM07 | System Prompt Leakage *(new)* |
| LLM08 | Vector & Embedding Weaknesses *(new)* |
| LLM09 | Misinformation |
| LLM10 | Unbounded Consumption |

**Critical:** LLM07 means the system prompt is NOT a security control (see production security guidance below).

### OWASP Top 10 for Agentic Applications (December 2025)
See full Section 4 below.

### ISO/IEC 42001:2023
The world's first certifiable **AI Management System (AIMS)** standard. Plan-Do-Check-Act structure.

- 38 controls across 9 objectives
- Microsoft, Google Cloud (Vertex/Gemini), and others are now certified
- **This is the AI-governance analog of ISO 27001**
- Pair with ISO 27001 — they are complementary, not duplicative

### EU AI Act (Regulation 2024/1689)
Phased implementation timeline:
- **Aug 1, 2024** — entered into force
- **Feb 2, 2025** — prohibited practices + AI literacy requirements
- **Aug 2, 2025** — GPAI (General Purpose AI) obligations
- **Aug 2, 2026** — high-risk (Annex III) obligations and enforcement (plan for this date; a "Digital Omnibus" proposal may defer some, but assume original)

Fines: up to **€35M or 7% of global annual turnover**, whichever is higher.

**Action: classify all AI systems against Annex III before Aug 2, 2026. Any high-risk use case requires a full AI risk management system.**

---

## SECTION 4 — OWASP Agentic Top 10 (December 2025)

Released December 9, 2025. Developed with 100+ security researchers; review board includes NIST, Microsoft AI Red Team, AWS, Oracle.

| ID | Risk | Real-World Example |
|----|------|--------------------|
| ASI01 | Agent Goal Hijack | EchoLeak (CVE-2025-32711) |
| ASI02 | Tool Misuse | Amazon Q |
| ASI03 | Identity & Privilege Abuse | — |
| ASI04 | Agentic Supply Chain Vulnerabilities | GitHub MCP exploit |
| ASI05 | Unexpected Code Execution | AutoGPT RCE |
| ASI06 | Memory & Context Poisoning | Gemini memory attack |
| ASI07 | Insecure Inter-Agent Communication | — |
| ASI08 | Cascading Failures | — |
| ASI09 | Human-Agent Trust Exploitation | — |
| ASI10 | Rogue Agents | Replit meltdown |

### ASI01 — Agent Goal Hijack
The agentic analog of prompt injection. An attacker redirects an agent's objective at runtime. EchoLeak (CVE-2025-32711) is the canonical example: a crafted email caused M365 Copilot to exfiltrate data automatically, with no user interaction.

### ASI02 — Tool Misuse
An agent invokes tools beyond their intended scope. Amazon Q incident demonstrated an agent using cloud-management tools it shouldn't have accessed. Defense: strict tool allowlisting, not blocklisting.

### ASI03 — Identity and Privilege Abuse
Agents inheriting excessive permissions, or attackers impersonating agents. Treat every agent as a non-human identity; apply same rigor as human privileged accounts.

### ASI04 — Agentic Supply Chain Vulnerabilities
Compromised MCP servers, plugins, or orchestration frameworks introduce malicious behavior. The GitHub MCP exploit demonstrated supply-chain compromise in an agentic context.

### ASI05 — Unexpected Code Execution
Agents that can write and execute code are vulnerable to unintended RCE. AutoGPT RCE is the documented example. Defense: sandbox all code execution environments.

### ASI06 — Memory and Context Poisoning
Attacking an agent's persistent memory to alter future behavior. The Gemini memory attack demonstrated poisoning that persisted across sessions. Defense: validate/bound agent memory; treat stored memory as untrusted input.

### ASI07 — Insecure Inter-Agent Communication
In multi-agent architectures, messages between agents lack authentication or integrity protection. Currently, both A2A and MCP protocols lack enforced token expiration and central verification.

### ASI08 — Cascading Failures
One agent's failure or compromise propagates to dependent agents. In multi-agent pipelines, a blast radius can span the entire system. Defense: circuit breakers, timeouts, and independent failure domains.

### ASI09 — Human-Agent Trust Exploitation
Social-engineering tactics adapted for AI agents — manipulating users into trusting malicious agent outputs, or agents into trusting manipulated human instructions.

### ASI10 — Rogue Agents
Agents that deviate from their intended objectives, whether due to manipulation or emergent behavior. The Replit meltdown is the documented example of runaway agent behavior.

---

## SECTION 5 — Documented Real-World Agentic Incidents (2025–2026)

### EchoLeak (CVE-2025-32711, CVSS 9.3)
- **What:** First "zero-click" indirect prompt injection in Microsoft 365 Copilot enabling automatic data exfiltration via a single crafted email
- **Disclosed by:** Aim Labs to MSRC
- **Mechanism:** Malicious instructions in an email body caused Copilot to exfiltrate sensitive data to an attacker-controlled destination without any user action; Aim Labs termed it an "LLM Scope Violation"
- **Status:** Patched server-side; no confirmed in-the-wild exploitation
- **OWASP mapping:** ASI01 (Agent Goal Hijack), LLM01 (Prompt Injection)

### Morris II (March 2024)
- **What:** First self-replicating GenAI worm using an adversarial self-replicating prompt for zero-click propagation across email assistants
- **Researchers:** Cohen (Technion), Nassi (Cornell Tech), Bitton (Intuit)
- **Status:** Proof-of-concept; no in-the-wild exploitation confirmed
- **Significance:** Demonstrated autonomous AI-to-AI attack propagation without human interaction

### Agent Session Smuggling (October/November 2025)
- **What:** A malicious agent exploits a stateful Agent2Agent (A2A) session to inject covert instructions across turns
- **Disclosed by:** Palo Alto Networks Unit 42
- **Demonstrated:** Unauthorized stock trades proof-of-concept
- **Status:** Research PoC
- **OWASP mapping:** ASI07 (Insecure Inter-Agent Communication), ASI03 (Identity & Privilege Abuse)

### ServiceNow "BodySnatcher" (CVE-2025-12420, CVSS 9.3)
- **What:** Broken-auth flaw in ServiceNow Virtual Agent / Now Assist allowing an unauthenticated attacker to impersonate any user and drive privileged agentic workflows, bypassing MFA/SSO
- **Disclosed by:** Aaron Costello (AppOmni)
- **Status:** Patched; no confirmed exploitation
- **OWASP mapping:** ASI03 (Identity & Privilege Abuse), ASI09 (Human-Agent Trust Exploitation)

### MCP Ecosystem Vulnerabilities (2025)
- **CVE-2025-49596** — Anthropic MCP Inspector RCE, CVSS 9.4 (fixed in version 0.14.1)
- **Empirical study (2025):** 5.5% of 1,899 open-source MCP servers exhibited tool-poisoning vulnerabilities
- **Invariant Labs demo (April 2025):** WhatsApp MCP tool-poisoning data exfiltration
- **NSA MCP Security guidance** published May 2026 ("MCP: Security Design Considerations")
- **OWASP mapping:** ASI04 (Agentic Supply Chain), ASI02 (Tool Misuse)

---

## SECTION 6 — Controls for Agentic Systems

### Agent Identity and Authorization
**Microsoft Entra Agent ID** (GA April 2026) is the current gold standard for enterprise agent identity:
- Issues agent identities as credential-less service principals
- OAuth for authorization, OIDC for authentication
- Scoped short-lived tokens (no standing broad permissions)
- Required human "sponsor" for every agent
- Conditional Access policies apply to agents
- Soft-delete cascade cleanup prevents orphaned agents

**Important caveat:** There is no single ratified cross-vendor OAuth-for-agents standard as of mid-2026. OWASP is working on Agentic Identity / an Agentic Naming Service. Flag agent identity as an emerging, fragmented area.

### Inter-Agent Trust
- Require message signing between agents
- Enforce mutual authentication across agent boundaries
- Establish explicit trust boundaries — don't implicitly trust upstream agents
- Both A2A and MCP protocols currently **lack enforced token expiration and central verification** — compensating controls are required

### Tool-Use Security
- **Allowlist tools and egress domains** (not blocklist — assume hostile)
- Validate and sanitize all URLs and parameters before execution
- Require re-approval on tool definition changes — defend against "rug pulls" where tool behavior changes after initial approval
- Validate tool outputs before feeding back into the agent (XPIA defense)

### Guardrails Architecture
Layer all available guardrail types — no single guardrail is sufficient:
- **Azure AI Content Safety** — Prompt Shields for direct + indirect injection, Groundedness detection, protected-material detection
- **AWS Bedrock Guardrails** — content filters, denied topics, PII redaction
- **NVIDIA NeMo Guardrails** — programmable rails via Colang across input/dialog/retrieval/execution/output
- **Guardrails AI** — Python validator library for output validation

Layer cloud-native input filters + specialized output/hallucination checks + library-level controls, ideally enforced at a gateway, not in the model.

### System Prompt Security
**The system prompt is NOT a security control.** OWASP LLM07 (System Prompt Leakage) makes this explicit. Enforce all security constraints deterministically outside the model in code.

### CSA MAESTRO Threat Modeling Framework
MAESTRO (Multi-Agent Environment, Security, Threat, Risk, and Outcome) is a seven-layer agentic threat modeling framework developed by Ken Huang/CSA (February 2025). Used by OWASP's Multi-Agentic System Threat Modeling Guide. Use it for structured threat modeling of agentic architectures, layered with MITRE ATLAS technique mapping.

### Secure Orchestration Frameworks
LangChain, LlamaIndex, and AutoGen all require explicit hardening:
- Explicit permission scoping for each agent
- Sandboxing for all tool execution
- Output validation before downstream consumption
- Audit logging of all agent decisions and tool calls

---

## SECTION 7 — Post-Quantum Cryptography (PQC)

### Finalized NIST Standards (August 13, 2024)
- **FIPS 203 (ML-KEM)** — from CRYSTALS-Kyber; key encapsulation / key exchange
- **FIPS 204 (ML-DSA)** — from CRYSTALS-Dilithium; digital signatures
- **FIPS 205 (SLH-DSA)** — from SPHINCS+; stateless hash-based signatures
- **FN-DSA (FALCON)** — forthcoming (fourth standard)

### Why Key Exchange Migration Is Urgent NOW
"Harvest now, decrypt later" is an active threat: adversaries archive today's encrypted traffic to decrypt once they have a quantum computer. Any data with a >10-year confidentiality requirement is already at risk.

### Migration Priority
1. **Migrate key exchange first:** hybrid TLS 1.3 with **X25519MLKEM768**
2. **Defer signature migration** — lower urgency, larger performance/payload tradeoff

### Implementation State (mid-2026)
- **OpenSSL 3.5** (April 2025): full ML-KEM/ML-DSA/SLH-DSA support
- **OpenSSH 10+:** mlkem768x25519 is the default key exchange
- **52% of human-generated web traffic** was post-quantum encrypted by early December 2025 (Cloudflare Radar 2025 Year in Review) — nearly doubled from 29% at year-start
- **Apple iOS 26 / macOS Sequoia:** PQC enabled by default (September 2025)
- **US EO 14144** (January 2025): pushes federal PQC procurement
- Cloudflare targets full PQC by 2029; Azure and other cloud providers rolling out PQC across services

### Strategic Goal: Crypto-Agility
Inventory all cryptographic usage, abstract algorithms behind interfaces, and ensure you can swap algorithms without architectural changes. This is more valuable than any single algorithm choice.

---

## SECTION 8 — 10-Point Agentic Security Design Checklist

Apply this checklist to every agentic system before production deployment.

**1. Non-human identity with human sponsor**
Every agent has a registered identity (Entra Agent ID or equivalent), a named human sponsor who owns accountability, and scoped short-lived credentials — no standing broad permissions.

**2. Least privilege + complete mediation**
Validate every tool call against policy in a deterministic layer outside the LLM. Allowlist permitted tools and egress domains. Apply Saltzer & Schroeder's Complete Mediation principle: every access, every time.

**3. Treat prompt as hostile, output as untrusted**
Apply input filtering before the LLM and output validation after. Check groundedness. Never trust that the model will enforce security constraints itself.

**4. Blast-radius containment**
Sandbox all tool execution in isolated environments. Segment agent permissions so one compromised agent cannot pivot. Cap spend and request rate to defend against Denial of Wallet (LLM10: Unbounded Consumption).

**5. Human-in-the-loop for irreversible/high-stakes actions**
Define which actions require human confirmation before execution. Automate the reversible; gate the irreversible. This is the highest-leverage single control against runaway agent behavior (ASI10).

**6. XPIA defense across all data ingestion paths**
Treat every document, email, web page, database row, and tool output as potentially adversarial. Do not blindly pass retrieved content into the agent context as instructions. Validate, sanitize, and isolate untrusted external content from instructions.

**7. Memory protection**
Validate and bound agent memory at read and write. Protect against context poisoning (ASI06) — stored memory is an attack surface, not a trusted source. Treat retrieved memory as untrusted input requiring the same scrutiny as external data.

**8. Inter-agent authentication and trust boundaries**
Sign inter-agent messages. Enforce mutual authentication between agents. Define explicit trust boundaries. Use time-boxed tokens. Do not assume messages from other agents are trustworthy by virtue of origin.

**9. Audit logging and observability for all agent actions**
Log all prompts (or prompt hashes), tool calls, parameters, responses, and decisions. This is non-negotiable for incident response and for detecting drift or rogue behavior. LLM observability platforms (Langfuse, Helicone, etc.) or native platform logging.

**10. Regular threat modeling with MAESTRO and MITRE ATLAS**
Run a CSA MAESTRO layered analysis at design time. Map attacks to MITRE ATLAS techniques. Re-run threat models when agent capabilities, tools, or integrations change. Purple-team agentic scenarios.

---

## Threat-Modeling Reference: STRIDE Applied to AI/Agents

| STRIDE | AI/Agentic Mapping |
|--------|-------------------|
| **S**poofing | Agent impersonation, identity abuse (ASI03) |
| **T**ampering | Prompt/RAG/memory poisoning (LLM04, ASI06), tool definition rug-pulls (ASI04) |
| **R**epudiation | Missing audit logs for agent actions and tool calls |
| **I**nformation disclosure | Sensitive info leakage (LLM02), system-prompt leakage (LLM07), data exfiltration via XPIA |
| **D**enial of service | Unbounded consumption / Denial of Wallet (LLM10), cascading failures (ASI08) |
| **E**levation of privilege | Excessive agency (LLM06), tool misuse (ASI02), privilege abuse (ASI03) |

Augment STRIDE with MITRE ATLAS technique mapping and CSA MAESTRO layered analysis for comprehensive agentic threat models.

---

## RAG Security Pattern

1. Validate and provenance-tag all ingested content before indexing
2. Isolate untrusted external content from system instructions
3. Access-control the vector store per tenant — multi-tenant RAG is a common data leakage path
4. Check output groundedness — detect when the model departs from retrieved context
5. Treat all retrieved content as untrusted data, not trusted instructions
6. Monitor for false RAG entry injection (MITRE ATLAS Spring 2025)

---

## EU AI Act Compliance Checklist

- **Classify all AI systems against Annex III** (high-risk categories including biometric ID, critical infrastructure, employment, education, law enforcement, migration, justice)
- **Any high-risk classification** triggers: risk management system, data governance, technical documentation, transparency to users, human oversight, accuracy/robustness/cybersecurity requirements
- **GPAI providers** (general-purpose AI): must maintain technical documentation, provide usage policies, comply with copyright law; systemic-risk GPAI adds adversarial testing and incident reporting
- **Target date: Aug 2, 2026** (plan for original timeline regardless of Digital Omnibus)
- **ISO/IEC 42001** certification significantly accelerates high-risk compliance

---

## Key Caveats

- EchoLeak, BodySnatcher, Morris II, and Agent Session Smuggling were disclosed vulnerabilities or researcher PoCs — not confirmed in-the-wild exploitation at time of disclosure
- No single ratified cross-vendor "OAuth-for-agents" standard exists as of mid-2026; agent identity remains fragmented
- The EU AI Act "Digital Omnibus" proposal may defer some high-risk timelines, but plan for Aug 2, 2026
- OWASP labels the Agentic list the "2026" edition though it released December 2025 — same document
- MCP ecosystem vulnerabilities and mitigations are evolving rapidly; re-check current NSA/NIST guidance at implementation time
- Confidential GPU availability (Azure NCC H100 v5) is region- and SKU-limited — verify current availability before architecting
- Vendor self-reported metrics (false-positive reductions, analyst-hours saved) should be validated against independent evaluations (MITRE Engenuity ATT&CK, AV-Comparatives)

---
name: requirements-gathering
description: "Comprehensive requirements engineering reference covering elicitation techniques (structured interviews, Event Storming, Example Mapping, Story Mapping, JTBD), stakeholder analysis, domain modeling, prioritization frameworks (MoSCoW, RICE, WSJF, Kano), NFR specification with Planguage, AI-assisted RE, EU AI Act obligations, and documentation standards (SRS, BDD/Gherkin, VOLERE). Use when helping with requirements gathering, user story writing, stakeholder workshops, acceptance criteria, backlog refinement, or any requirements analysis task."
---

# Requirements Engineering Reference Guide

## Core Framework

### Standards and Governing Bodies
- **ISO/IEC/IEEE 29148:2018** — governing standard; defines RE as "an interdisciplinary function that mediates between the domains of the acquirer and supplier or developer to establish and maintain the requirements to be met by the system, software or service." Three processes: Business/Mission Analysis; Stakeholder Needs & Requirements Definition; System/Software Requirements Definition.
- **Functional requirement syntax** (29148): `[Condition][Subject][Action][Object][Constraint of action]` — e.g., "Upon receiving signal x, the system shall set the 'signal x received' bit within 2 seconds."
- **Quality characteristics of a good requirement**: necessary, unambiguous, complete, singular, feasible, verifiable, traceable.
- **IREB CPRE v3.0** — four core activities: elicit, document, validate/negotiate, manage. Key principles: **Value Orientation** (requirements are a means to deliver value, not an end) and **Shared Understanding**.
- **BABOK v3** — requirements hierarchy: **business requirements → stakeholder requirements → solution requirements (functional + non-functional) → transition requirements**.

### Role Distinctions
- **Product management**: owns the "why/what-to-bet-on" and outcomes.
- **Business analysis**: owns the "what/translate-need-to-spec," especially in enterprise IT.
- **Requirements engineering**: owns rigor, modeling, traceability, and verification in systems/regulated domains.
- Roles overlap heavily; which title "owns" requirements depends on org structure.

### Key Conceptual Distinctions
- **Stated vs. real vs. latent requirements**: customers articulate stated requirements (often pre-baked solutions); analysts must translate to real needs and probe for latent needs.
- **Verification vs. validation**: verification = "are we building it right?" (meets spec); validation = "are we building the right thing?" (meets real need).
- **Requirements vs. constraints vs. assumptions vs. dependencies**: keep these distinct — each drives different execution.
- **The requirements paradox**: customers often can't say what they want until they see what they don't want — the empirical basis for prototyping and example-driven elicitation.

---

## Right-Sizing the Method

| Context | Approach |
|---|---|
| Bug fix | Expected-vs-actual + repro steps + impact/severity + regression criteria. No workshop. |
| Small feature | One Example Mapping / Three Amigos session (~25 min) → story + rules + examples + questions. Spike if red cards dominate. |
| Medium feature/epic | Story map slice + journey map + explicit NFRs (Planguage) + thin-slice first release. |
| Greenfield/enterprise | Stakeholder onion + power/interest map → vision/impact-mapping workshop → Big-Picture Event Storming → story map → dedicated NFR/quality-attribute-scenario workshops → traceability spine. |

---

## Stakeholder Analysis

### Mapping Techniques
- **Onion model**: concentric rings from system outward — operators/users → containing business → wider environment.
- **Power/interest grid (Mendelow)**: manage closely / keep satisfied / keep informed / monitor.
- Distinguish authority: who **decides**, who **informs**, who **ratifies**.

### Chronic Failure Modes
- **Forgotten stakeholders**: compliance, legal, security, operations, support, training, downstream data consumers, and negative stakeholders (whose opposition must be actively managed).
- **The HiPPO problem**: Highest-Paid Person's Opinion overriding evidence — mitigated by continuous evidence and "compare-and-contrast" framing.
- **The real-user problem**: getting past proxies (sponsors, SMEs, CSMs) to actual users — a documented top driver of project failure.

---

## Elicitation Techniques

### Structured Interviews — The Evidence-Backed Winner
Davis et al. (IEEE RE 2006) systematic review concluded: "(1) Interviews, preferentially structured, appear to be one of the most effective elicitation techniques; (2) Many techniques often cited in the literature, like card sorting, ranking or thinking aloud, tend to be less effective than interviews; (3) Analyst experience does not appear to be a relevant factor."

**Practitioner toolkit:**
- Structured / semi-structured / unstructured formats.
- Open vs. closed and **context-free questions** (Gause & Weinberg).
- **5 Whys / laddering**: drive from surface feature-request to root need.
- Active listening: paraphrase, summarize, strategic silence.
- **Anti-patterns**: the agreeable stakeholder, the solution-provider, the "I want everything" stakeholder, the silent expert.
- Novices fail through *interview design and conduct mistakes*, not lack of domain knowledge — invest in interview craft, not seniority.

### Workshops and Group Techniques
- JAD-style requirements workshops; neutral facilitator, parking lot, ground rules, managing dominant voices.
- Convergence techniques: affinity mapping, dot voting, nominal group, fist-to-five, Roman voting.
- **Pre-mortems** (Gary Klein): imagine the project has already failed — surfaces hidden requirements and risks.

### Event Storming (Alberto Brandolini, 2013)
The dominant collaborative domain-modeling technique. Orange sticky notes = **domain events** (past-tense, business-relevant) placed on a timeline.

**Three formats:**
1. **Big Picture**: ~25–30 people; explore an entire business line; deliberately informal, no strict notation.
2. **Process Modeling**: grammar — read model → command on a system → event → policy ("whenever X we do Y").
3. **Software Design**: adds aggregates, bounded contexts for 1:1 mapping to code.

**Key insight**: "It's developer's (mis)understanding, not expert knowledge, that gets released into production." The magic happens when participants sort events chronologically, forcing discovery of disagreement and gaps. Getting **bounded-context boundaries** right is "the single design decision with the most significant impact over the entire life of a software project."

### Example Mapping (Matt Wynne, Cucumber)
BDD-prerequisite workshop for nailing acceptance criteria. Ideally a **Three Amigos** session (PO/BA + dev + tester). Target: ~25 minutes per story.

| Card Color | Meaning |
|---|---|
| Yellow | Story |
| Blue | Rule (acceptance criterion) |
| Green | Example illustrating one rule (Given/When/Then-ish) |
| Red | Question (unanswerable now) |

**Signals**: table full of red cards = too much uncertainty; many blue cards = story is too big. Do NOT write full Gherkin during the session — identify examples and surface rules, not formalize them.

### Story Mapping (Jeff Patton, 2014)
Two-dimensional backlog: **backbone** (high-level user activities in narrative order) + **user tasks/stories stacked vertically** beneath in priority order. Horizontal slices = releases; topmost slice = **walking skeleton** (Cockburn) — the thinnest end-to-end version.

**Workshop arc (~4 hrs)**: frame outcome → silent-write activities → place backbone → decompose tasks → stack stories essential-to-nice-to-have → slice walking skeleton → slice subsequent releases. Cures the "flat backlog" problem.

### Impact Mapping (Gojko Adzic, 2012)
Mind-map structure: **Why (Goal) → Who (Actors) → How (Impacts/behavior changes) → What (Deliverables)**. Prevents "feature factories" by forcing every deliverable to trace to a measurable goal via a behavioral impact on an actor. Common pitfall: going into deliverable detail before nailing actors and impacts.

### Contextual Inquiry (Beyer & Holtzblatt, early 1990s)
Built on the **master-apprentice model**: researcher is the apprentice, user is the master, conducted in the user's real work context.

**Four principles**: Context, Partnership, Interpretation, Focus. Reveals *tacit* knowledge and workarounds users can't articulate in a conference room. Run an **interpretation session within 24 hours**; build an affinity diagram.

Premier approach for the **tacit-knowledge problem**. Related: shadowing, think-aloud protocol, apprenticing, diary studies, artifact analysis.

### Prototyping and Visualization
Fidelity spectrum: paper/low-fi → wireframe (Balsamiq) → interactive (Figma — de-facto modern source of truth for UI requirements; Axure, InVision, Marvel).

**Wizard-of-Oz** prototyping (human behind the curtain) is invaluable for AI/complex features. The "I know it when I see it" concretization effect makes prototyping the practitioner favorite for surfacing unstated assumptions — even though the Davis review didn't credit it for raw information yield under controlled conditions.

### User Stories vs. Job Stories
**User story**: "As a [role], I want [goal], so that [benefit]" — tested against **INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable).

**Job story** (originated at Intercom, named by Alan Klement): "When [situation], I want to [motivation], so I can [expected outcome]." Replaces persona with situation; reduces tendency to smuggle in a prescribed solution and to drop the "so that." Intercom's rationale: motivations are far more similar across demographics than personas imply.

**Acceptance criteria**: Given/When/Then (Gherkin) or bulleted positive/negative cases.

**Splitting patterns**: by workflow step, data variation, role, happy/unhappy path, interface variation, business rule.

### JTBD Switch Interview (Bob Moesta and Chris Spiek)
Forensically reconstructs a recent real purchase backward through markers: **First Thought → Passive Looking → Event 1 (trigger) → Active Looking → Event 2 (final trigger) → Decision/Purchase → Consumption**.

**Four Forces of Progress** (built on Lewin's force-field theory):
- **Push of the situation**: friction/frustration that makes someone start looking.
- **Pull of the new solution**: the better life the customer pictures.
- **Anxiety of the new solution**: fear of the unknown — the most underestimated force.
- **Habit of the present**: comfortable inertia of what people already know and do.

Push + Pull > Anxiety + Habit → the switch happens.

Moesta's claim: ~10 strategically chosen recent buyers reveal 3–5 buying patterns covering most of a market ("We'll do ten interviews, but it's like having a thousand surveys").

---

## Domain Modeling

### Process and Data
- **BPMN 2.0**: events, activities, gateways, lanes, pools; value stream mapping; swimlanes; AS-IS → TO-BE modeling.
- Decision tables/trees for complex rules; state machines for entity lifecycles.
- **Data**: ERDs, DFDs, conceptual class models, data dictionary, logical vs. physical data models.

### Domain-Driven Design (Strategic)
- **Bounded contexts, context maps, ubiquitous language** — requirements-shaping tools.
- Context-mapping patterns (shared kernel, customer-supplier, conformist, anticorruption layer) define integration requirements.
- Ubiquitous language prevents misunderstanding that "gets released into production."

---

## Prioritization Frameworks

| Framework | Best Used For |
|---|---|
| **MoSCoW** (Must/Should/Could/Won't) | Only meaningful against a fixed timebox; shortlisting |
| **Kano** (basic/performance/delighter) | Classifying features by customer satisfaction type |
| **RICE** (Reach × Impact × Confidence ÷ Effort) | Best with analytics, ~20–100 items; Intercom origin |
| **WSJF** (Cost of Delay ÷ job size) | SAFe/Reinertsen; large multi-team orgs |
| **ICE** | Quick scoring without analytics |
| **Buy-a-Feature** | Customer-involved prioritization |

**2026 consensus**: mature teams combine frameworks (e.g., MoSCoW to shortlist → RICE to rank; Kano to classify → RICE within type). Pre-filter >100-item backlogs with MoSCoW before scoring.

---

## NFR Specification

### Quality Attribute Taxonomy
Performance, scalability, availability, reliability, security, maintainability, usability/accessibility, testability, observability, deployability, portability.

### Planguage (Tom Gilb) — Gold Standard for Testable NFRs
Keywords:
- **Scale**: unit of measure
- **Meter**: how to measure
- **Past**: benchmark value
- **Goal/Must**: target/constraint levels
- **Wish**: aspirational level
- **Fit Criterion**: numeric pass/fail condition

**Key lesson**: practitioners struggle to define scales of measure and practical meters; unrealistic quantification can cause delay. Quantify against real business need.

### Key NFR Benchmarks
- Availability SLAs: 99.9% ≈ 8.76 hrs/yr downtime; 99.99% ≈ 52.6 min/yr.
- Specify with RTO/RPO for availability/reliability.
- Security: authN/authZ, data classification, encryption at rest/in transit, audit logging, compliance frameworks (SOC2/PCI-DSS/HIPAA/GDPR).
- Usability/accessibility: **WCAG 2.1 AA** is the baseline.
- Ban adjective-requirements: "fast" and "user-friendly" are not requirements.

### Quality-Attribute Scenarios (Bass/Clements/Kazman)
For architecture-impactful requirements: **source–stimulus–environment–artifact–response–response measure**.

---

## Validation and Analysis

- **Conflict detection/resolution**, completeness analysis (every success/failure path covered?), dependency ordering.
- **CRUD matrix** as a completeness check.
- **Reviews**: walkthrough vs. **Fagan inspection** for high-risk specs.
- **Prototyping-as-validation**: "here's what I understood — is this right?"
- **ATDD / Specification by Example** (executable specifications as living validation).
- **Formal methods** (Z, Alloy) for safety-critical domains.

---

## Documentation Standards

### Right-Size by Context
| Scale | Format |
|---|---|
| Lightweight | Stories + acceptance criteria in Jira/Linear — "enough to have the conversation" |
| Medium | Structured stories + explicit NFRs + journey maps + wireframes + data dictionary |
| Heavyweight | SRS/BRD/FSD/SyRS — for contract/regulated work |

### Key Templates
- **VOLERE shell**: comprehensive, fit-criterion-driven; mandates a Fit Criterion per requirement.
- **IEEE 830 SRS structure**: classic functional/NFR specification.
- **arc42**: architecture-oriented.
- **Gherkin feature files** as living documentation.
- **PRDs** in Confluence/Notion.

Avoid over-specification in fast-changing domains — favor **living documentation** over frozen PDFs.

### Traceability
- **Forward**: requirements → design → code → tests.
- **Backward**: tests → code → design → requirements.
- **Bidirectional RTM**: mandatory in regulated domains for impact analysis and coverage.
- **Agile lightweight**: link stories → epics → themes → outcomes (Jira/Azure DevOps hierarchy).
- **Heavyweight tools**: Jama Connect, IBM DOORS/DOORS Next, Siemens Polarion, Codebeamer, Helix RM.

---

## Special Contexts

### Bug Fixes
"Fix the bug" is not a requirement. Minimum artifact: steps to reproduce + expected vs. actual behavior + impact/severity + environment. Add regression requirements. Use 5 Whys/Ishikawa for root cause.

### Legacy Modernization
The existing system *is* the requirements baseline — use characterization testing (Feathers), Strangler Fig sequencing. Most-forgotten area: **data migration requirements**. Treat entrenched user mental models and undocumented workarounds as requirements.

### Regulated/Safety-Critical
- **DO-178C** (avionics): high-level → low-level requirements with bidirectional traceability.
- **IEC 62304** (medical device software safety classes).
- **ISO 26262** (automotive ASIL): safety goals → functional safety requirements → technical safety requirements.
- FMEA and hazard analysis feed requirements; configuration management governs change.

### AI/ML-Specific Requirements
Specify: accuracy/precision/recall/confidence thresholds, bias/fairness constraints, training-data and data-quality requirements, explainability, model-drift monitoring, retraining triggers, fallback behavior, and **human-oversight requirements**.

**EU AI Act (Regulation (EU) 2024/1689)**:
- In force Aug 1, 2024.
- Article 14(1): high-risk AI systems must be designed so "natural persons" can effectively oversee them and remain aware of automation bias.
- Annex III biometric-identification systems require verification by at least two competent persons.
- Articles 8–15: risk management, data governance, technical documentation, transparency, accuracy/robustness/cybersecurity, and logging (≥6 months).
- **Timeline**: Article 50 transparency and GPAI rules apply from Aug 2, 2026; stand-alone high-risk (Annex III) obligations extended to Dec 2, 2027 per May 2026 "AI Act Omnibus" — verify final adopted text before compliance planning.

---

## Continuous Discovery (Teresa Torres)

Shift from episodic to weekly customer touchpoints by a **product trio** (PM + designer + engineer).

**Opportunity Solution Tree**: Outcome (root) → Opportunities (customer needs/pains) → Solutions → Assumption Tests/Experiments.

**Key practices**:
- Generate *multiple* solutions per opportunity (avoid confirmation bias).
- Break ideas into **assumptions** and test the riskiest first.
- **Dual-track agile**: runs discovery alongside delivery.
- 2026 AI guidance: use AI for synthesis drafts and prototyping the *one element that tests your riskiest assumption*, but keep humans in the loop — AI summaries miss important nuance.

---

## AI-Assisted Requirements Engineering (2024–2026)

### What AI Helps With
- Generating user stories/PBIs from meeting notes and business descriptions.
- Drafting SRS text (~60–70% reduction in drafting time vs. entry-level engineers per IEEE RE 2024 study).
- Ambiguity/inconsistency/incompleteness detection (20.2% average improvement in classifying ambiguous requirements with 10-shot prompting per ICSME 2025 Alstom study).
- NFR generation aligned to ISO/IEC 25010.
- Interview transcription and synthesis.
- Auto-generated BDD acceptance criteria.

### What AI Cannot Replace
- Tacit-knowledge elicitation and live interview probing.
- Material nuance in stakeholder conversations.

### Risks
- Hallucinated requirements.
- Bias propagation.
- Loss of tacit knowledge.
- Over-reliance.

**Rule**: human-in-the-loop is mandatory for all AI-assisted RE work.

---

## Tooling Ecosystem (2026)

### Software/Product Teams
- **Jira**: dominant; stories/epics/custom hierarchies + code/CI integration.
- **Azure DevOps Boards**: strong for Microsoft shops.
- **Linear**: fast, engineering-focused, gaining on Jira.
- **Productboard / Aha!**: product management + roadmapping + customer feedback.
- **Confluence/Notion**: PRDs.
- **Figma/FigJam**: UI requirements + whiteboarding.
- **Miro/MURAL**: Event Storming, story/journey mapping.

### Regulated/Enterprise
- **Jama Connect**: strong traceability/collaboration, FDA/FAA-friendly, SOC2 Type 2, validated by TÜV SÜD. Scores above Polarion on core requirements/traceability per SoftwareReviews 2025.
- **IBM DOORS/DOORS Next**: long-established, defense/aerospace standard.
- **Siemens Polarion**: integrated requirements+change+test, automotive/electronics.
- **Codebeamer**: full ALM, medical/automotive.
- **Helix RM, Visure, reqSuite rm**: additional regulated-domain options.

---

## Key Evidence and Caveats

- **The "100x cost of late defects" curve has no traceable primary dataset** — Hillel Wayne traced it to a 1981 IBM internal training note. Use the direction (early fixes are cheaper) as a heuristic, not the multiplier as a fact.
- **Requirements/stakeholder problems are consistently the top correlated cause of project failure** — Standish CHAOS 1994 and 2014 both identify incomplete requirements and lack of user involvement as leading factors. Standish methodology is contested, but the relative finding is robust.
- **Davis review primacy of interviews** comes from controlled studies and may not fully capture prototyping's real-world value in surfacing latent requirements — hold both truths.
- **AI-in-RE figures are early and setting-specific** — the ~60–70% drafting reduction and 20.2% ambiguity improvement come from specific studies; generalization is unproven.
- **EU AI Act details remain in motion** — verify current adopted text before compliance planning.

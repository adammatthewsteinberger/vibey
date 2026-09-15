---
name: ai-security-practices
description: "AI security and cybersecurity best practices for software development (Python and TypeScript/Next.js) covering prompt injection defense, OWASP LLM Top 10 2025, agentic AI risks (OWASP ASI Top 10), MCP security, RAG attack vectors, output sanitization, guardrail architectures (NeMo Guardrails, LLM Guard), secrets management for AI APIs, Denial of Wallet prevention, supply-chain security (SLSA/Sigstore/SBOMs), critical Next.js/React CVEs, and NIST AI RMF. Use when advising on securing AI systems, LLM applications, agent architectures, or web application security in Python/TypeScript stacks."
---

# AI Security Practices: 2025–2026 Reference for Python & TypeScript/Next.js

## The Three Core Truths

1. **Treat the LLM as an untrusted, internet-connected user.** Defense-in-depth (input validation + output sanitization at every boundary, least-privilege tool access, human-in-the-loop for high-impact actions) is the only viable posture, because prompt injection cannot be fully patched away.
2. **The biggest 2025–2026 attack-surface shifts are agentic AI and the framework deserialization layer.** The Next.js/React Server Components RCE (CVE-2025-55182 / CVE-2025-66478, CVSS 10.0, actively exploited within days) and the middleware auth-bypass (CVE-2025-29927, CVSS 9.1) show that "secure-by-default" frameworks still require continuous patching.
3. **AI-generated code is shipping security debt at scale.** Veracode (July 2025): 45% of AI-generated code samples failed security tests; XSS failing 86%, log injection 88%. Apiiro: 10,000+ new security findings/month (10× spike), privilege-escalation paths up 322%. GitGuardian: AI-assisted commits leak secrets at 3.2% vs 1.5% baseline.

---

## OWASP LLM Top 10 (2025 Edition)

| Rank | Risk | Key Point |
|---|---|---|
| LLM01 | **Prompt Injection** | #1 for second consecutive edition; both direct and indirect; cannot be fully patched at input layer |
| LLM02 | Sensitive Information Disclosure | — |
| LLM03 | Supply Chain (model provenance) | Pickle-based RCE, malicious weights, poisoned training data |
| LLM04 | Data and Model Poisoning | — |
| LLM05 | **Improper Output Handling** | Treating model output as trusted → XSS, SQLi, SSRF, RCE |
| LLM06 | **Excessive Agency** | Over-permissioned tools, agentic misuse |
| LLM07 | System Prompt Leakage | — |
| LLM08 | **Vector and Embedding Weaknesses** | RAG security — new in 2025 edition |
| LLM09 | Misinformation (renamed Overreliance) | — |
| LLM10 | **Unbounded Consumption** | "Denial of Wallet" — new in 2025 edition |

---

## Prompt Injection (LLM01:2025) — The Unfixable Risk

### Why It Cannot Be Patched Away
LLMs process instructions and data in the same channel without clear separation. No input filter is fully reliable — adaptive attacks evade classifiers.

### Direct vs Indirect Injection
- **Direct:** "ignore previous instructions"
- **Indirect (harder):** malicious instructions embedded in a webpage, RAG document, email, or tool result the model later reads — NOT caught by input-only classifiers
- **Multimodal:** instructions hidden in images

### Defensible Architectural Patterns (More Robust Than Detection)
1. **Action-selector:** constrain the set of actions an LLM can take
2. **Plan-then-execute:** LLM produces a plan; deterministic code validates and executes it
3. **Dual-LLM** (Simon Willison): one privileged LLM for user instructions, one quarantined for external content
4. **CaMeL** (Google DeepMind, March 2025): privileged planner + quarantined LLM executor with enforced information-flow controls
5. **IsolateGPT** (NDSS 2025): sandboxed execution of external content

### Detection Tooling (Treat as One Layer, Not the Solution)
- **Meta Prompt-Guard / Llama Guard 3** (open-weight, 8B): outperforms GPT-4 on injection detection with ~1/3 the false-positive rate
- **NVIDIA NeMo** jailbreak heuristics
- **LLM Guard** (Protect AI): input scanners
- **DataSentinel**, **PIShield**

### Implementation
- **Python:** run Llama Guard via vLLM or LLM Guard input scanners before the model call; enforce a Pydantic output schema after
- **TypeScript:** validate model output with **Zod** before it touches SQL/HTML/shell; never pass raw LLM text to `dangerouslySetInnerHTML`

---

## Output Sanitization (LLM05:2025 Improper Output Handling)

**Threat:** treating model output as trusted → XSS, SQLi, SSRF, or RCE when output flows into downstream interpreters.

**Pattern:** validate/encode output by context:
- Schema validation: Pydantic (Python) / Zod (TypeScript)
- Context-aware output encoding
- Parameterized queries (never string-concatenate LLM output into SQL)
- PII redaction: Presidio-based (built into NeMo Guardrails and Guardrails AI Hub)

---

## Guardrail Architectures

### Layer Model
```
input rail (jailbreak/PII) 
  → retrieval rail (RAG chunks) 
  → execution rail (tool-call gating) 
  → output rail (moderation/PII/format)
```
No single framework covers all ten OWASP items — layer them.

### NVIDIA NeMo Guardrails
- Open-source, Apache 2.0; v0.17.0 (Oct 2025); **NVIDIA labels it beta / "additional hardening required for production"**
- Five rail types: input, dialog, retrieval, execution, output
- Uses the Colang DSL; uniquely models multi-turn dialog
- Integrates: Llama Guard, Presidio PII detection, NemoGuard-8b content-safety/topic-control NIMs
- Supports streaming output checks
- Integrates with LangChain/LangGraph

### Other Options
| Tool | Model | Best For |
|---|---|---|
| **Guardrails AI** | RAIL spec + validator Hub, `num_reasks` for auto re-prompting | Python-centric apps |
| **LLM Guard** (Protect AI) | Input + output scanners | Composable pipeline |
| **Lakera Guard** | Managed API | Minimal integration effort |
| **Azure AI Content Safety** | Managed Azure | Azure-native teams |
| **AWS Bedrock Guardrails** | Managed AWS | AWS-native teams |

### Red-Teaming Tools
Garak, PyRIT, Promptfoo, DeepTeam

---

## RAG Security (LLM08:2025)

### Attack Vectors
- **PoisonedRAG** (USENIX Security 2025): 5 malicious documents → 90%+ attack success rate on databases with millions of entries (97% on NQ, 99% on HotpotQA, 91% on MS-MARCO in black-box settings)
- **Embedding-inversion attacks:** recover 50–70% of source text from stolen vectors (ALGEN 2025: ~1,000 samples, transfers across black-box encoders)
- **Cross-tenant leakage** through shared vector stores
- **Hidden-text injection:** white-on-white resume text ingested as legitimate content

### Defense-in-Depth Across Ingest / Retrieve / Generate
**Ingest:**
- Validate and authenticate all document sources
- Strip hidden/zero-width text and ignore formatting on ingestion
- Detect and reject suspicious instruction patterns in documents

**Store:**
- Per-tenant physical isolation or DB-layer namespace filtering (not app-layer)
- Treat the vector DB as a sensitive data store: encrypt, access-control
- Embedding anomaly detection

**Retrieve/Generate:**
- Retrieval rails
- Per OWASP/Snyk LLM Security Verification Standard (Aug 2025): full verification checklist

---

## Agentic AI Security (LLM06:2025 + OWASP ASI Top 10)

### Threat Classes
- Tool misuse, identity/privilege abuse, rogue agents
- Unexpected code execution (ASI05)
- Memory poisoning, resource overload, cascading hallucination
- Real CVEs: Claude Code data exfiltration via DNS (CVE-2025-55284); Cursor "AgentFlayer" via malicious Jira ticket

### Mandated Controls
1. **Least-privilege tool scoping** — the planner often needs no tools; scope each tool to only what it needs
2. **Sandboxing** — OWASP ASI: "Never execute agent-generated code without strict sandboxing, input validation, and allowlisting"
   - **Firecracker microVMs:** strongest isolation
   - **gVisor:** syscall-level isolation
   - **V8 isolates:** JS, latency-critical
3. **Default-deny reads** of `.env`/secrets
4. **Egress allow-lists** — not egress defaults
5. **Human approval gates** for high-stakes or irreversible actions
6. **Emergency kill switches** and circuit breakers
7. **Continuous behavioral monitoring**

**Note:** CVE-2025-59528 (CVSS 10.0) and the Google Antigravity sandbox escape confirm that app-level controls fail without isolated execution.

### Frameworks
- Progent (programmable privilege control)
- Microsoft Agent Governance Toolkit (April 2026)

---

## MCP Security (New, Under-Secured Layer)

**Current state (Bitsight Research, December 2025):** ~1,000 MCP servers exposed on the public internet with no authorization controls — some allowing Kubernetes cluster command execution, CRM access, and arbitrary shell commands.

### Documented Threats
- **Tool poisoning:** malicious MCP server returns harmful tool definitions
- **Rug pulls:** tool behavior changes after trust is established
- **Tool/ghost shadowing:** malicious tool impersonates legitimate one
- **Command injection:** CVE-2025-49596 (MCP-Inspector, fixed in 0.14.1)
- **Confused-deputy attacks**
- First malicious MCP package appeared September 2025

### Controls
- OAuth-enhanced tool definitions + policy-based access control (ETDI)
- Gateway/proxy with authentication
- Audit logging of all tool calls
- Secret management for MCP server credentials
- Human-in-the-loop for tool calls accessing sensitive systems
- References: NSA MCP guidance (May 2026), OWASP MCP Top 10, CISA joint guidance (May 22, 2025)

---

## Secrets Management for AI Services

### The Scale of the Problem
GitGuardian State of Secrets Sprawl 2026 (March 2026):
- 28.65 million new hardcoded secrets added to public GitHub commits in 2025 (+34% YoY, largest single-year jump)
- AI-assisted commits leak secrets at **3.2%** vs 1.5% GitHub-wide baseline
- 1,275,105 AI service secrets detected in 2025 (+81% over 2024)
- 8 of 10 fastest-growing detector categories tied to AI services
- ~113,000 leaked DeepSeek API keys as one example

### OpenAI Key Management
- Use **project-scoped keys** (`sk-proj-` prefix, replaces legacy org-wide `sk-` keys since April 2024)
- Use **service account keys** for CI/agents
- Separate **Admin key** for the management API
- RBAC at org/project level; IP allowlisting
- **Ephemeral Realtime client secrets** for browser sessions (never expose long-lived keys client-side)
- On compromise: rotate immediately from the API Keys page

### Anthropic Key Management
- Keys (`sk-ant-`) are **workspace-scoped**
- **Admin API keys** (`ANTHROPIC_ADMIN_KEY`) for management — org-admin only
- **Workload Identity Federation:** exchanges OIDC tokens for short-lived `sk-ant-oat01-` tokens (default 3,600s, min 60s) — no `ANTHROPIC_API_KEY` secret to create, store, or rotate
- Official guidance: rotate keys ~every 90 days; set usage/spend limits as a safeguard

### Secrets Managers
| Tool | Approach | Notes |
|---|---|---|
| **HashiCorp Vault** | True dynamic/short-lived secrets | BSL license; acquired by IBM 2025 |
| **AWS Secrets Manager / Azure Key Vault / GCP Secret Manager** | Managed, scheduled rotation | Cloud-native |
| **Doppler** | SaaS secrets sync | Developer-friendly |
| **Infisical** | MIT, self-hostable | Open-source option |

Never store AI keys client-side — route through a server-side proxy.

### Python Implementation
- **pydantic-settings** (`BaseSettings` + `SettingsConfigDict(env_file=...)` with `SecretStr` and `.get_secret_value()`; supports `secrets_dir` for Docker secrets)
- **python-dotenv** (does not override existing env vars by default)
- Add `.env` to `.gitignore` on day one; ship `.env.example`
- Pre-commit hooks: **detect-secrets** / **Gitleaks** / **TruffleHog**

### Next.js Implementation
- Only `NEXT_PUBLIC_`-prefixed vars reach the browser (inlined at build time) — never put secrets there
- Access `process.env` only in a server-only Data Access Layer (`import 'server-only'`)
- React **taint APIs** (`experimental_taintObjectReference`/`taintUniqueValue`) prevent accidental client exposure
- Post-build: grep `.next/static/chunks` for leaked secrets

---

## Denial of Wallet (LLM10:2025 Unbounded Consumption)

**Threat:** "excessive and uncontrolled inferences, leading to denial of service (DoS), economic losses, model theft, and service degradation." Bills can be business-ending.

### Controls
- Set explicit `max_tokens` on **every** call
- **Token-based limiting** (input+output tokens) AND **cost-based caps**, not just request counts
- Pre-count tokens with `tiktoken` before sending
- Per-user/per-API-key/per-endpoint limits
- Timeouts and throttling
- Provider dashboard hard/soft spend caps
  - OpenAI: billing limits → 429 on hard limit
  - Anthropic: monthly cap + alerts (essential — billing is post-usage)
- Continuous logging/monitoring; graceful degradation

### Python Rate Limiting
- **slowapi** (Starlette/FastAPI, v0.1.9): Redis/Memcached backends; custom `key_func` for per-user/per-key limits; token-bucket/sliding-window via `limits`
- **fastapi-limiter** (Redis async)
- Atomic Redis+Lua token buckets for distributed limiting

### Next.js Rate Limiting
- **@upstash/ratelimit** (connectionless HTTP, v2.0.8): `fixedWindow`/`slidingWindow`/`tokenBucket`; multi-region; ephemeral in-memory DDoS cache
- **Arcjet:** rate limiting + bot detection + shield, `aj.protect(req)`

---

## Critical Next.js / React CVEs (2025–2026)

### React2Shell RCE — CVE-2025-55182 / CVE-2025-66478 (CVSS 10.0)
- **Unauthenticated RCE** exploitable on a default `create-next-app`
- React Server Components deserialization vulnerability
- **Actively exploited in the wild within days of disclosure**
- Follow-on CVEs landed through April 2026: CVE-2025-55184, CVE-2025-55183, CVE-2025-67779, CVE-2026-23864, CVE-2026-23869

**Action:** upgrade to patched Next.js (15.x patched line / 16.1.2+ with React 19.1+); validate inputs at the data layer; never trust middleware alone for security.

### Middleware Auth-Bypass — CVE-2025-29927 (CVSS 9.1)
- Spoofed `x-middleware-subrequest` header bypassed middleware-based authorization entirely
- **Fix:** upgrade (≥15.2.3, ≥14.2.25, ≥13.5.9, ≥12.3.5) AND strip the header at the reverse proxy/WAF

**Architectural lesson (applies beyond this CVE):** never rely on middleware alone for auth — do "optimistic" cookie checks in middleware but full session validation in the Server Component/Route Handler/Data Access Layer. In Next.js 16, `middleware.ts` is renamed `proxy.ts`.

---

## Python Security Patterns

### Type Safety and Validation (Pydantic v2)
- Use Pydantic models as request/response contracts in FastAPI
- `Field` constraints: `min_length`, `ge`/`le`, `EmailStr`
- Custom `@field_validator`/`@model_validator`
- Separate Create/Update/Response models — secrets (password hashes, internal fields) never serialize out
- `response_model` to filter output
- Validation is the first line of defense but not a substitute for authorization

### Dependency Security
- **pip-audit** (PyPA official): run in CI and as a pytest gate against the PyPA advisory DB
- Pin deps with hashes (`uv lock` / `uv pip compile --generate-hashes`)
- Add cool-off (`--exclude-newer "1 week"`) to dodge fresh malicious releases
- Behavioral scanners: **Socket.dev** / **GuardDog** / **Phylum**
- **Trusted Publishing (OIDC)** instead of long-lived PyPI tokens
- Real campaigns to know: Shai-Hulud worm (Nov 2025), GhostAction (Sept 2025, 570+ repos / 3,300+ secrets), PyPI phishing (pypj.org, July 2025)

### Static Analysis
- **Bandit** (~80 plugins: weak crypto, `shell=True`, `eval`/`exec`, `assert` for security [B101 — stripped under `-O`], `random` for secrets, bind-all-interfaces) — run in pre-commit at MEDIUM severity/HIGH confidence
- **Semgrep** (taint tracking, OWASP rulesets, reachability in paid Supply Chain)
- **CodeQL**, **Ruff** security rules, **Pysa**

### Async Pitfalls
- Never block the event loop with sync I/O — use `run_in_threadpool` (Starlette) for sync libs
- Avoid shared mutable state across coroutines
- Set timeouts on all awaits to bound resource use

### Authentication and Authorization
- OAuth2 + JWT via `fastapi.security` (`OAuth2PasswordBearer`)
- Hash passwords with **bcrypt** (passlib) or **Argon2**
- Store JWT/refresh config in pydantic-settings with `SecretStr`
- Short-lived access tokens + rotating refresh tokens
- Never use `assert` for authorization (stripped under `-O`)
- RBAC and BOLA checks on every object access (OWASP API Top 10)
- Never log auth headers/cookies/tokens — use a logging filter to scrub PII

---

## TypeScript / Next.js Security Patterns

### TypeScript as a Security Mechanism
- Strict types + Zod runtime validation at every trust boundary
- Strict schema validation also blunts prototype-pollution (reject `__proto__`/`constructor` keys) — the exact class CVE-2025-55182 abused

### Server Actions and RSC
- Server Actions deserialize client input — validate with Zod, treat as untrusted
- Never hardcode secrets in Server Action code (source-exposure CVE risk)
- CSRF protection for Server Actions invoked from forms: Next.js encrypts action IDs; set a persistent `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` across instances

### Auth.js v5 / NextAuth
- All env vars prefixed `AUTH_` (auto-inferred)
- `AUTH_SECRET` is mandatory
- **JWT sessions:** encrypted (JWE) in HttpOnly cookies; can't be revoked pre-expiry but Edge-compatible
- **Database sessions:** allow revocation/"sign out everywhere" but not Edge-compatible
- Split config: `auth.config.ts` (edge-safe) vs `auth.ts` (with adapter) so middleware stays Edge-compatible
- Always validate sessions server-side for sensitive ops, not just in middleware

### Cookie Security Flags
HttpOnly + Secure + SameSite + `__Host-` prefix

### Content Security Policy
- Start with `default-src 'self'`
- Prefer **nonce-based** CSP over `'unsafe-inline'`
- Libraries: **Nosecone** (Arcjet) / set headers in `proxy.ts`
- Also add: HSTS, X-Content-Type-Options, Permissions-Policy, X-Frame-Options/`frame-ancestors 'none'`
- Validate with Google CSP Evaluator

### Server vs Client Data Exposure
Most dangerous anti-pattern: passing whole DB rows from Server to Client Components.
- Pass only needed, sanitized fields
- Use `import 'server-only'`
- Taint APIs (`experimental_taintObjectReference`/`taintUniqueValue`)
- With Supabase/Postgres: Row-Level Security as a DB-layer backstop

### API Route Security
- Rate limiting (@upstash/ratelimit, Arcjet)
- Explicit CORS allow-lists
- Validate all inputs server-side with Zod

### Dependency Security
- `npm audit` as a blocking CI step; lockfile committed
- **Socket** for behavioral analysis on PRs
- Pin GitHub Actions to commit SHA, not tag (GhostAction lesson)
- Renovate/Dependabot auto-merge patch releases for next/react/react-dom

---

## AI Model Supply Chain (LLM03:2025)

### Threats
- Malicious weights, pickle-based RCE (PickleScan bypasses: CVE-2025-10156 CRC differential, CVE-2025-10157 subclass substitution — single scanners insufficient)
- Poisoned training data
- Real incidents: Ultralytics compromise (Dec 2024, ~80M downloads/mo), LiteLLM supply-chain compromise, Langflow code injection (CVE-2025-3248)

### Controls
- Prefer **safetensors** over pickle
- Allow-lists not block-lists for model file types
- Hash verification before loading
- Sandboxed model loading
- Update PickleScan ≥0.0.31
- Generate **AI-BOMs** (OWASP AIBOM generator)

---

## Supply-Chain Security (SBOM/Sigstore/Provenance)

- Generate SBOMs: **Syft** (broad coverage) or **cyclonedx-py** (build-tool integrated, most accurate at capture time)
- Sign artifacts: **cosign** (keyless via Sigstore/Fulcio/Rekor + OIDC)
- Target **SLSA Level 2→3** provenance (SLSA GitHub Generator gives L3 on GitHub Actions)
- **in-toto attestations**
- Verify at deploy time via admission policy (Kubernetes admission controller)
- Sonatype: 454,600+ new malicious packages reported in 2025
- **SBOM alone is insufficient** — pair with provenance + signature verification (SolarWinds/GhostAction lesson)

### CI/CD Security Gates
SAST (Bandit/Semgrep/CodeQL) + SCA (pip-audit/npm audit/Snyk/Trivy/OSV-Scanner) + secret scanning (Gitleaks/detect-secrets/TruffleHog) + DAST (OWASP ZAP) as **blocking** pipeline gates.

**Note on SAST limitations:** a 2026 benchmark found 78% of confirmed vulnerabilities detected by only 1 of 5 SAST tools — SAST is structurally insufficient for semantic flaws.

---

## Vibe Coding / AI-Generated Code Risks

**The data (multiple independent sources, 2025–2026):**
- **Veracode (July 2025):** 45% failure rate on security tests; XSS failing 86%, log injection 88%; rate "virtually identical to where it stood two years ago" as of Spring 2026
- **Apiiro (Sept 2025):** 10× spike in security findings (10,000+/month by June 2025); 3–4× more commits; privilege-escalation paths +322%, architectural design flaws +153%
- **CodeRabbit:** AI-co-authored PRs had ~1.7× more major issues, 2.74× more security flaws
- **Tenzai (Dec 2025):** 5/5 AI agents introduced SSRF; 0/15 apps had CSRF protection or security headers
- **IEEE-ISTAS:** +37.6% critical vulns after 5 rounds of AI refinement (iteration compounds flaws)
- **Slopsquatting:** attackers pre-register hallucinated package names

### Mitigations
1. Mandatory human review gates for AI-generated PRs
2. Strict AI "rule files" (ban `eval`, require env vars + parameterized queries)
3. Secret-scanning pre-commit hooks
4. Enforce security at the infra layer (WAF/Zero Trust gateway) — SAST alone is insufficient
5. AI code review as a quality gate on AI-generated code (CodeRabbit, Greptile, etc.)

---

## AI Threat-Modeling Frameworks

| Framework | Focus |
|---|---|
| **MITRE ATLAS** | Adversarial ML tactics/techniques |
| **NIST AI RMF 1.0** (Jan 2023) | Govern/Map/Measure/Manage functions |
| **NIST GenAI Profile (AI 600-1)** (July 2024) | Generative AI-specific risks |
| **Draft NIST Cyber AI Profile (IR 8596)** (Dec 2025, comment period closed Jan 2026) | Overlays Secure/Detect/Thwart focus areas on CSF 2.0; High/Moderate/Foundational priorities |
| **NIST COSAiS** (concept paper Aug 2025) | SP 800-53 control overlays for AI systems |
| **Databricks AI Security Framework v2.0** | Data/ML platform focus |
| **ISO/IEC 42001** | AI management system standard |

---

## Zero-Trust Principles for AI Systems

- Least-privilege for every actor including **non-human/agent identities**
- Verify explicitly at each layer (don't trust middleware/network position)
- Short-lived scoped credentials for all service-to-service calls
- Per-request authorization at the data layer
- OIDC for CI/CD to cloud (no long-lived secrets)

---

## Container and Kubernetes Security

- Run as non-root; read-only filesystem
- Minimal base images (distroless/Chainguard/Alpine)
- Trivy/Checkov scanning in CI
- Egress firewall/allow-list; block cloud-metadata access (IMDSv2, hop limit 1)
- Admission controllers (Kyverno) to require signed images

---

## Observability for Security

- Structured logging to a SIEM
- Log security events (authn failures, authz denials) at a distinct level
- Anomaly detection on LLM usage/cost (unusual spend = potential credential compromise or DoS)
- For LLMs: trace each guardrail step (e.g., Langfuse `@observe`) and monitor risk scores
- OpenTelemetry tracing
- Data privacy: Presidio-based PII detection/redaction; data minimization; never log request bodies/tokens

---

## Staged Implementation Roadmap

### Stage 1 — This Week (Stop Active Bleeding)
1. **Patch Next.js/React** to current patched versions; strip `x-middleware-subrequest` at proxy/WAF; confirm no auth relies solely on middleware — verify with CVE-2025-29927 / CVE-2025-66478 detection templates
2. **Turn on secret scanning** (Gitleaks/detect-secrets) as pre-commit + CI gate; rotate any exposed AI keys; move to project/workspace-scoped keys; set provider spend caps
3. **Add token-aware rate limiting + `max_tokens` + spend alerts** to every LLM endpoint

### Stage 2 — This Quarter (Build the Baseline)
4. Wire **SAST + SCA + DAST** into CI as blocking gates; pin deps with hashes and Actions to SHA; generate SBOMs; sign artifacts with cosign (SLSA L2)
5. Stand up a **guardrail layer** (NeMo Guardrails or LLM Guard + Llama Guard 3) with input/retrieval/execution/output rails; enforce Pydantic/Zod schemas on all model output
6. For **RAG:** authenticate document sources, strip hidden text on ingest, enforce per-tenant isolation at the DB layer, encrypt the vector store
7. **Mandate human review gates** and "rule files" for AI-assisted PRs

### Stage 3 — This Year (Mature the Program)
8. Adopt **NIST AI RMF** + map to the Cyber AI Profile and ISO 42001; maintain an AI/Agent inventory with named owners
9. **Sandbox all agents** (Firecracker/gVisor), enforce least-privilege tool scoping, default-deny secret reads, egress allow-lists, human approval for high-impact actions
10. Move secrets to a manager with dynamic/short-lived credentials (Vault) or OIDC federation (Anthropic WIF, OpenAI service accounts); rotate on 90-day cadence

### Thresholds That Change the Plan
- Any agent with write/financial/PII access → require sandbox + human-in-the-loop before launch
- LLM spend variance >X% week-over-week → tighten token quotas
- Any unauthenticated public endpoint → WAF + rate limit mandatory
- SAST/SCA HIGH/CRITICAL finding → block deploy

---

## The First Rule

"The first sentence of any LLM defense is: don't grant the capability you can't afford to have misused." Capability minimization is more reliable than any filter.

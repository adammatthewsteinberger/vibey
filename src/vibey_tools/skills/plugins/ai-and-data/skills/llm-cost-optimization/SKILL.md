---
name: llm-cost-optimization
description: "Production reference for LLM token economics, cost optimization, and prompt engineering on Azure. Covers tokenization and pricing asymmetry, prompt caching (Azure/Anthropic/Google), model routing and cascades, PTU vs PAYG break-even, Azure APIM AI gateway, semantic caching, context window engineering, prompt/context compression (LLMLingua, LongLLMLingua, RECOMP, Selective Context, extractive compression), caveman/telegraphic prompting, token-lean serialization formats (TOON/Markdown/YAML vs JSON/XML), output control (Concise CoT, Chain-of-Draft), fine-tuning for cost, Batch API, structured outputs, conversation history management, and Azure-specific deployment patterns. Use when optimizing LLM spend, compressing prompts or context, choosing a compression library, picking token-lean formats, reducing output verbosity, designing cost-efficient AI architectures, troubleshooting token costs, engineering prompts for performance, or sizing Azure OpenAI deployments."
---

# LLM Cost Optimization, Prompt Engineering & Context Engineering — Azure Reference

## The Three Core Levers (in ROI order)

1. **Model routing** — route routine traffic to cheaper models, escalate only uncertain requests (60–80% cost reduction on routine queries per Microsoft guidance; validated RouteLLM benchmark: 95% GPT-4 quality at 26% GPT-4 calls, ~48% cheaper)
2. **Prompt caching** — restructure prompts for a stable prefix (Azure: ~50% off input; Anthropic: 90% off cache reads)
3. **Deployment pricing** — Batch API (50% off), PTU reservations (up to 70% off hourly), right-tier matching

**Governance is architecture, not monitoring.** Without per-request token logging and cost attribution, optimization is guesswork.

---

## Token Economics Fundamentals

### Tokenization
- **`o200k_base`** (GPT-4o, o-series, GPT-4.1+): 200K-token vocabulary; ~10% fewer tokens for English than `cl100k_base`; 20–40% fewer tokens for non-Latin scripts (Chinese, Japanese, Arabic)
- **`cl100k_base`** (GPT-4/3.5/ada-002): 100K-token vocabulary
- Always resolve encodings with `tiktoken.encoding_for_model()` — never hardcode. Tokenizer drift across model generations can silently inflate per-request cost by up to ~35% at unchanged per-token prices.
- The only ground truth for billing is the API's `usage` object (includes `cached_tokens` and `reasoning_tokens` breakdowns)

### Input/Output Pricing Asymmetry — **Architectural Implication**
- Input (prefill): one parallel forward pass over all tokens
- Output (decode): one sequential forward pass **per token** → output costs 3–8× input
- Azure GPT-4o example: input $2.50/1M vs output $10/1M (4×)
- **Design implication**: minimize output length for cost-sensitive paths; be explicit about output length in the prompt

### Reasoning Tokens
- Billed at **output rates** (expensive)
- Invisible in the response body; surfaced in `output_tokens_details.reasoning_tokens`
- Do NOT persist across turns
- Consume the `max_tokens` budget — a complex task can burn 8,000+ reasoning tokens before a 300-token answer
- **Anti-pattern trap**: setting `max_tokens` too low yields `finish_reason: "length"` with empty content because reasoning consumed the entire budget
- **Rule**: set `max_tokens` to ≥4× expected visible output for reasoning models
- Track reasoning tokens as a first-class metric
- Worth it for genuine multi-step reasoning (math, code, legal analysis); wasteful on pipelines expecting short outputs

---

## Azure Pricing Models

### Standard (PAYG)
- Per-token billing; quota in TPM/RPM
- **Global Standard**: routed worldwide, highest throughput, lowest rate
- **Data Zone Standard**: US/EU data residency
- **Regional Standard**: single region, highest per-token cost
- Prompt caching and Batch discounts apply automatically

### PTU (Provisioned Throughput Units)
- Reserved capacity; predictable latency
- Hourly: ~$1/PTU/hr (GPT-4o Global, Jan 2025)
- Monthly reservation: up to 64% off hourly
- 1-year reservation: up to 70% off (~$0.30/PTU/hr)
- Minimums: 15 PTU (Global/Data Zone, increments of 5), 50 PTU (Regional, increments of 50)
- PTU sizing depends on output:input ratios (gpt-5: 1 output = 8 input tokens; gpt-4.1: 1 output = 4 input)
- **Best practice**: deploy first, then buy the reservation — reservations guarantee discount, not capacity
- Cached tokens count 0% toward PTU utilization (100% off on Provisioned)

### Break-Even: PTU vs PAYG
- PTU generally wins above ~50% sustained utilization and ~150–200M tokens/month on GPT-4o
- This is a practitioner rule-of-thumb — not a single official Microsoft figure
- Bursty workloads may justify PTU earlier than the token volume suggests (for latency predictability)

### Batch API
- **50% off** Global Standard pricing
- Async, 24h SLA (often 1–6h in practice)
- Up to 50K requests / 200MB per input file
- **Ideal for**: evals, nightly summarization, classification queues, embedding refreshes

### Azure Credits Warning
- Microsoft for Startups credits (up to $150K) cover only "models sold directly by Azure" (Azure OpenAI)
- **Does NOT cover** third-party Marketplace models (Anthropic Claude, Meta Llama via Marketplace, etc.) — a documented billing trap that hit ≥20 startups with surprise invoices in early 2026
- Filter the catalog by "Direct from Azure" to stay covered
- Billing data lags 24–72h

---

## PTU Spillover (GA August 2025)

Routes PTU overage to a Standard deployment on non-200 responses (429 PTU-exhausted; 400 long-context >128K on gpt-4.1 PTU; 500/503).

**Enable via:**
- `spilloverDeploymentName` (all requests)
- `x-ms-spillover-deployment` header (per-request)

**Billing:** PTU requests = hourly only; spilled requests = standard token rates.

**Pattern**: size PTU for average load; spill peaks to PAYG. Monitor by splitting `Azure OpenAI Requests` metric by `ModelDeploymentName` + `StatusCode`.

---

## Prompt Caching — The Cache Golden Rule

**Stable content first, dynamic content last.**

Order:
1. System prompt (most stable)
2. Tool definitions
3. Static documents/corpus
4. Conversation history (older first)
5. Current user message (most dynamic, last)

**A single byte of drift before the cached boundary invalidates the entire prefix.** A documented production failure: team's system prompt opened with `f"Today is {datetime.now().date()}…"` which dropped cache hit rate to ~1%.

### Azure/OpenAI Caching
- Automatic; no opt-in required
- ~50% input discount (some 2026 sources cite up to 90% on newer families); no write penalty
- Minimum: ≥1,024 tokens with identical first 1,024-token prefix
- Cache hits accrue every 128 tokens after the initial 1,024
- Verify via `cached_tokens` in `prompt_tokens_details`
- In-memory caches: clear after 5–10 min of inactivity (max 1h)
- GPT-4.1 / GPT-5 family: extended retention up to 24h via `prompt_cache_retention: "24h"`
- Use `prompt_cache_key` to improve routing/hit rate
- Regional/model-version splits do NOT share caches

### Anthropic Caching
- Explicit `cache_control` breakpoints (≤4 per request)
- Cache read = 0.1× input cost (90% off)
- Cache write = 1.25× (5-min TTL) or 2× (1-hr TTL)
- Break-even: ~2–3 cache reads per write
- Expanded to a 5M-token cache
- Real-world result: one developer cut $8,000→$800/month on a RAG system

### Google Gemini Caching
- Explicit user-managed cache objects with multi-day TTLs

### Caveats
- Tool-definition churn invalidates the tool-list cache
- Compacting conversation history destroys its cached prefix

---

## Context Window Engineering

### Token Budget Allocation
**Token budget is a first-class design constraint.** Allocate explicit budgets per component:
- System prompt
- Tool definitions
- Conversation history
- Retrieved context (RAG)
- Output headroom (especially for reasoning models)

Optimize for **cost-per-task**, not tokens-saved-in-isolation.

### Conversation History Management (Cost Tiers)
1. **Naive** (full history): linear cost growth — only for short sessions
2. **Sliding window**: keep last N turns
3. **Rolling summarization** (MapReduce): summarize old turns, keep recent full
4. **Embedding-based selective retention**: retrieve most-relevant past turns
5. **Hybrid**: recent full + rolling summary + pinned facts
6. **External memory** (MemGPT/Letta): LLM-managed memory tiers; Cosmos DB/Redis/AI Search as backing store

Store session state in Azure Cosmos DB or Azure Cache for Redis. Compact conversation history infrequently at predictable boundaries (compacting breaks the stable cache prefix).

### LLMLingua Prompt Compression (Microsoft Research)
- **LLMLingua** (arXiv 2310.05736, EMNLP 2023): up to 20× compression with only ~1.5 point performance drop
- **LLMLingua-2**: 3–6× faster than LLMLingua-1; task-agnostic
- **LongLLMLingua**: improves RAG by up to 21.4% using only 1/4 of the tokens
- Stacks with caching — cache the compressed prompt
- Use when: long-doc RAG with many retrieved passages; cost-sensitive pipelines; large static context

### "Lost in the Middle"
Per Liu et al. (TACL 2024, arXiv:2307.03172): performance "significantly degrades when models must access relevant information in the middle of long contexts, even for explicitly long-context models." Place critical information first or last. Rerank retrieved docs so the gold passage sits at an extremity.

---

## Prompt & Context Compression (Provider-Agnostic)

Caching and routing beat any prompt-rewriting trick — apply this section only after the structural levers above. Measure **tokens-per-completed-task**: over-compression triggers retries and clarifications that cost more than they save.

### The Counterintuitive Research Consensus
**Extractive compression — selecting whole sentences — often outperforms fancier token-pruning and enables up to ~10× compression with minimal accuracy loss** (UC Berkeley, "Characterizing Prompt Compression Methods for Long Context Inference," arXiv 2407.08892, ICML 2024 Es-FoMo). Reach for perplexity-based pruning (LLMLingua) only when query-aware long-context demands it.

### Compression Libraries
- **LLMLingua / LongLLMLingua / LLMLingua-2** — see the LLMLingua subsection above. `pip install llmlingua`; stacks with caching (cache the compressed prompt).
- **RECOMP** (arXiv 2310.04408): "Retrieve, Compress, Prepend" for RAG. Extractive + abstractive compressors to **~6%** of original; emits an empty summary on irrelevant docs (selective augmentation). Can over-compress on multi-hop queries.
- **Selective Context** (EMNLP 2023): self-information pruning via a base LM; process 2× more content, save 40% memory/GPU. `pip install selective-context`.
- **Soft-prompt / learned** (need fine-tuning + weight access): Gist tokens (up to 26×, NeurIPS 2023), AutoCompressor (~30:1), ICAE (512→32/64/128 memory tokens).
- **PCToolkit** bundles Selective Context, LLMLingua, LongLLMLingua, SCRL, KiS as plug-and-play.

### Caveman / Telegraphic Prompting — Oversold
Stripping articles, prepositions, pleasantries, and filler claims up to 75% savings; independent benchmarks land at **14–21%** on real coding tasks (Guzik: Sonnet 14%, Opus 21%; ncvgl SWE-bench Pro ~14%) because input/context dominates the bill there, with quality staying 100%. Best for output-heavy interactive sessions. The middle ground — "Be concise, no filler, skip pleasantries" — captures most savings without unreadable telegraph. Politeness tokens are pure cost.

### Serialization Format Choice (20–80% Token Swing)
Roughly **TOON < Markdown < YAML < compact JSON < pretty JSON < XML**. XML needs ~80% more tokens than Markdown for the same nested data; YAML ~36% cheaper than JSON per record; TOON ~30–50% savings on uniform tabular arrays (weak on nested/irregular data). **But** use XML *tags* for prompt structure (semantic clarity, per Anthropic) and avoid forcing JSON output on reasoning — it can degrade quality 10–15%.

### Output Verbosity Control
- **Concise CoT** (arXiv 2401.05618): −48.70% response length, −22.67% per-token cost; watch a −27.69% accuracy hit on GPT-3.5 math.
- **Chain-of-Draft** (~5 words/step, arXiv 2502.18600): as little as **7.6% of CoT tokens** while matching/beating accuracy; on Claude 3.5 Sonnet's sports task, 189.4→14.3 output tokens (−92.4%) with accuracy rising 93.2%→97.3%.
- **Structured output does NOT save tokens** — JSON adds ~40% over free text; constrained decoding adds schema tokens + 10–30% latency. It guards weak models (Qwen2.5-Coder-7B 0%→75%) but degrades strong ones (GPT-5 extraction 86.9%→70% on complex schemas). For reasoning: two-step (free-form think → constrained format). See Structured Outputs below for the Azure API specifics.

---

## Model Routing & Cascades

**The single highest-ROI lever.** Task-to-tier mapping:

| Task type | Recommended tier |
|---|---|
| Classification, extraction, simple formatting | Nano/Phi-4-class |
| Chat, summarization, standard Q&A | Mini-class |
| Complex reasoning, code refactoring, multi-step analysis | Frontier/reasoning |

### RouteLLM (UC Berkeley/Anyscale/Canva, ICLR 2025)
- Matrix-factorization routing between strong/weak models
- Achieves 95% of GPT-4 performance using 26% GPT-4 calls (~48% cheaper)
- With LLM-judge-augmented training data: 14% of total calls (75% cheaper)
- Routers generalize to new model pairs without retraining

**Microsoft Foundry Model Router caveat**: "Balanced" mode is conservative — selects within ~1–2% quality range; one Microsoft field test measured only 4.5–14.2% savings. Validate on your own traffic before projecting the 60–80% figure.

### Implementation Options
- Rule-based: query length, keyword triggers, explicit complexity signals
- Classifier-based: fine-tuned on your traffic
- RouteLLM: research-grade, open-source
- Semantic Router: embedding-based intent classification

---

## APIM AI Gateway — Reference Architecture

**Deploy APIM as the AI gateway for every Azure OpenAI deployment.** This enables per-consumer token limits, per-team cost attribution, semantic caching, PTU→standard spillover routing, and content safety — all before the request reaches the model.

### Five AI-Gateway Policies
| Policy | Function |
|---|---|
| `llm-token-limit` | Per-key TPM/quota enforcement with prompt-token pre-calculation |
| `llm-emit-token-metric` | Per-consumer token metrics to App Insights (up to 5 custom dimensions) |
| `llm-semantic-cache-lookup` / `store` | Redis-backed vector semantic cache |
| `llm-content-safety` | Azure Content Safety integration |
| Backend pool + circuit breaker | Priority/weighted routing + circuit breakers per backend |

### Backend Pool Pattern
PTU backend (priority 1) → PAYG Standard (priority 2 / overflow). Circuit breaker per backend. `retry` policy honoring `Retry-After`.

### Reference Implementation
Azure-Samples/apim-genai-gateway-toolkit

### Cost Attribution
- Subscription keys map to cost attribution
- JWT enables per-user attribution
- Up to 5 custom dimensions on `llm-emit-token-metric`
- Note Azure Monitor's 10-dimension/50,000-time-series limits when designing custom dimensions

---

## Semantic Caching

**APIM + Redis Enterprise pattern** for FAQ/support bots:
- Embed query → vector search cache → return if cosine similarity above threshold (~0.95)
- Add `rate-limit` after lookup to protect backend if cache is unavailable
- Tune `score-threshold` (lower = stricter match)

**Output cache** (simple TTL) cuts FAQ/deterministic traffic 30–80%.

**When NOT to use semantic caching**: personalized queries, real-time data, high-diversity query patterns.

---

## Advanced Prompt Engineering

### System Prompt Structure
```
[Role and objective]
[Constraints and rules — positive instructions ("always do X") outperform negative]
[Output format specification]
[Examples if needed]
```

### Reasoning Techniques (with cost trade-offs)
| Technique | Cost | When to use |
|---|---|---|
| Zero-shot CoT ("think step by step") | Moderate (adds output tokens) | Multi-step tasks on non-reasoning models |
| Few-shot CoT (3–8 exemplars) | Higher (adds input tokens) | Complex tasks needing demonstrated format |
| Self-consistency (sample N, vote) | N× cost | High-stakes decisions |
| Tree of Thoughts (branching) | Expensive | Deep search/planning problems |
| Dedicated reasoning model (o-series) | High but predictable | Genuine multi-step reasoning |

**Rule**: use dedicated reasoning models for genuine multi-step problems; use CoT-prompted standard models when you need to see/control the reasoning and cost matters.

### Structured Outputs
**Prefer Structured Outputs (JSON Schema, `strict: true`)** over legacy JSON mode — guarantees schema adherence, not just valid JSON.

Azure constraints:
- All fields must be `required` (emulate optional via `["type","null"]`)
- `additionalProperties: false`
- ≤100 properties, ≤5 nesting levels
- Not compatible with `parallel_tool_calls` (set to false) or On Your Data/Assistants
- Supported on: gpt-4o (2024-08-06+), gpt-4.1 family, o1/o3/o3-mini/o4-mini

### Sampling Parameters
- Temperature 0 + `seed` for deterministic/factual outputs
- Higher temperature/top-p for creative generation
- Always set `max_tokens` — no cap means unbounded cost exposure

### Dynamic Few-Shot
Retrieve similar examples via embedding search rather than hardcoding — enables more relevant examples without growing the static system prompt.

### Prompt-as-Code
- Git-version prompts
- Test against golden eval sets before deploying
- Store prompts in Azure App Configuration for runtime updates without redeploy
- A/B test prompt changes with proper statistical significance

---

## Tool Calling Cost Optimization

- **Write terse tool descriptions** — verbose schemas waste input tokens
- **Limit tools** — performance degrades past ~10 tools per call
- **Progressive/intent-based tool exposure** — send only relevant tools per query type
- Use `parallel_tool_calls` for independent calls (reduces round-trips)
- Cache tool definitions in the system prefix (they're stable → high cache hit rate)
- Fine-tuning with tool examples can replace verbose tool definitions at inference time

---

## Fine-Tuning for Cost (Distillation Pattern)

1. Set `store: true` on production frontier-model calls to capture completions
2. Accumulate hundreds–thousands of high-quality examples (minimum 10 stored completions)
3. Fine-tune a smaller model (e.g., GPT-4.1-nano) on teacher's outputs
4. Validate quality delta is acceptable before routing production traffic

**Expected result**: ~90% quality at ~10% cost.

**Azure fine-tuning specifics:**
- Training files: JSONL format; per-token training fee + hourly hosting cost for deployed custom models
- **"Fine-tune zombie" trap**: delete unused fine-tuned deployments to avoid hourly hosting cost
- Supported: gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-nano, o4-mini (Reinforcement Fine-Tuning), Llama 4 Scout
- Global Standard is the default deployment for new fine-tunes (cheaper than regional)
- Prompt caching works on fine-tuned models

---

## Embeddings Cost Optimization

| Model | Dimensions | Price/1M | MTEB | Notes |
|---|---|---|---|---|
| `text-embedding-3-small` | 1,536 | ~$0.02 | 62.3 | OpenAI-ecosystem default; 5× cheaper than ada-002 |
| `text-embedding-3-large` | 3,072 | ~$0.13 | 64.6 | ~2.3 MTEB points better; Matryoshka-truncatable |
| `ada-002` | 1,536 | ~$0.10 | 61.0 | Legacy; replace with 3-small |

**Matryoshka**: store full-dim once; truncate per index (768 dims halves storage). Standard in modern models.

**Cost reduction rules:**
- Cache static-document embeddings by content hash — never re-embed unchanged docs
- Cache common-query embeddings
- Quantize stored vectors (fp32→fp16/int8)
- Batch embedding requests to respect rate limits
- Use ANN over exact search at scale

---

## Rate Limiting & 429 Handling

| Error | Meaning | Response |
|---|---|---|
| 429 | TPM/RPM quota or PTU 100% utilized | Respect `Retry-After`; exponential backoff with jitter |
| 503 | Capacity/server issue | Backoff + failover to another deployment |

Azure returns `x-ratelimit-*` headers. The APIM circuit breaker handles this automatically at the gateway layer.

---

## Azure Monitor Metrics Reference

**Key metrics to track:**
- `ProcessedPromptTokens`, `GeneratedTokens`, `TokenTransaction` (Processed Inference = prompt+generated)
- `InputTokens`, `OutputTokens`, `TotalTokens`
- `ProvisionedUtilizationV2` (PTU utilization)
- `AzureOpenAIContextTokensCacheMatchRate` (`Prompt Token Cache Match Rate`)
- `FineTunedTrainingHours`
- Latency: Time to Response, Time to Last Byte, Time Between Tokens — **do NOT use the legacy Cognitive Services `Latency` metric**

**Dimensions**: split by `ModelDeploymentName` / `ModelName`.

**Export**: diagnostic settings → Log Analytics (KQL); build workbooks/Managed Grafana dashboards.

**`llm-emit-token-metric` policy** supports OpenAI, Anthropic Messages, and Google Vertex schemas.

---

## Cost Unit Economics

**Build cost-per-task, not cost-per-token.** RAG cost breakdown:
- Embedding (one-time per document)
- Storage
- Retrieval query embedding (per query)
- Generation (retrieved context dominates — often 80%+ of per-query cost)

**Multi-agent fan-out**: multiplies LLM calls; "your average cost per task is a lie" (GrisLabs tracked 1,127 agent runs: median $1.22, p95 $22.14 — an 18× tail). Implement:
- Per-user/session/feature anomaly detection
- Per-feature token budgets
- Hard per-run token/cost ceilings

---

## Real-World Optimization Recipes

| Recipe | Expected savings | Requirement |
|---|---|---|
| **R1 — Model routing** | 60–80% on routine queries | Quality eval confirming <1–2% delta |
| **R2 — Prompt caching** | 40–50% on input tokens | Stable ≥1,024 token prefix; verify via `cached_tokens` |
| **R3 — Semantic caching** | 30–80% on repeat traffic | Low query diversity; non-personalized/non-realtime answers |
| **R4 — Batch API** | 50% at 24h SLA | Async workloads (evals, nightly processing, embedding refresh) |
| **R5 — LLMLingua compression** | Up to 20× token reduction | Long-doc RAG; accept ~1.5 point quality drop |
| **R6 — Distillation** | ~90% quality at ~10% cost | High-volume domain-specific tasks; hundreds of teacher completions |
| **R7 — PTU right-sizing** | Up to 70% vs hourly | 30–60 days telemetry; P95 hourly throughput; sustained >50% utilization |

**Stack order**: Instrument first → quick wins (caching + batch) → routing → semantic cache → PTU commitment → distillation.

---

## Staged Implementation Roadmap

**Stage 1 — Instrument before optimizing (week 1).** Deploy APIM as AI gateway with `llm-emit-token-metric` (dimensions: team/app/user). Enable diagnostic settings → Log Analytics. Tag every deployment by feature. Compute cost-per-task on your top 3 features. Threshold: attribute >90% of spend to a feature/team.

**Stage 2 — Quick wins (weeks 2–3).** (a) Restructure prompts for stable ≥1,024-token prefix; confirm `cached_tokens` > 0. (b) Cap `max_tokens` (600–800 chat). (c) Move async workloads to Batch API. (d) Cache static-doc embeddings by content hash. Expected: 30–50% reduction.

**Stage 3 — Model routing (weeks 4–6).** Default to mini/nano-class; build rule- or classifier-based router escalating on complexity/low-confidence. Re-run evals to confirm no quality regression. Expected: additional 40–70% on routine traffic. Hold routing if quality delta exceeds 1–2 eval points.

**Stage 4 — Semantic caching + compression (weeks 6–8).** Add APIM semantic cache (Redis Enterprise) for FAQ/support traffic. Apply LLMLingua to long-doc RAG passages. Threshold: only where query diversity is low and answers aren't personalized/real-time.

**Stage 5 — PTU commitment (after 30–60 days telemetry).** Pull P95 hourly throughput. If GPT-4o-class monthly volume >150–200M tokens AND sustained utilization >50%: deploy PTU for average load, enable spillover for peaks, buy 1-month reservation first, then 1-year once steady state confirmed.

**Stage 6 — Distillation (ongoing).** Set `store: true` for high-volume domain-specific tasks. Accumulate hundreds–thousands of frontier completions. Fine-tune nano/mini behind a quality gate. Delete idle fine-tuned deployments.

**Re-evaluate model selection quarterly.** Prices and quality move fast; a model that was your only option may now be 5× pricier than a newer SKU within 1–2 eval points.

---

## Anti-Patterns

1. **Full history every turn** — linear cost growth; use sliding window or summarization
2. **Dynamic content before static** (e.g., timestamp in system prompt) — breaks prompt caching
3. **Frontier model for trivial tasks** — use routing
4. **Verbose tool schemas** — wastes input tokens; cache them in stable prefix
5. **Sequential calls for independent subtasks** — parallelize with `parallel_tool_calls` or asyncio
6. **JSON mode over Structured Outputs** — use `strict: true` JSON Schema instead
7. **No `max_tokens` set** — unbounded cost exposure
8. **Re-embedding unchanged documents** — cache by content hash
9. **Unsanitized injection vectors** — RAG retrieved content can carry injection payloads
10. **Optimizing without evals** — cost savings are assumed quality-neutral; they are not
11. **Ignoring reasoning token billing** — reconcile against API `usage` object and Azure invoice
12. **Using Marketplace models without checking billing coverage** — not covered by Azure credits/sponsorship

---
name: rag-and-agents
description: "Production reference for RAG (Retrieval-Augmented Generation) and AI agent development covering document parsing, chunking strategies (parent-child, contextual retrieval), embedding models, vector databases, hybrid search with reranking, GraphRAG, RAGAS evaluation, agent frameworks (LangGraph, CrewAI, Microsoft Agent Framework, Foundry Agent Service), MCP, multi-agent patterns, computer use, and Azure-native RAG (Azure AI Search, Foundry IQ). Use when designing or debugging RAG pipelines, choosing vector databases, building agent systems, evaluating retrieval quality, or architecting Azure AI Search solutions."
---

# RAG & AI Agent Development — Production Reference

## The Decision Framework

**Start naive → add complexity only when evaluation shows a quality ceiling.**

Progression:
1. Naive RAG (embed-retrieve-stuff)
2. Hybrid search + semantic reranking
3. Parent-child chunking + better parsing
4. Contextual retrieval (Anthropic)
5. Advanced RAG (query transforms, multi-query, decomposition)
6. GraphRAG or agents — only when steps above have hit their ceiling

**Each step adds cost. Advance only when a 50–200 QA golden set proves it.**

---

## RAG Fundamentals

**Four problems RAG solves:**
1. Hallucination (grounds answers in retrieved documents)
2. Knowledge cutoff (retrieves current private data)
3. Private-data access (indexes your corpus)
4. Verifiable sourcing (enables citations)

**The full pipeline:** ingestion → chunking → embedding → indexing → query processing → retrieval → reranking → context assembly → generation

**RAG vs Fine-tuning vs Long-context:**
- **RAG**: dynamic/proprietary knowledge needing citations; audit trail
- **Fine-tuning**: changing behavior, format, tone, domain style
- **Long-context stuffing**: single-document deep reasoning where the whole doc fits; no extra infra

They combine — fine-tune for domain language, RAG for facts.

**"Lost in the middle" (Liu et al., TACL 2024):** performance degrades significantly when relevant information is in the middle of long contexts, even for explicitly long-context models. Critical info should be first or last. A 1M-token window is not a license to fill it.

**Quality framework — the "3 C's":**
- **Coverage**: right docs are indexed
- **Correctness**: retrieval finds them
- **Coherence**: generation uses them faithfully

---

## Document Parsing — Honest Comparison

| Parser | F1 (benchmark) | Best for | Cost | Notes |
|---|---|---|---|---|
| **LlamaParse** | ~92% | Complex layouts | ~$0.10/page (top tier), API-only | Multimodal LLM-based; highest accuracy |
| **Azure Document Intelligence** | ~90% structured, ~75% free-form | Azure workloads; standardized forms | ~$1.50/1K pages (prebuilt) | Layout model outputs Markdown; natively callable as AI Search skill |
| **Docling** (IBM, MIT) | ~88%, ~45 pages/sec GPU | Self-hosted; MCP server available | Free | Best open-source; fully local for sensitive data |
| **PyMuPDF4LLM** | — | Digital text; speed/lightness | Free | Fully local |
| **Unstructured** | — | 30+ formats with built-in chunking | Free/paid | Broad format support |

**For RAG**: Markdown output beats JSON — chunks cleanly while preserving hierarchy.

**Azure Document Intelligence Layout model**: produces Markdown (`MarkdownOutputFormat`), extracts tables/selection-marks, cross-page tables (since Ignite 2025); the cheaper `Read` model handles OCR/handwriting only.

**Pre-processing checklist:** Unicode normalization, header/footer/boilerplate removal, language detection, PII scrubbing (Azure AI Language / Presidio / Content Safety), quality filtering, dedup (exact + near-duplicate via MinHash/SimHash).

---

## Chunking — The Highest-ROI Lever

### Standard Strategies
| Strategy | How | When to use |
|---|---|---|
| **Recursive character splitting** | Split by newlines, spaces, chars | Standard baseline; default in LangChain |
| **Markdown/HTML header splitters** | Split at header boundaries | When document structure matters |
| **Semantic chunking** | Embedding-similarity breakpoints | When topics vary within a document |

### Parent-Child (Hierarchical) — **Single Highest-ROI Production Pattern**
- Embed small child chunks (100–500 tokens, often 100–200) for retrieval precision
- Return larger parent (500–2,000 tokens) to the LLM for generation context
- Children are "searchable atoms"; parents are "answer-ready context"

### Advanced Chunking
| Method | Description | Best for |
|---|---|---|
| **Sentence-window** | Retrieve a sentence, expand ±k neighbors | Conversational/factoid |
| **Late chunking** (Jina, 2024) | Embed full doc first, pool per-chunk so chunk embeddings retain document context | Any domain with long documents |
| **Contextual Retrieval** (Anthropic, Sept 2024) | Prepend LLM-generated chunk-specific context summary before embedding/indexing | General — see numbers below |

**Contextual Retrieval verified numbers (Anthropic, Sept 2024):**
- Contextual Embeddings alone: 35% failure reduction (5.7% → 3.7%)
- + Contextual BM25: 49% failure reduction (→ 2.9%)
- + Reranking: 67% failure reduction (→ 1.9%)
- One-time cost: ~$1.02 per million document tokens using prompt caching
- Caveat: gains vary by domain — large on fiction, near-zero on arXiv papers at top-20

**Size guidance by use case:**
- FAQ: ~512 tokens
- Technical docs: ~1,024 tokens
- Legal/contracts: ~2,048 tokens
- Code: at function/class boundaries (AST-aware)

---

## Embedding Models (2026)

**MTEB leaderboard is directional only — always test on your own data.**

| Model | Dimensions | Price/1M tokens | Notes |
|---|---|---|---|
| **text-embedding-3-large** | 3,072 (Matryoshka) | ~$0.13 | Safe OpenAI default; truncatable to 256/512/1024 |
| **text-embedding-3-small** | 1,536 (Matryoshka) | ~$0.02 | 5× cheaper; adequate for most workloads |
| **Cohere embed-v4** | 1,024 | ~$0.01 | Multilingual 100+ languages |
| **Voyage voyage-3-large / voyage-4** | — | — | Domain leader for code/legal/medical; +4–6 MTEB points on domain retrieval |
| **BGE-M3** | — | Self-hosted | Open; self-hostable |

**Matryoshka Representation Learning**: truncate dimensions (3,072→256/512/1,024) without retraining for graceful quality/storage trade-offs. Now standard.

**Asymmetric search**: E5-instruct task prefixes align query vs document intent — important for asymmetric query/passage retrieval.

---

## Vector Databases — Honest Selection Guide

### ANN Index Types
- **HNSW**: graph, in-memory, top performance/recall, high RAM; tune `M`, `efConstruction`, `efSearch`
- **IVF / IVF+PQ**: partitioned + compressed; large-scale (billions with limited RAM)
- **DiskANN/Vamana**: disk-resident for billions of vectors; powers Azure Cosmos DB and Azure SQL

### Database Selection (2026)

| DB | Strength | Weakness |
|---|---|---|
| **Pinecone** | Zero-ops managed | Can't tune HNSW parameters |
| **Qdrant** (Rust) | Best-in-class filtered search, quantization | Self-host/cloud — ops burden if self-hosted |
| **Weaviate** | Best native hybrid search (BlockMax WAND GA 2025) | |
| **Milvus/Zilliz** | Billion-scale | Heavy ops (Kafka/MinIO/etcd) |
| **Chroma** | Prototyping | No native hybrid search |
| **LanceDB** | Embedded + columnar; native hybrid | |
| **pgvector** | Good enough under ~10M vectors if already on Postgres | Query planner can choose seqscan on filtered queries; degrades past 10M |

**pgvector production note**: HNSW since 0.5.0 matches dedicated DBs at 1M scale. Use `SET enable_seqscan=off` or pgvectorscale's StreamingDiskANN for filtered queries. At 50M vectors: Qdrant ~41 QPS vs pgvectorscale ~471 QPS at 99% recall.

### Azure-Native Vector Stores
- **Azure AI Search**: vector + hybrid (BM25+vector via RRF) + semantic reranker + integrated vectorization + scalar/binary quantization — the Azure-native answer
- **Azure Cosmos DB (NoSQL) with DiskANN** (GA): <20ms latency over 10M vectors; ~43× lower query cost vs Pinecone and ~12× vs Zilliz serverless; co-locates vectors with operational data
- **Azure SQL**: native VECTOR type + VECTOR_DISTANCE
- **Azure Cache for Redis Enterprise**: low-latency caching + semantic caching

---

## Retrieval Strategies

### Sparse vs Dense vs Hybrid
- **Sparse (BM25/TF-IDF/SPLADE)**: wins for exact keywords, product codes, acronyms, statute numbers
- **Dense bi-encoder**: handles semantics, synonyms, paraphrase
- **Hybrid almost always beats either alone**: fuse with Reciprocal Rank Fusion (RRF) — Azure AI Search's default

### Query Processing Techniques
| Technique | What it does |
|---|---|
| **HyDE** | Generate a hypothetical answer, embed it as the query |
| **Step-back prompting** | Rephrase to a more general question |
| **Multi-query** | Generate multiple phrasings; union results |
| **Decomposition** | Break complex question into sub-questions; synthesize |
| **Routing** | Classify query type → pick retrieval strategy |

---

## Reranking

**Two-stage pipeline**: retrieve top 50–200 (bi-encoder) → rerank to top 3–10 (cross-encoder).

**Expected gains**: independent benchmarks (Voyage AI) report +13.89% for Cohere rerank-2 and +11.86% for rerank-2-lite across 93 datasets on top of OpenAI text-embedding-3-large. Cohere's own materials cite 20–35%; expect 10–35% depending on baseline and domain.

| Reranker | Notes |
|---|---|
| **Cohere Rerank 3.5 / 4.0** | Best-in-class managed; multilingual 100+ languages; underperforms on identifier-heavy queries (function names, statute numbers) |
| **BGE-Reranker-v2-m3** | Self-hosted |
| **Jina Reranker v2** | 8K context |
| **FlashRank** | CPU; lightweight |
| **ColBERT/RAGatouille** | Late interaction; good when exact term matching matters |
| **Azure AI Search semantic ranker** | Microsoft-trained cross-encoder (Bing corpus); rescores top 50; returns `@search.rerankerScore` 0–4; score below ~1.0 signals weak match |

**Azure semantic ranker**: passes up to 2,048 tokens per doc (raised from 256 in Nov 2024). Order fields in semantic configuration by priority — long fields are trimmed.

---

## Context Assembly & Generation

**Fight "lost in the middle"**: place best material at the beginning or end of the context window.

**System prompt structure for RAG:**
```
[role/instruction]
[document format description]
[citation rules]
[anti-hallucination instruction: "Answer only from the provided context; if the answer is not in the documents, say you don't know."]
```

- Deduplicate and stitch adjacent chunks before passing to LLM
- Handle no-answer cases explicitly with a fallback instruction
- Stream responses for UX; prompt for clarifying questions when context is insufficient

---

## Advanced RAG Patterns

### GraphRAG (Microsoft, open-sourced July 2, 2024)
**From:** "From Local to Global: A Graph RAG Approach to Query-Focused Summarization" (arXiv 2404.16130)

**Indexing:** LLM extracts entities/relationships per chunk → builds graph → partitions with Leiden algorithm hierarchically → generates community summaries bottom-up.

**Query modes:**
- **Global search**: map-reduce over community summaries; for whole-dataset/thematic questions ("top 5 themes?")
- **Local search**: entity-anchored retrieval; for specific-entity questions; faster and cheaper than global
- **DRIFT search** (late 2024): combines global+local — HyDE-based Primer phase + local refinement; produces hierarchical Q&A output

**Paper results vs vector RAG**: comprehensiveness win 72–83%, diversity 62–82%. Vector RAG scored higher only on Directness (expected — passage retriever is more targeted for local questions).

**Cost cliff**: original GraphRAG indexing was prohibitively expensive (one estimate: $33K for a 5GB legal case). Use **LazyGraphRAG** (Microsoft Research, Nov 25, 2024):
- Defers LLM use to query time; uses NLP-based extraction
- ~0.1% of full GraphRAG indexing cost (~1,000× reduction)
- Matches full GraphRAG global-search quality at >700× lower query cost
- Best for one-off queries, exploratory analysis, streaming data

**When to use GraphRAG**: multi-hop or thematic queries across large, relatively static corpus. Start with LazyGraphRAG, not full GraphRAG, unless you have high-utilization static corpus justifying expensive indexing. Never deploy on high-update or simple-factoid corpus.

### CRAG, Self-RAG, Adaptive RAG
- **CRAG** (Corrective RAG): grader LLM scores retrieved docs; if irrelevant, fall back to web search (LangGraph conditional routing)
- **Self-RAG**: model decides when to retrieve and critiques its own output (via prompting in practice)
- **Adaptive RAG**: classify query complexity → route (no-retrieval for simple factoids, single retrieval for medium, multi-step for complex)

---

## RAG Evaluation

**Build a 50–200 QA golden dataset before launch (human-curated + LLM-synthesized then filtered). Run it on every change.**

### RAGAS Metrics (largely reference-free, LLM-as-judge)
| Metric | Definition |
|---|---|
| **Faithfulness** | Claims in answer supported by context ÷ total claims in answer |
| **Answer Relevancy** | Mean cosine similarity between the question and questions reverse-generated from the answer |
| **Context Precision** | Average precision@k over retrieved chunks (are relevant chunks ranked high?) |
| **Context Recall** | Reference claims supported by retrieved context ÷ total reference claims — **only metric needing ground truth** |

### Retrieval Metrics
- Hit Rate@k, MRR, NDCG, Precision@k

### Azure AI Foundry Evaluators (GA)
Groundedness, Groundedness Pro (Content-Safety-model-based), Relevance, Retrieval, Document Retrieval, Response Completeness, Coherence, Fluency. Continuous evaluation on sampled production traffic surfaced through Azure Monitor.

**Other frameworks**: DeepEval (pytest-style), TruLens (RAG triad: groundedness/answer-relevance/context-relevance), Arize Phoenix.

---

## Azure AI Search — Deep Dive

### Tiers
Free (3 indexes, 50MB) → Basic → Standard S1/S2/S3 → Storage-Optimized L1/L2. New Serverless (Compute Unit-based) model rolling out.

### Vector Configuration
- HNSW params: `m`, `efConstruction`, `efSearch`, metric (cosine/euclidean/dotProduct)
- Exhaustive KNN for small indexes
- Scalar/binary quantization with rescoring/oversampling for storage savings

### Hybrid + Semantic Setup
```
vectorSearch + text search → RRF fusion → queryType: semantic → semantic reranker
```
- `vectorFilterMode`: preFilter (accurate, slower) or postFilter (fast, can under-return)
- `queryType: semantic` + `semanticConfiguration` + optional `answers`/`captions`

### Integrated Vectorization
Drives auto-embedding via indexer skillsets calling Azure OpenAI. A query-time **vectorizer** removes app-side embedding code. **Index projections** create chunk + parent indexes from one document. **Index aliases** enable blue-green zero-downtime reindexing.

### Security
- Managed identity (Search → Azure OpenAI keyless)
- Private endpoints, CMK, RBAC (Search Service Contributor, Search Index Data Contributor/Reader)
- **Document-level access control** via `search.in(group_ids,...)` security trimming

### Foundry IQ (Successor to "On Your Data")
- Reusable, topic-centric knowledge base with automatic indexing/vectorization/enrichment
- Sources: Blob, OneLake, SharePoint, existing indexes, web (via Grounding with Bing)
- Document-level ACL + Purview sensitivity labels
- Microsoft reports +36% improvement in RAG answer quality (vs brute-force searching all sources)
- Exposes MCP endpoint (`/knowledgebases/<kb>/mcp?api-version=2025-11-01-preview`)

### "On Your Data" Deprecation
Microsoft stopped onboarding new models. Only supports GPT-4o (2024-05-13, 2024-08-06, 2024-11-20) and GPT-4o-mini (2024-07-18). Migration path: **Foundry Agent Service with Foundry IQ** (or custom Azure AI Search RAG pipeline — only managed On Your Data workloads need to migrate).

---

## AI Agent Fundamentals

**Agent = LLM + tools + memory + planning loop**

**Base pattern**: ReAct (Yao et al., 2022) — interleaved Thought/Action/Observation. Foundation of modern tool-using agents implemented via function calling.

**When to use agents vs deterministic workflows:**
- Known steps, no dynamic planning → deterministic workflow
- Dynamic planning required → agent

**Top failure modes**: tool-call errors, infinite loops, context loss, hallucinated tool calls, over-planning.

### Tool Calling Best Practices
- Validate inputs with Pydantic
- Use `parallel_tool_calls` for independent calls
- Performance degrades above ~10 tools — use progressive/intent-based tool exposure
- Cache tool definitions in the system prefix (stable prefix for caching)

### Memory Tiers
| Tier | Storage | Use |
|---|---|---|
| In-context (working) | Token window | Current task context |
| Episodic | Vector DB (Cosmos DB, Redis, AI Search) | Past conversations |
| Semantic | Long-term facts store | Knowledge base |
| Procedural | Fine-tuning / system prompt | Action patterns |

**Production memory (Azure):** Cosmos DB for durable history, Redis for fast recent, AI Search for semantic retrieval. Foundry Agent Service Memory (public preview) for automatic extraction/consolidation.

---

## Agent Frameworks

### LangGraph (Production Default)
- Stateful graph orchestration: nodes/edges/typed state
- Checkpointing: MemorySaver / AsyncPostgresSaver / RedisSaver — **use Postgres/Redis, not SQLite, for distributed**
- `interrupt()` for human-in-the-loop
- Streaming, subgraphs, time-travel debugging
- **Best for**: regulated/auditable, conditional, stateful multi-turn, HITL workflows

### LlamaIndex
- Data-heavy RAG: loaders, node parsers (Simple/Sentence/Markdown/Hierarchical)
- Index types: Vector/Summary/DocumentSummary/KnowledgeGraph/SQL
- RouterQueryEngine, SubQuestionQueryEngine, event-driven Workflows
- `AzureAISearchVectorStore` with hybrid + semantic reranker
- LlamaHub: 100+ integrations

### LangChain
- Large ecosystem; criticized for over-abstraction and version churn
- LCEL composition; 100+ loaders; all major splitters; vector store integrations including `AzureSearch`
- Use for prototyping; prefer LangGraph for production agents

### Other Frameworks
- **CrewAI**: fastest role-based multi-agent prototyping
- **Pydantic AI**: typed, Pythonic, minimal boilerplate, Logfire integration
- **Smolagents** (HuggingFace): minimal CodeAgent (writes/executes Python — **needs sandboxing**)

### Microsoft Agent Framework 1.0 (GA April 3, 2026)
- Open-source successor to Semantic Kernel + AutoGen (both now in maintenance mode)
- Built on Microsoft.Extensions.AI; .NET + Python parity
- Stable 1.0 surface: single-agent abstraction + connectors, middleware, agent memory/context providers, graph-based workflows with checkpointing
- Orchestration patterns: sequential/concurrent/handoff/group-chat/Magentic
- Native MCP + A2A; `UseOpenTelemetry()` built in; YAML declarative agents

### Azure AI Foundry Agent Service (GA March 16, 2026)
- Architecture: Threads (context), Messages (turns), Runs (execution), Run Steps (tool calls/generation)
- Built-in tools: file_search, code_interpreter, azure_ai_search/Foundry IQ, function tools, Logic Apps connectors (1,400+), MCP tools, A2A
- **Connected Agents** = agent-calls-agent; **Foundry Workflows** = visual/YAML multi-agent
- Private networking: no public egress, VNet/subnet injection
- GA REST API: `/openai/v1/`

**Managed (Foundry) vs self-built (LangGraph):**
- Managed: no infra, SOC2, built-in storage/memory, faster to production
- Self-built: full control, portability, custom checkpointing, no lock-in

---

## MCP (Model Context Protocol)

**Standardizes LLM↔tool/data connections.** Anthropic Nov 2024; donated to Linux Foundation (Agentic AI Foundation) Dec 9, 2025; adopted by OpenAI, Google, Microsoft, Amazon. Over 97M monthly SDK downloads, 10,000 active servers at donation.

**Architecture**: Host/client/server roles. Transports: stdio (local), HTTP+SSE/streamable HTTP (remote), WebSocket.

**Primitives**: Resources (readable data), Tools (callable functions), Prompts (templates), Sampling (server requests completion). OAuth 2.0 for remote servers.

**Build with**: FastMCP (Python decorators) or official SDKs.

**Azure MCP servers**: Azure DevOps, ARM, Bing, Azure SQL, Blob, Monitor. Deploy custom servers on Azure Container Apps or Azure Functions (`/runtime/webhooks/mcp`).

**A2A** (Google, 2025): complementary agent-to-agent protocol.

**Security risks**: prompt injection via malicious servers, confused-deputy attacks. Restrict capabilities, sandbox, validate.

---

## Multi-Agent Systems

**Justified by**: specialization, parallelism, redundancy, context-window scale.
**Costs**: coordination overhead, non-determinism, debugging difficulty, cost multiplication.

### Patterns
- Orchestrator-worker, supervisor (LangGraph), hierarchical
- Group-chat/round-table (AutoGen→MAF)
- Sequential chaining, parallel fan-out, debate, handoff, swarm

### Production Requirements
- Shared state vs message passing; checkpoint and ensure idempotency for retries
- Trust boundaries between agents; per-agent budget caps
- Validate inter-agent output before acting on it

---

## Agentic System Design & Security

### Mandatory Production Controls
- Hard `max_iterations` limit
- Token and time budgets per run
- Explicit completion criteria
- Retry limits per tool
- Fallback/graceful degradation
- Human-in-the-loop via `interrupt()` / Foundry approvals

**The "AI cost snowball"** — runaway agents without limits is a documented incident class; hard limits are mandatory, not polish.

### Sandboxed Code Execution
**Azure Container Apps Dynamic Sessions** (GA): Hyper-V-isolated, per-session, millisecond startup. Python/Node/shell + custom container. Never run LLM-generated code in-process.

### Observability
- Trace every tool call, LLM call, decision, latency, and cost via OpenTelemetry
- Tools: LangSmith, Langfuse (open-source, Azure-deployable), Arize Phoenix, W&B Weave, Foundry Traces
- The APIM AI gateway pattern fronts agents with semantic caching, rate limiting, monitoring, and MCP tool governance

### Security Architecture
- Managed identity everywhere, private endpoints, CMK, VNet, regional data residency
- PII scrubbing before indexing
- Document-level ACL trimming
- Diagnostic/audit logging to Log Analytics
- Foundry XPIA/cross-prompt injection filters for indirect injection from retrieved content
- Defend against direct injection (user input) and indirect injection (poisoned retrieved docs)

---

## Emerging Patterns

### Voice RAG
Azure OpenAI Realtime API (GA Aug 2025): WebRTC/WebSocket/SIP, ~250–500ms end-to-end. Pattern: Realtime API → function call → AI Search retrieval → grounded spoken response.

### Streaming RAG
Event Hubs → Stream Analytics → AI Search push API; Cosmos DB change feed → embedding pipeline.

### Text-to-SQL
Beats RAG for exact aggregations/joins/filters. Pattern: schema injection → NL→SQL→execute→synthesize. Evaluate on Spider/BIRD benchmarks.

---

## Anti-Patterns to Avoid

1. **Pure vector search** with no keyword/hybrid component (misses exact terms, codes, acronyms)
2. **Re-embedding unchanged documents** (deterministic; cache by content hash)
3. **Mismatched query/document embedding models** (use the same model or an asymmetric pair)
4. **Fixed-size chunking** that splits tables/clauses mid-unit (neutralizes reranker gains)
5. **Exposing >10 tools to a single agent** without intent-based gating
6. **Running LLM-generated code in-process** instead of an isolated sandbox
7. **Deploying full GraphRAG** on high-update or simple-factoid corpus — use LazyGraphRAG
8. **MTEB leaderboard as ground truth** instead of testing on your own data
9. **Shipping without a golden eval set** — never deploy RAG/agent changes without measuring against a baseline

---

## Staged Implementation Roadmap

**Stage 1 — Baseline (weeks 1–2):** Stand up hybrid search + semantic reranking. Azure: AI Search Standard + integrated vectorization with text-embedding-3-large + `queryType: semantic`. Custom: Qdrant or pgvector (<10M vectors) + Cohere Rerank 3.5 or BGE-reranker. Build the 50–200 QA golden set now.

**Stage 2 — Chunking & context (weeks 3–4):** Add parent-child chunking (child 100–256 tokens, parent 512–2,048). Switch parsers to LlamaParse/Docling/Azure Document Intelligence Layout (Markdown output) if table/layout fidelity is failing. Add Contextual Retrieval if retrieval misses persist.

**Stage 3 — Advanced retrieval (month 2):** Add query decomposition/multi-query, or adopt Azure AI Search agentic retrieval / Foundry IQ for multi-intent queries. GraphRAG only if queries are genuinely multi-hop/thematic on large static corpus — start with LazyGraphRAG.

**Stage 4 — Agents (months 2–3):** If dynamic tool use/planning is needed: Foundry Agent Service + Foundry IQ for fastest enterprise time-to-production; LangGraph for full control; Microsoft Agent Framework 1.0 for open-source Azure-aligned path. Enforce termination contracts, sandbox code execution, trace everything.

**Migration deadlines:** Migrate "On Your Data" workloads to Foundry IQ before GPT-4o 2024-11-20 retires (2026-10-01). Migrate AzureML SDK v1 before June 30, 2026 end-of-support.

---
name: ai-ml-landscape
description: "Comprehensive practitioner reference for the 2025–2026 AI/ML landscape covering frontier model selection and routing, open-weight vs hosted API trade-offs, reasoning models and test-time compute, RAG and agent production patterns, classical ML for tabular data, deep learning foundations (transformers, attention, MoE, SSMs), LLM training and post-training (DPO/GRPO/LoRA/QLoRA), inference serving (vLLM/SGLang), evaluation benchmark skepticism, safety/alignment, EU AI Act governance, and hardware selection. Use when advising on model selection, AI architecture decisions, LLM deployment, fine-tuning strategy, benchmark interpretation, or AI governance compliance."
---

# AI & Machine Learning Landscape — Practitioner Reference (2026)

## The Three-Layer Structure of AI in 2026

1. **Frontier model race** — fast-moving, narrow quality gaps between top models (~2.7% lead at the top as of March 2026)
2. **Production engineering stack** — maturing: vLLM/SGLang serving, MCP-standardized agents, contextual-retrieval RAG
3. **Classical ML core** — stable: gradient boosting still wins most tabular problems

**Inference cost collapse**: >280-fold reduction from $20.00 to $0.07 per million tokens between Nov 2022 and Oct 2024 (GPT-3.5-equivalent quality, per Stanford HAI). This makes capability cheap and **engineering discipline** the binding constraint.

---

## Frontier Model Landscape (Mid-2026)

No single model dominates. The top model leads by only ~2.7% (Stanford HAI AI Index, March 2026). The leading closed-weight model's edge over the top open-weight model on Chatbot Arena narrowed from 8.04% (Jan 2024) to 1.70% (Feb 2025).

**Key practitioner principle:** Build behind an abstraction layer (LiteLLM/OpenRouter) to avoid lock-in. Model names and rankings shift weekly.

---

## Hosted APIs vs Open Weights — Decision Rule

| Factor | Hosted API | Open Weights |
|---|---|---|
| Peak capability, zero ops | ✓ | |
| Privacy, air-gap, data residency | | ✓ |
| Fine-tuning control | | ✓ |
| Predictable cost at sustained high QPS | | ✓ |
| Fastest to start | ✓ | |

**Open-weight options**: DeepSeek-V4 (MIT-licensed, 1M context, 1.6T/49B active MoE), Qwen3, Meta Llama 4, Mistral, IBM Granite 4.0.

**Threshold to self-host**: sustained high QPS where API spend exceeds fully-loaded GPU fleet cost, or a hard data-residency requirement.

---

## Model Selection Strategy (Staged)

1. **Start with hosted frontier behind an abstraction layer.** Default to strong mid-tier (Claude Sonnet-class, GPT-4.1-mini-class, Gemini Flash-class); escalate to top-tier only for hard tasks.

2. **Implement model routing** once volume justifies it. A cheap classifier sends easy queries to small/cheap models with confidence-gated escalation. RouteLLM (UC Berkeley/Anyscale/Canva, ICLR 2025) achieved 95% of GPT-4 quality using only ~26% of GPT-4 calls, with up to 85% cost reduction on MT-Bench.

3. **Move to open weights self-hosted on vLLM/SGLang** when privacy, air-gap, predictable cost at scale, or fine-tuning control becomes the binding constraint.

---

## Build Pattern for LLM Applications

**Prompting → RAG → Fine-tuning (in that order)**

- **Few-shot prompting** for behavioral change
- **RAG** for dynamic/factual/auditable knowledge — use hybrid retrieval (BM25 + dense) + reranking + contextual retrieval
- **Fine-tune** (LoRA/QLoRA) only for consistent format/style/jargon or cost reduction
- **GRPO/DPO** only when you have verifiable rewards or preference data and a reasoning/behavior target

---

## Reasoning Models & Test-Time Compute

The o1/o3/R1 paradigm: spending more inference compute on chain-of-thought "thinking tokens" is a complementary scaling axis to parameters/data.

**Process Reward Models (PRMs)**: score intermediate reasoning steps; outperform outcome-only rewards on math (GenPRM: 1.5B model beats GPT-4o on ProcessBench via test-time scaling).

**GRPO** (Group Relative Policy Optimization): critic-free, group-relative RL with verifiable rewards (RLVR). Dominant post-training method for reasoning. Spawned variants DAPO, Dr. GRPO, GSPO, GMPO.

**When reasoning tokens are worth it**: genuine multi-step reasoning (math, code generation, legal analysis). Wasteful when wired into pipelines expecting short outputs.

---

## Classical ML — Tabular Data

Gradient-boosted trees remain state-of-the-art on most tabular problems. Deep learning requires more tuning and rarely wins on tabular without genuine unstructured signal.

**2025 challenger**: TabPFN (transformer tabular foundation model, published in Nature) beats GBDTs on small/medium single tables. XGBoost still wins on large tables.

**Practitioner default**: GBDT-first (LightGBM → CatBoost → XGBoost depending on data characteristics). Only reach for deep learning with genuine unstructured signal or very large data.

---

## Mathematical Foundations

**Linear algebra**: tensors are batched multidimensional arrays; matmul/dot products implement every linear layer and attention score; SVD underpins PCA and low-rank adaptation (LoRA literally learns low-rank ΔW). Norms drive regularization (L1 sparsity/Lasso, L2 weight decay/Ridge) and gradient clipping.

**Probability**: KL/JS/Wasserstein divergences anchor VAEs, GANs, and distribution matching. Cross-entropy is the default classification loss (= MLE under a categorical model). Bias–variance is operationalized by regularization and ensembling.

**Optimization**: backprop = reverse-mode autodiff applying chain rule over the computational graph. Deep loss landscapes are non-convex but navigable — saddle points (not bad local minima) dominate, and SGD noise helps escape them. **AdamW** is the safe default; cosine annealing with linear warmup is the standard LR schedule. First-order methods dominate because Hessian-based methods don't scale to billions of parameters.

---

## Classical ML Reference

### Regression & Classification
- OLS with Ridge/Lasso/ElasticNet for regularized selection
- GLMs (logistic, Poisson, negative binomial) for non-Gaussian targets
- Gaussian Process Regression for small-data + calibrated uncertainty
- Logistic regression: strong, interpretable baseline — always try it first
- SVMs (kernel trick, RBF): still win on small high-dimensional data

### Calibration
**Calibration matters in production.** Temperature scaling (post-hoc, single-parameter) for neural nets; isotonic/Platt for others. Brier score and reliability diagrams for diagnosis.

### Unsupervised & Anomaly Detection
- Clustering: k-means(++)/DBSCAN/HDBSCAN/GMM/spectral
- Dimensionality reduction: PCA/UMAP/t-SNE (UMAP preferred for preserving global structure and speed)
- Anomaly detection: isolation forest/LOF/autoencoders

### Model Selection
- Stratified/group/time-series CV to prevent leakage
- Metric choice: AUC-PR for imbalanced, MCC as balanced single number, log-loss for probabilistic
- Optuna (TPE/Bayesian) + Hyperband/ASHA for hyperparameter tuning
- **Leakage is the silent killer**: target leakage, train/test contamination via preprocessing, and temporal leakage cause the most "great offline, broken online" failures

---

## Deep Learning Foundations

### Activations & Normalization
- **ReLU**: default for CNNs
- **GELU/SiLU(Swish)**: dominate transformers (smooth, work well with normalization)
- **BatchNorm**: CNNs
- **LayerNorm/RMSNorm**: transformers (RMSNorm is cheaper, now standard in LLMs)
- **Pre-norm** (LayerNorm before sublayer): dominates modern transformers for stability at depth

### Initialization & Precision
- He/Kaiming for ReLU nets; Xavier for tanh; orthogonal for RNNs
- **BF16**: LLM-training default (wider dynamic range than FP16, no loss scaling)
- **FP8**: production on Hopper/Blackwell (DeepSeek-V3 trained in FP8)
- Mixed precision memory tools: gradient checkpointing, gradient accumulation, activation recomputation

### Residual Connections
Enable very deep networks by giving gradients an identity path.

---

## The Transformer & Attention

**Architecture types:**
- Encoder-only (BERT): classification/embedding
- Encoder-decoder (T5): seq2seq tasks
- Decoder-only (GPT): dominates generative LLMs

**Attention components:**
- Scaled dot-product attention over Q,K,V
- Multi-head attention
- **RoPE** (rotary positional encoding): now standard; YaRN/position interpolation extends context
- **FlashAttention (v1→v3)**: IO-aware, exact (not approximate), tiling attention in SRAM — mitigates O(n²) attention cost
- **KV cache**: makes autoregressive decoding tractable
- FFN uses **SwiGLU**

**Mixture of Experts (MoE)**: dominant frontier-scaling lever. Sparse gating + routing + load balancing. DeepSeek-V3 activates 37B of 671B params per token. Mixtral, DeepSeek-MoE, Qwen3-MoE all use this architecture.

---

## LLM Training & Post-Training

### Tokenization
- BPE/WordPiece/SentencePiece/tiktoken; larger vocabulary = shorter sequences but larger embedding tables
- **Chinchilla scaling** (~20:1 tokens:params) guided compute-optimal training; inference-cost economics now push toward "overtrain a smaller model"

### Pre-training Infrastructure
- Curated/deduplicated/quality-filtered corpora + heavy synthetic data (Phi "textbooks" thesis)
- Tensor/pipeline/data parallelism; ZeRO/DeepSpeed; FSDP; Megatron-LM

### Alignment Pipeline
1. **SFT** (Supervised Fine-Tuning): high-quality instruction examples; "LIMA / Less is More" — a few thousand high-quality examples often beat massive noisy sets
2. **DPO** (Direct Preference Optimization): reference-model based, no explicit reward model; simple default
3. **GRPO**: critic-free, group-relative, RLVR; dominates reasoning post-training

### PEFT (Parameter-Efficient Fine-Tuning)
- **LoRA**: low-rank adapters; workhorses of production fine-tuning
- **QLoRA**: 4-bit NF4 base + LoRA; enables fine-tuning large models on consumer hardware
- DoRA/VeRA: refinements of LoRA

---

## LLM Inference Optimization

### Quantization Formats
| Format | Use case | Notes |
|---|---|---|
| **AWQ** | Best throughput in vLLM; INT4 weight-only | <2% degradation on most tasks; noticeable on math/code/reasoning |
| **GPTQ** | Best throughput in vLLM | Similar trade-offs to AWQ |
| **GGUF** | llama.cpp/Ollama; CPU+GPU offload | Q4_K_M–Q6_K near-BF16 quality |
| **FP8 W8A8** | Near-lossless on Hopper/Blackwell | Production preferred when hardware supports it |

**Rule**: avoid INT4 for math/code/reasoning-critical paths.

### Serving Engines
| Engine | Strength |
|---|---|
| **vLLM** | PagedAttention; broadest model/hardware support; V1 architecture |
| **SGLang** | RadixAttention; ~29% higher H100 throughput; up to 6.4× on prefix-heavy RAG/chat |
| **TensorRT-LLM** | Maximum NVIDIA throughput |
| **Ollama/llama.cpp** | Local deployment; CPU offload |

**Continuous batching** + **disaggregated prefill/decode** (separate compute-bound prefill and bandwidth-bound decode pools) are the 2026 production patterns.

**Speculative decoding** (draft+verify, Medusa/EAGLE): 2–4× latency wins losslessly.

---

## Evaluation & Benchmark Skepticism

**The contamination problem is severe.** A single model can swing 17–35 points between SWE-bench Verified and the standardized-scaffold Pro leaderboard — scaffold and harness move scores more than model swaps.

**Key benchmarks:**
- MMLU(-Pro), GPQA Diamond: knowledge/reasoning
- HumanEval/MBPP, SWE-bench Verified/Pro: coding
- GSM8K/MATH: math reasoning
- MMMU: multimodal
- LiveBench/LiveCodeBench: contamination-resistant
- Chatbot Arena Elo: human preference
- RULER/HELMET: long-context
- TruthfulQA/FActScore: factuality
- RAGAS: RAG evaluation

**Decision rule for benchmarks:**
- Never select on a single leaderboard number
- Build a 50–200 case internal eval of your real workflows
- Weight SWE-bench Pro (standardized scaffold) over Verified for coding
- When a benchmark and your production results diverge sharply, trust contamination/scaffold effects over the leaderboard
- LLM-as-judge is widespread but carries position/verbosity/self-preference biases

---

## RAG Fundamentals (Quick Reference)

**Production default** (2026): hybrid search (BM25 + dense via RRF) + cross-encoder reranking + parent-child chunking.

**Anthropic Contextual Retrieval** (Sept 2024): prepend LLM-generated chunk summary before embedding/indexing.
- Contextual Embeddings alone: 35% reduction in retrieval failure (5.7%→3.7%)
- + Contextual BM25: 49% reduction (→2.9%)
- + Reranking: 67% reduction (→1.9%)

**RAG vs fine-tuning vs long-context:**
- RAG: dynamic/proprietary knowledge with citations
- Fine-tuning: changing behavior/format/tone/domain style
- Long-context: single-document deep reasoning where doc fits
- They combine

---

## Agent Stack & MCP

**Model Context Protocol (MCP)**: Anthropic, Nov 2024; donated to Linux Foundation Dec 2025; adopted by OpenAI, Google, Microsoft, Amazon. "USB-C for AI tools." Over 97M monthly SDK downloads and 10,000 active servers at donation time.

**Production failure modes**: runaway loops, unbounded retries, silent context truncation. Iteration limits, cost ceilings, and termination conditions are mandatory, not polish.

**Single-agent suffices for ~80% of cases.** Multi-agent adds cost and non-determinism.

**Framework selection:**
- **LangGraph**: production default for regulated/auditable workflows; graph state machines with checkpointing
- **CrewAI**: fastest role-based multi-agent prototyping
- **Pydantic AI**: typed, minimal boilerplate

---

## Generative AI Across Modalities

### Image
- GANs and VAEs gave way to **diffusion** (DDPM→DDIM→Latent Diffusion = Stable Diffusion)
- Now **flow matching / rectified flow** (backbone of SD3, FLUX)
- Classifier-free guidance, ControlNet (pose/depth/edge conditioning), LoRA/DreamBooth personalization are standard
- FLUX (Black Forest Labs): open-weight image generation leader in 2026

### Video
- Standardized on **diffusion transformers (DiT) over spacetime patches** (Sora, Veo, Kling, Seedance, WAN, Hunyuan)
- By early 2026: 8–25s clips at native resolution with synchronized audio and plausible physics
- Weaknesses: long-range temporal coherence and quadratic attention cost

### Audio
- TTS: Tacotron→FastSpeech→VITS→XTTS/F5-TTS/Kokoro; ElevenLabs leads commercial quality
- ASR: Whisper dominates
- Discrete audio tokens: EnCodec/DAC

### Multimodal/VLMs
- Vision encoders trend SigLIP over CLIP, with tile-based high-res
- Open options: LLaVA, Qwen-VL, InternVL, Molmo, Pixtral

---

## MLOps & Infrastructure

### Hardware
| Chip | Key spec | Notes |
|---|---|---|
| NVIDIA H100/H200 (Hopper) | 80GB/141GB HBM3 | Current production standard |
| B200/GB200 (Blackwell) | 192GB HBM3e at 8TB/s | ~2.5–3× H100 training; GB200 NVL72 trained Llama 3.1 405B in ~10 min on 5,120 GPUs (MLPerf) |
| AMD MI300X/MI325X/MI355X | 192–288GB HBM3 | More memory; CUDA/ROCm moat keeps NVIDIA at ~80%+ share |
| Google TPU v5/v6e | — | JAX/XLA affinity |
| Groq LPU | — | Deterministic high-throughput inference |

### Frameworks
- **PyTorch**: dominant (eager + torch.compile/Inductor)
- **JAX**: TPU/research
- **Hugging Face stack**: Transformers, Diffusers, PEFT, TRL, Datasets, Accelerate — the default
- **Experiment tracking**: W&B (research favorite), MLflow (open, ubiquitous)

### Observability & Monitoring
- **LLM serving/observability**: LangSmith, Langfuse, Arize Phoenix, Helicone, Braintrust, W&B Weave
- **Drift/monitoring**: Evidently, NannyML, Arize, WhyLabs, Fiddler; PSI/KS tests; distinguish covariate/label/concept shift
- **Explainability**: SHAP/LIME/Integrated Gradients (caution: attention weights ≠ explanations)

---

## Advanced Architectures

### State-Space Models (SSMs)
- **Mamba** (selective state spaces, Mamba-2): linear complexity, ~5× throughput
- **Critical weakness**: pure SSMs fail at retrieval/in-context copying — removing attention layers drops retrieval accuracy to near-zero
- **Hybrids win in production**: Jamba (AI21), Zamba2, NVIDIA Nemotron-H, IBM Granite 4.0 — small fraction of attention layers interleaved with Mamba blocks

### Long Context
- 1M+ token windows are table stakes across flagships
- "Lost in the middle" and needle-in-haystack failures persist
- RAG vs long-context is a cost/freshness/auditability decision, not a pure capability one

### Reasoning Research
- Test-time compute scaling via PRMs
- MCTS for reasoning
- Self-consistency voting
- Formal-verification systems (AlphaProof/AlphaGeometry 2)

---

## Safety, Alignment & Governance

### Alignment Approaches
- **Constitutional AI / RLAIF** (Anthropic): AI self-critique for alignment
- **Mechanistic interpretability**: sparse autoencoders decompose superposed/polysemantic activations; circuit tracing with cross-layer transcoders lets researchers trace and intervene on causal pathways (Anthropic, open-sourced May 2025; MIT Tech Review 2026 Breakthrough Technology)
- Outer alignment (specification) vs inner alignment (goal generalization)
- Reward hacking and Goodhart's Law: recurring failure modes

### EU AI Act Timeline (Critical Deadlines)
| Date | What takes effect |
|---|---|
| Aug 1, 2024 | In force |
| Feb 2, 2025 | Prohibited practices + AI literacy obligations |
| Aug 2, 2025 | GPAI (General Purpose AI) obligations |
| **Aug 2, 2026** | **GPAI enforcement powers and fines; high-risk system obligations** |
| Aug 2, 2027 | Legacy-GPAI compliance deadline |

Fines: up to €35M or 7% of global turnover (prohibited practices) — higher ceiling than GDPR. The voluntary GPAI Code of Practice offers a "presumption of conformity" safe harbor.

**Action**: If you touch EU users, classify your system now against the AI Act risk tiers. If you fine-tune a GPAI model substantially, you may become a "provider" with heavier obligations.

### Fairness
Demographic parity vs equalized odds vs individual fairness are mutually incompatible (impossibility theorems). Tools: Fairlearn, AI Fairness 360.

### Privacy
Differential privacy, federated learning, and defenses against membership-inference/model-inversion/poisoning attacks.

### US Framework
NIST AI RMF (Govern/Map/Measure/Manage) is the US reference standard.

---

## Durable Principles (Outlast Model Names)

1. **Baseline-first**: always establish a simple baseline before reaching for complex architectures
2. **Data quality over architecture**: garbage in, garbage out — no model overcomes bad data
3. **Route, don't over-provision**: tiered model fleets beat one expensive frontier model
4. **RAG before fine-tune**: try prompting and retrieval before committing to training
5. **Guardrails and observability before launch**: build I/O filtering, tracing, and cost monitoring into the initial design
6. **Benchmark skepticism**: build internal evals on your real workflows; never select on a single leaderboard number
7. **Open vs closed is a cost/privacy/capability trade-off, not an ideology**: evaluate quarterly as quality gaps narrow

---
name: ml-reference
description: "Use when reviewing ML work for known anti-patterns (leakage, test-set tuning, benchmark gaming), weighing contested questions (deep learning vs GBDTs on tabular data, scaling laws vs diminishing returns, PyTorch vs JAX, whether benchmark progress is real, bigger models vs better data, how much MLOps tooling, open-weight vs API models), checking whether a framework, model, or hardware claim is still current (snapshot verified August 2026), finding the books, papers, courses, and people worth reading, or needing the numbers, new-project checklist, and triage. Companion to the other machine-learning skills."
---

# Machine Learning: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 4 of 4** of the *Machine Learning* reference (plugin `machine-learning`), covering §15–§20. Sibling skills: `ml-framing-data-and-classical` (§0–§3), `ml-deep-learning-and-training` (§4–§8), `ml-evaluation-serving-mlops-and-safety` (§9–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — statistics, optimization theory, or a lesson the field has relearned
>   every few years. Does not expire.
> - **[VERSIONED]** — framework versions, hardware, library APIs. Moving fast; verify.
> - **[CONTESTED]** — practitioners genuinely disagree.
>
> **⚠️ GOTCHA** boxes mark the mistakes that produce a model that looks great offline and
> fails in production — which is the characteristic failure of this field.
>
> **The three framings that organize everything below:**
> 1. **Your data is the model.** Architecture choices matter far less than data quality,
>    quantity, and whether your evaluation measures the thing you care about. Most time on
>    a real project goes to data, and most catastrophic failures originate there (§2 → `ml-framing-data-and-classical`).
> 2. **The default failure mode is a number that lies.** Leakage, distribution shift, a
>    metric that doesn't match the objective, a test set you tuned against. **A model that
>    looks too good almost always is** — and finding out why is the core skill.
> 3. **Almost everything you'll build should not be a neural network.** For tabular data —
>    which is most business data — gradient-boosted trees remain the strongest default
>    (§3.1 → `ml-framing-data-and-classical`). Reach for deep learning when you have perceptual data, sequences, very large
>    datasets, or a pretrained model to adapt.

---

## §15. Anti-Patterns

| Anti-pattern | Why | Instead |
|---|---|---|
| Using ML where rules work | Unmaintainable, undebuggable, drifts | Write the rules (§1.1 → `ml-framing-data-and-classical`) |
| No baseline | You can't tell if the model helps | Majority class / mean / linear / existing heuristic (§1.2 → `ml-framing-data-and-classical`) |
| Preprocessing before splitting | **Leakage** | Fit on train only; use a `Pipeline` (§2.1 → `ml-framing-data-and-classical`) |
| Random-splitting time series | The model sees the future | Split by time (§2.1 → `ml-framing-data-and-classical`) |
| Ignoring group structure in splits | Same entity in train and test | Grouped splits (§2.1 → `ml-framing-data-and-classical`) |
| Repeatedly evaluating on the test set | Slow-motion leakage | One final look (§2.1 → `ml-framing-data-and-classical`, §9.2 → `ml-evaluation-serving-mlops-and-safety`) |
| Celebrating a suspiciously good result | It's almost always leakage | **Go looking for the bug** (§2.1 → `ml-framing-data-and-classical`) |
| Reaching for deep learning on tabular data | GBDTs are the stronger default | XGBoost/LightGBM/CatBoost (§3.1 → `ml-framing-data-and-classical`) |
| Using accuracy on imbalanced data | 99% accuracy can be useless | PR-AUC, F1, confusion matrix (§9.1 → `ml-evaluation-serving-mlops-and-safety`) |
| Leaving the threshold at 0.5 | It's a free parameter matched to your costs | Tune it (§9.1 → `ml-evaluation-serving-mlops-and-safety`) |
| Using uncalibrated probabilities in a decision | Probabilities are meaningfully wrong | Calibrate (§3.2 → `ml-framing-data-and-classical`) |
| Reporting a single run | Much of it is seed noise | Multiple seeds + variance (§9.2 → `ml-evaluation-serving-mlops-and-safety`) |
| Comparing against an untuned baseline | Not a comparison | Tune both equally (§9.2 → `ml-evaluation-serving-mlops-and-safety`) |
| Only aggregate metrics | Hides systematic subgroup failure | Slice everything (§9.2 → `ml-evaluation-serving-mlops-and-safety`, §14.2 → `ml-evaluation-serving-mlops-and-safety`) |
| Never reading the model's errors | Highest-value diagnostic, skipped | Read 50 mistakes (§9.2 → `ml-evaluation-serving-mlops-and-safety`) |
| Trusting public benchmark scores | **Contamination is pervasive** | Build a private eval set (§9.3 → `ml-evaluation-serving-mlops-and-safety`) |
| Adam with weight decay | Not equivalent to true weight decay | **AdamW** (§4.2 → `ml-deep-learning-and-training`) |
| Tuning architecture before learning rate | LR dominates | Sweep LR first (§4.2 → `ml-deep-learning-and-training`) |
| Debugging without overfitting one batch | You're guessing | Overfit 2–10 examples first (§10 → `ml-evaluation-serving-mlops-and-safety`) |
| Using fp16 without loss scaling | Gradient underflow → NaN | **bf16** (§7.2 → `ml-deep-learning-and-training`) |
| Fine-tuning to add knowledge | Teaches behaviour well, facts poorly | **Retrieve** (§8 → `ml-deep-learning-and-training`) |
| Fine-tuning without checking for forgetting | Narrow gains, broad losses | Evaluate untrained capabilities (§8 → `ml-deep-learning-and-training`) |
| Computing features in two codepaths | **Training/serving skew** | Feature store or one shared path (§12.2 → `ml-evaluation-serving-mlops-and-safety`) |
| Deploying without monitoring | Silent degradation | Monitor predictions and inputs (§12.3 → `ml-evaluation-serving-mlops-and-safety`) |
| No rollback path | A bad model is an outage | Instant rollback (§12.3 → `ml-evaluation-serving-mlops-and-safety`) |
| Scaling hardware before profiling | Most jobs are dataloader-bound | Profile first (§13 → `ml-evaluation-serving-mlops-and-safety`) |
| Assuming quantization is free | Degradation concentrates in hard cases | Evaluate quantized on **your** task (§11.3 → `ml-evaluation-serving-mlops-and-safety`) |
| Reading t-SNE/UMAP distances as meaningful | They aren't | Visualization only (§3.2 → `ml-framing-data-and-classical`) |
| Treating feature importance as causal | It describes the model, not the world | Causal methods, or don't claim it (§14.1 → `ml-evaluation-serving-mlops-and-safety`) |
| Treating attention as explanation | Well-known negative result | Other methods (§14.1 → `ml-evaluation-serving-mlops-and-safety`) |
| Loading pickled checkpoints from strangers | Arbitrary code execution | **safetensors** (§14.3 → `ml-evaluation-serving-mlops-and-safety`) |
| Ignoring `torch.compile` graph breaks | Silently loses the speedup | `error_on_graph_break()` (§6.1 → `ml-deep-learning-and-training`) |

---

## §16. Contested Questions

**16.1 Deep learning vs. GBDTs on tabular data.** §3.1 → `ml-framing-data-and-classical`. The weight of independent benchmark
evidence favours trees, but the literature genuinely conflicts — some studies find
well-regularized MLPs competitive, ensembles of both usually beat either alone, and trees
are documented as generalizing less well to unseen distributions and being less robust to
uninformative features. **The practical position — start with a GBDT, and prove a neural
network earns its complexity — is well-supported.**

**16.2 Scaling laws vs. diminishing returns.** *For scaling*: the empirical laws have held
remarkably well and predicted capabilities. *Against*: data is finite, compute costs are
enormous, and returns on some capabilities appear to be flattening. Post-training and
inference-time compute have absorbed much of the recent progress, which is itself evidence
about pretraining's marginal returns.

**16.3 PyTorch vs. JAX.** *PyTorch*: dominant ecosystem, easier debugging, most models
ship here first. *JAX*: functional purity, superior compilation and TPU story, better for
large-scale research where transformations compose. **Most people should use PyTorch; JAX
is a defensible choice for a team that will use its strengths.**

**16.4 Is benchmark progress real?** Contamination, overfitting to leaderboards, and the
gap between benchmark scores and task performance are all documented. **The defensible
position: benchmarks are directionally useful and precisely misleading**, which is why §9.3 → `ml-evaluation-serving-mlops-and-safety`
recommends a private eval set.

**16.5 Bigger models vs. better data.** Increasing evidence that data quality and curation
give more per dollar than parameter count, especially in post-training. **Not settled**, but
the direction of practitioner opinion has moved decisively toward data.

**16.6 How much MLOps tooling.** *For*: reproducibility, monitoring, and safe deploys are
real needs. *Against*: enormous accidental complexity, and many teams build a platform
before they have a model worth deploying. **Start with experiment tracking, versioned data,
and monitoring; add the rest when it hurts.**

**16.7 Open-weight vs. API models.** *Open*: control, privacy, no per-token cost at volume,
customization. *API*: no ops, frontier capability, elastic. **The break-even is real and
computable** (§11.4 → `ml-evaluation-serving-mlops-and-safety`) — and it depends almost entirely on utilization, not on ideology.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **PyTorch** | **2.13 (July 2026)** — 3,328 commits from 526 contributors since 2.12. **FlexAttention on Apple Silicon (MPS)** with ~12× speedup over SDPA on sparse patterns, plus a deterministic CUDA backward path. **CuTeDSL "Native DSL" Inductor backend** alongside Triton for GEMM/RMSNorm. **`nn.LinearCrossEntropyLoss`** cuts peak GPU memory **up to 4×** for large-vocab LM training. **torchcomms** distributed backend. **FSDP2 reduce-scatter/all-gather overlap** (opt-in). Python 3.15 wheels incl. free-threaded 3.15t. ⚠️ **Breaking: named tensors and Bazel build removed** | **High** |
| **PyTorch release cadence** | Roughly quarterly: 2.9 (Oct 2025), 2.10 (Jan 2026), 2.11 (Mar 2026), 2.12 (May 2026), 2.13 (Jul 2026) | **High** |
| **torchcomms migration** | ⚠️ PyTorch plans to make **torchcomms the default in 2.13+**, with **breaking ProcessGroup changes** — eager initialization required at `dist.init_process_group`, single backend device only. Available now via `pip install torchcomms` + `TORCH_DISTRIBUTED_USE_TORCHCOMMS=1` | **High** |
| **Python support** | ⚠️ **CPython 3.13t (free-threaded) binaries dropped** — manylinux removed 3.13t on **7 May 2026** as superseded by non-experimental 3.14t. Move free-threaded workloads to 3.14t | Medium |
| **TGI** | ⚠️ **Maintenance mode** — announced December 2025, **repository archived read-only 21 March 2026**, redirecting to vLLM, SGLang, llama.cpp, MLX | Low |
| **Serving engines** | **vLLM** is the practical default (NVIDIA CUDA, AMD ROCm, Intel XPU, Google TPU, Trainium/Inferentia, Gaudi, Arm). **SGLang** for prefix-heavy workloads (RadixAttention) — one comparison reports ~29% higher throughput than vLLM on H100 and much larger gains on RAG/multi-turn. **TensorRT-LLM** for deepest NVIDIA optimization. **FlashInfer** is the default attention backend for vLLM on Blackwell and for SGLang on both Hopper and Blackwell | Medium |
| **NVIDIA Dynamo** | Inference layer disaggregating prefill and decode; NVIDIA claims **up to 7× throughput per GPU** for DeepSeek R1 on GB200 NVL72. Integrates with TensorRT-LLM, vLLM, SGLang | Medium |
| **Hardware** | **H100 80GB** — most mature software ecosystem. **H200** — 141 GB, 4.8 TB/s (+43% bandwidth). **Blackwell B200/GB200/B300** — 192 GB HBM3e, NVFP4; NVIDIA claims ~3× faster LLM training than prior gen. **Rubin/Vera** announced for agentic training and inference. **RTX PRO 6000 Blackwell (96 GB)** for workstation-class serving | Medium |
| **Inference economics** | **Inference is now ~2/3 of all AI compute** (up from ~1/3 in 2023). Cost-per-token: **~$0.40/M tokens for GPT-4-equivalent in early 2026 vs ~$20 in late 2022**. Engine improvements took GPU utilization from **~30–40% to ~70–80%**. Self-hosting reaches API cost parity within **1–4 months at ~30M tokens/day** in one 2026 study | Medium |
| **Gradient boosting** | **XGBoost 3.2** (mature categoricals, terabyte-scale external memory), **LightGBM 4.6** (fastest, lowest memory), **CatBoost 1.2.10** (best defaults on categorical-heavy data). ⚠️ **The gap between them has narrowed to near-irrelevance** — feature engineering and tuning matter more. **HistGradientBoosting** identified as most stable across datasets in comparative work | Low |
| **Tabular DL vs GBDT** | Trees still lead on the weight of benchmark evidence (Shwartz-Ziv & Armon; Grinsztajn et al.), though newer benchmarks (TabArena, OmniTabBench) and foundation models like **TabPFN** — strong on *small* datasets — keep the question live | Medium |

**Goes stale fastest:** PyTorch versions and APIs; serving-engine benchmarks; GPU
generations and pricing; inference cost figures. **Essentially never stale:** §1 → `ml-framing-data-and-classical` (framing),
§2 → `ml-framing-data-and-classical` (leakage), §4 → `ml-deep-learning-and-training` (optimization fundamentals), §9 → `ml-evaluation-serving-mlops-and-safety` (evaluation discipline), §10 → `ml-evaluation-serving-mlops-and-safety` (debugging
ladder), §14.2 → `ml-evaluation-serving-mlops-and-safety` (fairness impossibility), §15 (anti-patterns).

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Hastie, Tibshirani, Friedman** | ***The Elements of Statistical Learning*** (**free**) | The statistical foundation. Dense and worth it |
| **James et al.** | ***An Introduction to Statistical Learning*** (**free**) | ESL's accessible sibling. **The best starting book** |
| **Goodfellow, Bengio, Courville** | ***Deep Learning*** (**free**) | The foundational DL text; dated on architectures, excellent on theory |
| **Kevin Murphy** | *Probabilistic Machine Learning* (2 vols, **free drafts**) | The most comprehensive modern reference |
| **Christopher Bishop** | *Pattern Recognition and ML*; *Deep Learning: Foundations and Concepts* (2024) | The classic, and its modern successor |
| **Aurélien Géron** | ***Hands-On ML with Scikit-Learn, Keras & TensorFlow*** | **The best practical book.** Start here if you want to build things |
| **Chip Huyen** | ***Designing Machine Learning Systems***; *AI Engineering* | **The best book on the parts that aren't modeling** — §12 → `ml-evaluation-serving-mlops-and-safety`, §1 → `ml-framing-data-and-classical`, §9 → `ml-evaluation-serving-mlops-and-safety` |
| **Andriy Burkov** | *The Hundred-Page ML Book*; *The Hundred-Page LLM Book* | Exactly what they say |
| **Jeremy Howard & Sylvain Gugger** | *Deep Learning for Coders with fastai and PyTorch* | Top-down and effective |
| **Sebastian Raschka** | *Build a Large Language Model (From Scratch)* | The clearest LLM-internals walkthrough |
| **Zhang et al.** | *Dive into Deep Learning* (**free, interactive**) | Runnable code alongside the math |
| **Pearl & Mackenzie** | *The Book of Why* | For §1.1 → `ml-framing-data-and-classical`'s prediction≠causation |

### 18.2 Papers worth reading directly
*Attention Is All You Need* (2017). *Adam* and *Decoupled Weight Decay* (AdamW) — read the
second to understand §4.2 → `ml-deep-learning-and-training`. *Batch Normalization*, *Layer Normalization*, *Deep Residual
Learning*. *Scaling Laws for Neural Language Models* (Kaplan) and *Training
Compute-Optimal LLMs* (Chinchilla). *LoRA* and *QLoRA*. *FlashAttention* 1–3. *Direct
Preference Optimization*. **"Tabular Data: Deep Learning Is Not All You Need"** and
**"Why do tree-based models still outperform deep learning on tabular data?"** for §3.1 → `ml-framing-data-and-classical`.
*Attention is not Explanation*. *Hidden Technical Debt in Machine Learning Systems*
(Sculley et al. — **read this one before you build a platform**).

### 18.3 Courses, sites, people
**Andrej Karpathy's** "Neural Networks: Zero to Hero" and **`nanoGPT`/`micrograd`** —
**the single best way to actually understand what's happening**; his *"A Recipe for
Training Neural Networks"* is the best short piece on §10 → `ml-evaluation-serving-mlops-and-safety`. **fast.ai** (top-down, practical),
**Stanford CS231n** (vision), **CS224n** (NLP), **Andrew Ng's** courses (the on-ramp),
**Hugging Face courses** (free, practical, current). **Distill.pub** (dormant but the
explanations are timeless), **The Illustrated Transformer** (Jay Alammar),
**Lil'Log** (Lilian Weng — the best technical survey blog in ML), **Sebastian Raschka's
Ahead of AI**, **Papers with Code**, and **Weights & Biases' reports**.

**People**: Karpathy, Lilian Weng, Chip Huyen, Sebastian Raschka, Jeremy Howard,
François Chollet (especially on evaluation and generalization), Yann LeCun,
Rachel Thomas (fairness), Tim Dettmers (quantization, QLoRA), Tri Dao (FlashAttention),
Horace He (PyTorch performance).

---

## §19. Quick Reference

### 19.1 Numbers
- **fp32 Adam training ≈ 16 bytes/parameter** before activations.
- Gradient checkpointing: **~30% more compute** for large activation memory savings.
- **Cross-entropy at init on k balanced classes ≈ ln(k)** — check this.
- **bf16 needs no loss scaling; fp16 does.**
- INT4 quantization: **~4× memory reduction**, small quality cost.
- Attention is **O(n²)** in sequence length.
- **H100 80 GB · H200 141 GB · B200 192 GB.**
- Self-hosting vs. API break-even: **cloud wins under ~8 hrs/day utilization.**

### 19.2 New-project checklist
- [ ] Is ML actually the right tool? (§1.1 → `ml-framing-data-and-classical`)
- [ ] Baseline defined and measured **first**
- [ ] Metric chosen from the decision it informs; threshold treated as tunable
- [ ] Split strategy correct for the data's structure (time? groups?)
- [ ] Preprocessing inside a `Pipeline`, fit on train only
- [ ] Leakage checklist walked (§2.1 → `ml-framing-data-and-classical`)
- [ ] Deployment constraints known **before** modeling (latency, memory, cost)
- [ ] For tabular: GBDT tried before anything deep
- [ ] Multiple seeds; variance reported
- [ ] Metrics sliced by relevant subgroups
- [ ] 50 errors read by a human
- [ ] Versions and data versioned and logged
- [ ] Monitoring and rollback in place before launch

### 19.3 Triage
| Symptom | First look |
|---|---|
| Too good to be true | **Leakage** (§2.1 → `ml-framing-data-and-classical`). Assume it until disproven |
| Great offline, bad in production | Distribution shift, or training/serving skew (§12.2 → `ml-evaluation-serving-mlops-and-safety`) |
| Loss NaN | LR, fp16 overflow (**use bf16**), log(0), bad data |
| Loss flat | LR too low, frozen params, disconnected graph |
| Can't overfit one batch | **You have a bug**, not a tuning problem (§10 → `ml-evaluation-serving-mlops-and-safety`) |
| GPU underutilized | Dataloader-bound; check batch size and workers |
| OOM | Optimizer state → 8-bit/fused; activations → checkpointing; §7.3 → `ml-deep-learning-and-training` |
| Slower after `torch.compile` | Graph breaks or recompilation on dynamic shapes (§6.1 → `ml-deep-learning-and-training`) |
| Model degraded over months | Expected — drift. Retrain (§12.3 → `ml-evaluation-serving-mlops-and-safety`) |

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. The durable material — §1 → `ml-framing-data-and-classical` (framing),
§2 → `ml-framing-data-and-classical` (leakage and splitting), §4 → `ml-deep-learning-and-training` (optimization and training fundamentals), §9 → `ml-evaluation-serving-mlops-and-safety` (evaluation),
§10 → `ml-evaluation-serving-mlops-and-safety` (debugging), §12 → `ml-evaluation-serving-mlops-and-safety`, §14.2 → `ml-evaluation-serving-mlops-and-safety`, §15 — rests on established statistics and optimization
literature, the standard references in §18, and practices that have been stable across
framework generations. Every **time-sensitive** claim (framework versions, serving-engine
comparisons, hardware specs, cost figures) was verified against a primary or near-primary
source in **August 2026** and is flagged in §17 with a decay-risk rating. Where the
literature genuinely conflicts — notably §3.1 → `ml-framing-data-and-classical`'s tabular question — §16 presents both sides
rather than picking one.

**Search log** (August 2026): PyTorch current version and release features · vLLM/SGLang/
TensorRT-LLM serving landscape and NVIDIA hardware · gradient boosting versus deep learning
on tabular data.

**Primary and near-primary sources consulted (selected):**
- **PyTorch** — the 2.13 release announcement and GitHub release notes, the 2.12 release
  blog (torchcomms migration and breaking ProcessGroup changes), the PyTorch Versions wiki,
  and the PyTorch dev-discuss release-announcement threads
- **Academic benchmarks for §3.1 → `ml-framing-data-and-classical`** — Shwartz-Ziv & Armon, *Tabular Data: Deep Learning Is
  Not All You Need* (arXiv 2106.03253); Grinsztajn et al., *Why do tree-based models still
  outperform deep learning on tabular data?* (arXiv 2207.08815); a 2025 *Neurocomputing*
  comprehensive benchmark; and 2026 comparative work identifying HistGradientBoosting's
  stability. Counter-evidence (Kadra et al. on regularized MLPs; TabR; TabPFN) noted
- **Serving and hardware** — Inference Engineering's vLLM/SGLang/TensorRT-LLM and hardware
  guides; comparative benchmarks from Particula, Yotta Labs, JarvisLabs and
  decodethefuture; Spheron on FlashInfer backend defaults; NVIDIA's AI training platform
  pages and GTC 2026 coverage on Dynamo; Thunder Compute and VRLA Tech on the TGI
  maintenance-mode transition and GPU selection
- **Economics** — GPUnex's 2026 inference-economics analysis; an arXiv study (2601.09527)
  benchmarking self-hosted inference cost parity on consumer Blackwell GPUs

**Confidence statement.** **High confidence** in §1–§5 → `ml-framing-data-and-classical`, `ml-deep-learning-and-training`, §9 → `ml-evaluation-serving-mlops-and-safety`, §10 → `ml-evaluation-serving-mlops-and-safety`, §12 → `ml-evaluation-serving-mlops-and-safety`, §14 → `ml-evaluation-serving-mlops-and-safety`, §15 and §19 —
these rest on textbook statistics, established optimization results, and practices
consistently reported across the standard references. **High confidence** in the PyTorch
2.13 details in §17, which come from PyTorch's own release notes and announcements.
**Moderate confidence** in §11.1 → `ml-evaluation-serving-mlops-and-safety`'s serving-engine performance comparisons: the throughput
numbers come from third-party benchmarks run on specific hardware with specific models and
workloads, **different benchmarks reach different conclusions**, and both engines are
evolving fast enough that a six-month-old number may be wrong — treat them as directional
and benchmark on your own workload. **Moderate confidence** in §11.4 → `ml-evaluation-serving-mlops-and-safety`'s and §17's cost
figures, which come from industry analysis rather than audited data and depend heavily on
assumptions about utilization and model choice. **Moderate confidence, deliberately hedged,
in §3.1 → `ml-framing-data-and-classical`**: the weight of independent evidence favours GBDTs on tabular data and I've said
so, but I have also cited the conflicting findings, and the *reason* the practical advice
holds (start with a GBDT, make the neural network earn its complexity) is about cost and
tuning burden as much as about raw accuracy. Hardware specifications in §13 → `ml-evaluation-serving-mlops-and-safety` come from
vendor materials and vendor performance claims (notably NVIDIA's "3× faster training") are
**vendor-measured on vendor-chosen benchmarks** and should be treated accordingly.

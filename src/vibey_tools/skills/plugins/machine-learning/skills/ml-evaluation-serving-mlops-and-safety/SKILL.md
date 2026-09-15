---
name: ml-evaluation-serving-mlops-and-safety
description: "Use when evaluating, debugging, deploying, or governing models. Covers metrics and doing evaluation honestly, evaluating generative models, debugging training runs (NaNs, divergence, overfitting, data bugs), inference and serving (vLLM, SGLang, batching, the KV cache, quantization, what actually determines inference cost and its economics), MLOps and reproducibility (the pipeline, monitoring, drift), hardware and cost, and interpretability, fairness, security, and safety."
---

# Machine Learning: Evaluation, Debugging, Inference and Serving, MLOps, and Responsible ML

> **Part 3 of 4** of the *Machine Learning* reference (plugin `machine-learning`), covering §9–§14. Sibling skills: `ml-framing-data-and-classical` (§0–§3), `ml-deep-learning-and-training` (§4–§8), `ml-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `ml-reference` for the currency snapshot and what goes stale first.

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

## §9. Evaluation

**[DURABLE] This section is where most projects actually fail, and it fails quietly.**

### 9.1 Metrics

**⚠️ Accuracy is almost always the wrong metric.** On a 99:1 imbalanced problem, predicting
the majority class gets 99% accuracy and is useless.

| Task | Metrics |
|---|---|
| **Binary classification** | Precision, recall, F1, **PR-AUC** (better than ROC-AUC under heavy imbalance), ROC-AUC, MCC, and the **confusion matrix — always look at it** |
| **Multi-class** | Macro (treats classes equally) vs. micro (weights by frequency) vs. weighted — **say which you used; they disagree substantially** |
| **Regression** | MAE (robust), RMSE (penalizes large errors), MAPE (⚠️ breaks near zero, asymmetric), R² |
| **Ranking / retrieval** | NDCG, MRR, MAP, recall@k, precision@k |
| **Probabilistic** | **Log loss, Brier score, calibration curves** — use these when the probability matters |
| **Generative / LLM** | Task-specific benchmarks, human eval, LLM-as-judge (⚠️ §9.3), pairwise preference |

**[DURABLE] Choose the metric from the decision it informs.** If false negatives cost 100×
false positives, optimize for that, and **tune the decision threshold explicitly** — it's a
free parameter most people leave at 0.5 for no reason.

### 9.2 Doing it honestly

- **One test-set evaluation.** Every additional look is leakage (§2.1 → `ml-framing-data-and-classical`).
- **Report variance**, not a point estimate. Multiple seeds, confidence intervals,
  bootstrapping. **⚠️ A great deal of reported "improvement" in ML is within seed noise**,
  and the field's reproducibility problems are substantially this.
- **Compare against a strong baseline**, tuned as carefully as your method. An untuned
  baseline is not a comparison.
- **Slice your metrics.** Aggregate performance hides systematic failure on subgroups —
  by user segment, geography, device, class, time period. **This is both an accuracy
  practice and a fairness practice** (§14.2).
- **Evaluate on distribution shift** you expect in production: a future time period, a new
  region, a new source.
- **Look at the errors.** Sample 50 mistakes and read them. **Consistently the highest
  information-per-minute activity in applied ML**, and consistently skipped.

### 9.3 Evaluating generative models

Hard, and getting harder. **Benchmark contamination** is pervasive — test sets leak into
pretraining corpora, so public benchmark scores are systematically optimistic.
**LLM-as-judge** is practical and scalable but carries **position bias, verbosity bias,
and self-preference bias**; mitigate by randomizing order, using multiple judges, and
calibrating against human labels on a subset. **Build a private eval set from your actual
task**, hold it out, and version it — this beats any public benchmark for deciding whether
your system works.

---

## §10. Debugging Training

**[DURABLE] A systematic ladder, in order. Skipping steps is what makes debugging take
weeks.**

1. **Overfit a single batch.** Train on 2–10 examples until loss ≈ 0. **If you can't, you
   have a bug, not a learning-rate problem.** This is the single most valuable diagnostic in
   deep learning and takes two minutes.
2. **Check shapes and the data.** Print them. Visualize an actual batch after
   augmentation. **⚠️ Silent broadcasting bugs are endemic** — a `(B,1)` vs. `(B,)` mismatch
   produces a `(B,B)` tensor and a loss that trains to something meaningless.
3. **Verify the loss at initialization.** Cross-entropy on k balanced classes should start
   near `ln(k)`. If it doesn't, your labels, logits, or reduction are wrong.
4. **Check the label pipeline end-to-end.** Off-by-one, shuffled labels, wrong mapping.
5. **Watch gradient norms.** Zero → disconnected graph or dead activations. Exploding →
   clip, lower the LR, check normalization.
6. **Sweep the learning rate** over orders of magnitude before touching anything else.
7. **Compare train vs. validation curves**: both high = underfitting (bigger model, train
   longer, better features); train low + val high = overfitting (more data, more
   regularization, augmentation); **val better than train** = a bug, or dropout/BN
   train-mode artifacts.
8. **Turn off tricks** — augmentation, scheduler, mixed precision, `torch.compile` — and
   reintroduce them one at a time.

| Symptom | Likely cause |
|---|---|
| Loss is NaN | LR too high; log(0)/div-by-zero; fp16 overflow (**use bf16**); bad input data |
| Loss flat from step 0 | LR too low; frozen params; disconnected graph; `optimizer.zero_grad()` misplaced |
| Loss decreases then explodes | LR too high; missing gradient clipping; a bad batch |
| Great train, terrible val | Overfitting, or **leakage in reverse** (val is harder/different) |
| Great val, terrible production | **Distribution shift, or leakage** (§2.1 → `ml-framing-data-and-classical`). Check the leakage list first |
| Works in eager, breaks compiled | Graph breaks, dynamic shapes, or a numerics difference |
| Non-deterministic across runs | Expected — see §12.1. Report variance |
| Slower than expected on GPU | Dataloader-bound (check GPU utilization), small batches, unnecessary syncs, `.item()` in the loop |

---

## §11. Inference and Serving

### 11.1 The landscape

**[VERSIONED — this layer moved fast and consolidated in 2025–2026.]**

| Engine | Best for |
|---|---|
| **vLLM** | **The practical default.** Broadest hardware support (NVIDIA CUDA, AMD ROCm, Intel XPU, Google TPU, and more), one `pip` install, OpenAI-compatible server immediately |
| **SGLang** | **Long shared prefixes** — RAG over a fixed corpus, multi-turn agents, structured decoding. **RadixAttention** turns prefix overlap into automatic cache hits. Reported ~29% higher throughput than vLLM on H100 in one comparison, with much larger gains on prefix-heavy workloads |
| **TensorRT-LLM** | Committed to NVIDIA's newest silicon and want the deepest kernel-level optimization — **paid for in build complexity** |
| **llama.cpp / Ollama / MLX** | Single-user local inference, CPU and Apple Silicon |
| **Triton Inference Server / Ray Serve** | General model serving, multi-model, non-LLM |

**⚠️ [VERSIONED] Hugging Face TGI moved to maintenance mode** (announced December 2025,
repository archived read-only **21 March 2026**), redirecting users to vLLM, SGLang,
llama.cpp, and MLX. **If you're on TGI, plan a migration.**

**[DURABLE] The feature set has converged.** Any modern engine gives you **continuous
(in-flight) batching** — new requests join the running batch the moment a slot frees, which
is the single biggest throughput unlock over naïve batching — and a **paged KV cache**
(virtual-memory management for the attention K/V store). Choose on hardware breadth,
workload shape, and operational complexity, not on feature checklists.

### 11.2 What actually determines inference cost

**[DURABLE]** LLM inference has two distinct phases with completely different bottlenecks:
- **Prefill** (processing the prompt) — **compute-bound**, parallel across tokens.
- **Decode** (generating tokens) — **memory-bandwidth-bound**, one token at a time.

**This asymmetry drives everything**: it's why **disaggregated prefill/decode** (routing
each phase to different hardware) is a major 2026 architecture, why **memory bandwidth
matters more than FLOPs** for serving, and why batch size helps decode enormously.

**The KV cache is usually your real memory constraint**, growing linearly with batch size
and sequence length. **GQA/MQA**, **paged attention**, **prefix caching**, and **KV cache
quantization** all exist to attack it.

**Other levers**: **quantization** (§11.3), **speculative decoding** (a small draft model
proposes, the big model verifies — real latency wins), **prefix caching**, and **structured
output constraints**.

### 11.3 Quantization

| Format | Use |
|---|---|
| **INT8 / W8A8** | Well-established, minimal quality loss |
| **INT4 / W4A16** (GPTQ, AWQ) | **The common serving choice.** ~4× memory reduction, small quality cost |
| **FP8** | Native hardware support on Hopper/Blackwell; good quality retention |
| **NVFP4 / MXFP4** | 4-bit with Blackwell hardware support; increasingly used |
| **GGUF (k-quants)** | The llama.cpp ecosystem, CPU and Apple Silicon |

**[DURABLE] Quantization-aware training beats post-training quantization on quality and
costs more.** For most people PTQ with a good calibration set is sufficient. **⚠️ Always
evaluate the quantized model on your own task** — published "negligible degradation" claims
are measured on benchmarks that may have nothing to do with your use case, and degradation
is often concentrated in exactly the hard cases you care about.

### 11.4 The economics

**[VERSIONED, and the trend is the point]**: **inference now accounts for roughly two-thirds
of all AI compute, up from about one-third in 2023**, and cost-per-token has fallen by
orders of magnitude — one analysis puts GPT-4-equivalent performance at roughly **$0.40 per
million tokens in early 2026 versus ~$20 in late 2022**. Serving-engine improvements are a
large part of it: **GPU utilization went from ~30–40% to ~70–80%** through continuous
batching, paged attention, and speculative decoding.

**[DURABLE] The practical consequence: cost-per-token is the KPI**, and a 10× inference cost
reduction directly enables 10× the users at the same budget. Self-hosting reaches cost
parity with commercial APIs at moderate volume — one 2026 study found parity within 1–4
months at ~30M tokens/day — but **only if you actually keep the hardware busy.**

---

## §12. MLOps and Reproducibility

### 12.1 Reproducibility

**[DURABLE] Bit-exact reproducibility on GPU is achievable but costly**, and most teams
should aim for *statistical* reproducibility instead: seed everything (Python, NumPy,
framework, dataloader workers), pin all versions and record them, version data and code
together, log the full config, and **report variance across seeds rather than a single
run**. Full determinism requires deterministic algorithms (`torch.use_deterministic_algorithms`),
disabling cuDNN benchmarking, and fixed dataloader ordering — and it will slow you down.

**Version the data.** Model artifacts without the exact training data are not reproducible,
and "we retrained and got different numbers" is otherwise unresolvable.

### 12.2 The pipeline

```
data ingestion → validation → feature engineering → training → EVALUATION GATE
  → registry → deployment (shadow → canary → full) → MONITORING → retraining
```
**[DURABLE] The evaluation gate and monitoring are the parts people skip**, and they're
the parts that prevent silent disasters.

**Feature stores** solve a real problem — **training/serving skew**, where the features
computed at training time differ subtly from those computed at inference. **⚠️ This is one
of the most common and hardest-to-find production bugs**, and if you compute features in
two different codepaths you will eventually have it.

### 12.3 Monitoring

Monitor, in roughly this priority order: **prediction distribution** (drifts first and
cheapest to watch), **input feature distributions** (PSI, KL divergence), **actual
performance** where labels eventually arrive, **latency and throughput**, **error rates**,
and **business metrics** (the only ones that ultimately matter).

**[DURABLE] Models degrade. Plan for retraining from day one** — trigger it on a schedule,
on drift detection, or on performance drop. And **keep the ability to roll back to the
previous model instantly**; a bad model deploy is an outage.

---

## §13. Hardware and Cost

**[VERSIONED]**

| Tier | Notes |
|---|---|
| **H100 (80 GB)** | ⚠️ **The software ecosystem is most mature here** — vLLM, SGLang, TensorRT-LLM, PyTorch, JAX. **Any optimization technique you read about was probably benchmarked on H100** |
| **H200 (141 GB)** | Same die as H100 with HBM3e: **141 GB and 4.8 TB/s (+43% bandwidth)**. Often better per-token cost than 2× H100 for FP16 70B |
| **Blackwell (B200/GB200/B300)** | **192 GB HBM3e** — a 70B FP16 model with real KV headroom, or 405B FP8 on two chips. NVFP4 support. ~3× faster LLM training than the prior generation by NVIDIA's own MLPerf claims |
| **Rubin / Vera** | The announced next generation, aimed at agentic training and inference |
| **RTX PRO 6000 Blackwell (96 GB)** | Workstation-class; 4–8 in a rackmount is a standard 2026 self-hosting configuration |
| **AMD MI300X / ROCm** | Real and improving; **NVIDIA remains the default for vLLM, Unsloth, and most production workflows** |
| **TPU v5e/v6, Trainium/Inferentia, Gaudi 3** | Viable, especially via JAX (TPU) or where you have committed cloud spend |

**[DURABLE] For LLM inference, memory capacity and bandwidth dominate the selection
decision, not FLOPs** (§11.2). For training, interconnect (NVLink, InfiniBand) often
matters more than per-chip performance once you're multi-node.

**Cost discipline**: cloud beats buying unless you keep hardware busy more than roughly
8 hours/day; **spot/preemptible instances plus checkpointing** are the single biggest
training cost lever; profile before scaling up (most jobs are dataloader-bound or
badly-batched, not compute-bound); and **the cheapest optimization is a smaller model that
meets the requirement.**

---

## §14. Interpretability, Fairness, Safety

### 14.1 Interpretability

**Intrinsically interpretable models** — linear models, small trees, GAMs — are
underrated. **[DURABLE] If interpretability is a hard requirement, use an interpretable
model rather than explaining a black box.**

**Post-hoc methods**: **SHAP** (game-theoretic, the practical standard; ⚠️ correlated
features make attributions ambiguous), **LIME** (local surrogates; unstable),
**permutation importance** (⚠️ misleading with correlated features), **partial dependence
and ICE**, attention maps (⚠️ **attention is not explanation** — a well-known result;
attention weights don't reliably indicate what drove the output), and **counterfactuals**
(often the most *useful* form for an affected person).

**⚠️ Feature importance is not causal.** A high-importance feature tells you what the model
uses, not what drives the outcome. Acting on it as if it were causal is a recurring and
expensive error.

### 14.2 Fairness

**[DURABLE] The mathematics constrains you**: demographic parity, equalized odds, and
calibration within groups are **provably mutually incompatible** except in degenerate cases.
**You must choose which fairness definition applies to your context** — there is no
technically neutral option, and pretending otherwise is itself a choice.

Practically: **slice every metric by group** (§9.2 — this is the same practice as good
evaluation), audit training data for representation and historical bias, remember that
**removing a protected attribute doesn't remove its influence** (proxies are everywhere),
and document the model's intended use and limitations (model cards, datasheets).

### 14.3 Security and safety

**Adversarial examples** (small perturbations flip predictions — still largely unsolved),
**data poisoning**, **model extraction**, **membership inference** and **training data
extraction** (models memorize; verbatim regurgitation is real), and **prompt injection**
for LLM systems (⚠️ **not solved**, and any system giving an LLM tools plus untrusted input
has this exposure).

**⚠️ `pickle` deserialization is arbitrary code execution.** Use **safetensors** for model
weights. PyTorch's `weights_only=True` default since 2.6 addresses this, but third-party
checkpoints from unknown sources remain a real supply-chain risk.

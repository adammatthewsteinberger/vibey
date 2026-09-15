---
name: ml-deep-learning-and-training
description: "Use when building or training neural networks. Covers the machinery (autodiff, initialization, normalization, regularization), optimization and schedules, the things that make training work, the updated bias-variance picture, transformers and the rest (CNNs, diffusion, SSMs), PyTorch and torch.compile, JAX and the rest of the stack, training at scale (the parallelism taxonomy — DDP, FSDP, tensor and pipeline parallelism), mixed precision and memory, and fine-tuning and adaptation (full fine-tuning, PEFT/LoRA)."
---

# Machine Learning: Deep Learning, Architectures, the Ecosystem, and Training at Scale

> **Part 2 of 4** of the *Machine Learning* reference (plugin `machine-learning`), covering §4–§8. Sibling skills: `ml-framing-data-and-classical` (§0–§3), `ml-evaluation-serving-mlops-and-safety` (§9–§14), `ml-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §4. Deep Learning Fundamentals

### 4.1 The machinery

```
forward pass  →  loss  →  BACKPROP (reverse-mode autodiff)  →  optimizer step
                              ↑
                    the chain rule, applied over a computation graph
```
**[DURABLE] Backpropagation is reverse-mode automatic differentiation**, not a separate
algorithm. Understanding it as autodiff over a graph explains why memory scales with
activations (you must keep intermediates for the backward pass), why gradient checkpointing
works (recompute instead of store), and why `detach()`/`stop_gradient` does what it does.

### 4.2 Optimization

| Optimizer | Notes |
|---|---|
| **SGD + momentum** | Still competitive for vision; often generalizes better than adaptive methods |
| **Adam / AdamW** | **The default.** ⚠️ **Use AdamW, not Adam, whenever you use weight decay** — Adam's L2 penalty is not equivalent to weight decay, and this measurably hurts |
| **Adafactor / 8-bit Adam** | Memory-efficient for large models — optimizer state is often the largest memory consumer (§7.3) |
| **Muon, Shampoo, second-order** | Active area; real wins reported at scale, less settled than the marketing |

**Learning rate is the hyperparameter that matters most, by a wide margin.** Practices that
consistently pay: **warmup** (especially with transformers and large batches), **cosine or
linear decay**, and an **LR-range test** to find the scale. **[DURABLE] If you can tune only
one thing, tune the learning rate.**

**Batch size** interacts with LR (linear scaling rule as a starting heuristic), affects
generalization, and is often set by memory rather than by choice. **Gradient accumulation**
simulates a large batch on small hardware.

### 4.3 The things that make training work

- **Initialization** — Xavier/Glorot for tanh-family, **He/Kaiming for ReLU-family**.
  Getting this wrong causes vanishing or exploding activations before you write a single
  training loop.
- **Normalization** — **BatchNorm** (⚠️ batch-size dependent, and it behaves differently in
  train vs. eval — a classic bug source), **LayerNorm** (the transformer standard),
  **RMSNorm** (cheaper, now widely preferred in LLMs), GroupNorm.
- **Residual connections** — the innovation that made deep networks trainable at all.
- **Activations** — ReLU, GELU, **SiLU/Swish**, and **SwiGLU** (the modern LLM FFN default).
- **Regularization** — weight decay, dropout (⚠️ largely fallen out of favour in large
  transformers), early stopping, data augmentation (**the most effective regularizer in
  vision**), label smoothing, and mixup/cutmix.
- **Gradient clipping** — by global norm. Cheap insurance against loss spikes.

### 4.4 The bias-variance picture, updated

**[DURABLE, but the classical story is incomplete.]** The textbook U-curve — underfit,
sweet spot, overfit — is real for classical models. **Double descent** complicates it:
past the interpolation threshold, test error can *decrease again* as you keep adding
capacity, which is part of why enormously overparameterized networks work at all.
**Practical implication: "the model is too big, it will overfit" is not a reliable
argument for deep networks**, and regularization plus data scale matters more than
parameter count.

---

## §5. Architectures

### 5.1 Transformers

**[DURABLE] The dominant architecture, and worth understanding mechanically rather than by
analogy.**
```
tokens → embeddings + POSITIONAL INFORMATION
  → N × [ self-attention  →  residual+norm  →  FFN  →  residual+norm ]
    → output head

attention(Q,K,V) = softmax(QKᵀ/√d_k) V
```
Key points: **multi-head attention** runs several attention patterns in parallel;
attention is **O(n²)** in sequence length, which is the central scaling problem; the
**FFN holds most of the parameters**; and **causal masking** is what makes a decoder
autoregressive.

**The modern variants you'll meet**: **RoPE** (rotary position embeddings — now standard),
**GQA / MQA** (grouped/multi-query attention — fewer KV heads, **dramatically smaller KV
cache**, §11.2 → `ml-evaluation-serving-mlops-and-safety`), **FlashAttention** (IO-aware exact attention — not an approximation; it
avoids materializing the n² matrix in HBM), **MoE** (mixture of experts — many parameters,
few active per token), **sliding-window** and other sparse attention, and **SSMs/Mamba**
as the main non-attention contender.

### 5.2 The rest

**CNNs** — still the right choice for many vision tasks, especially with limited data and
compute; ConvNeXt showed a modernized CNN matches ViTs. Convolution's inductive bias
(locality, translation equivariance) is a *feature* when data is scarce.
**Vision Transformers** — win at scale, need more data or heavy augmentation.
**Diffusion models** — the generative image/video/audio default; iterative denoising, with
flow matching as the cleaner modern formulation.
**GNNs** — for genuinely graph-structured data. ⚠️ Often beaten by feature engineering plus
a GBDT; verify the graph structure actually carries signal.
**Encoder-decoder vs. decoder-only** — decoder-only won for general LLMs; encoder models
(BERT-family) remain excellent and much cheaper for classification and retrieval, and are
badly underused because attention moved elsewhere.
**Embedding models** — the workhorse of retrieval, RAG, semantic search, and dedup, and
often the highest-value-per-FLOP thing you can deploy.

---

## §6. The Ecosystem

### 6.1 PyTorch

**[VERSIONED] PyTorch 2.13 is current (July 2026)**, with a roughly quarterly cadence.
The parts that matter:

**`torch.compile`** — the headline feature since 2.0. Traces your model (TorchDynamo),
lowers it (TorchInductor), and generates fused Triton (or now **CuTeDSL**) kernels.
**Typically a substantial speedup for free.** ⚠️ **Watch for graph breaks** — Python
constructs Dynamo can't trace force it to fall back, silently costing you the speedup;
`torch._dynamo.error_on_graph_break()` makes that loud rather than silent.
**Recompilation** on changing shapes is the other tax — mark dynamic dimensions explicitly.

**Other things worth knowing**: `torch.export` is the unified capture path (legacy
`torch.jit` and old ONNX flows are deprecated or removed); **`weights_only=True` is the
default for `torch.load` since 2.6** — a genuine security improvement, since pickle
deserialization is arbitrary code execution; **FlexAttention** for custom attention
patterns without writing kernels; **AOTInductor** for ahead-of-time compilation.

### 6.2 The rest of the stack

| Layer | Tools |
|---|---|
| **Frameworks** | **PyTorch** (dominant in research and increasingly production), **JAX** (functional, `jit`/`grad`/`vmap`/`pmap`, strong on TPU, favored for large-scale research), TensorFlow/Keras (legacy-heavy but alive), **MLX** (Apple Silicon) |
| **Training loops** | **Lightning**, **HF Accelerate**, **torchtune**, raw loops (fine, and often clearer) |
| **Models and data** | **Hugging Face** `transformers`, `datasets`, `tokenizers`, `peft`, `trl` — effectively the industry's default distribution channel |
| **Classical** | scikit-learn, XGBoost, LightGBM, CatBoost, statsmodels |
| **Numerics** | NumPy, pandas, **Polars** (faster, saner API, increasingly the default for new work), DuckDB, Arrow |
| **Kernels** | **Triton** (write GPU kernels in Python), CUDA, FlashAttention, **FlashInfer** |
| **Experiment tracking** | Weights & Biases, MLflow, TensorBoard, Aim |
| **Serving** | **vLLM**, **SGLang**, TensorRT-LLM, Triton Inference Server, Ray Serve, llama.cpp/Ollama (§11 → `ml-evaluation-serving-mlops-and-safety`) |
| **Orchestration** | Ray, Kubeflow, Airflow, Prefect, SLURM (still the HPC standard) |

**[DURABLE] Pin your versions and record them.** The ML stack breaks compatibility
constantly, and "it worked last month" is a real and frequent failure.

---

## §7. Training at Scale

### 7.1 The parallelism taxonomy

| Strategy | Splits | Use when |
|---|---|---|
| **Data parallel (DDP)** | The batch | **The default.** Model fits on one GPU |
| **FSDP / ZeRO** | Parameters, gradients, optimizer state | Model doesn't fit. **The mainstream large-model answer** |
| **Tensor parallel** | Individual matrices, within a layer | Very large layers; needs fast interconnect (NVLink) |
| **Pipeline parallel** | Layers across devices | Very deep models; ⚠️ introduces bubbles |
| **Expert parallel** | MoE experts | MoE models |
| **Context/sequence parallel** | The sequence dimension | Very long context |

**[DURABLE] Real large-scale training composes several of these** ("3D parallelism" and
beyond), and the composition is chosen against your interconnect topology, not in the
abstract. **Communication is usually the bottleneck**, which is why NVLink/InfiniBand
topology drives the design.

**[VERSIONED]** PyTorch's **FSDP2** now supports overlapping reduce-scatter and all-gather
via separate process groups (opt-in), which increases throughput; and **torchcomms** is a
new communications backend for PyTorch Distributed aimed at fault tolerance, scalability,
and debuggability on large clusters — with plans to make it the default, including
breaking changes to how ProcessGroups operate (eager initialization, single backend
device). **If you run large distributed jobs, that migration is on your horizon.**

### 7.2 Mixed precision

**[DURABLE]** Train in low precision, keep a master copy and accumulations in higher
precision.
- **FP16** — needs **loss scaling** (gradients underflow otherwise).
- **BF16** — same exponent range as FP32, less mantissa. **No loss scaling needed. The
  default on modern hardware, and the right choice.**
- **FP8** — real on Hopper and Blackwell; needs careful scaling; increasingly used in
  production training.
- **[VERSIONED] NVFP4 / MXFP4** — 4-bit formats with hardware support on Blackwell,
  now appearing in both training and inference paths.

### 7.3 Memory

**[DURABLE] Know where the memory goes**, because "CUDA out of memory" is the most common
obstacle in practice:
```
parameters  +  gradients  +  OPTIMIZER STATE  +  activations  +  fragmentation
                                    ↑
              Adam keeps 2 extra copies — often the largest single term
```
A rough anchor: **fp32 Adam training costs roughly 16 bytes per parameter** (4 param +
4 grad + 8 optimizer state), before activations. That's why a 7B model doesn't fit on an
80 GB card without help.

**The levers**: **gradient checkpointing** (recompute activations — trades ~30% compute for
large memory savings), **gradient accumulation**, **8-bit or fused optimizers**, **FSDP
sharding**, **`nn.LinearCrossEntropyLoss`** (a 2026 PyTorch addition fusing the final
projection and loss — **cuts peak memory by up to 4× for large-vocabulary LM training**,
where the logits tensor is genuinely enormous), and simply **reducing sequence length**.

---

## §8. Fine-Tuning and Adaptation

**[DURABLE] The order to try things, cheapest first:**
```
1. Prompting / few-shot                  ← no training. Try this first, seriously
2. Retrieval (RAG)                       ← when the problem is missing knowledge
3. PEFT / LoRA                           ← when the problem is behaviour or format
4. Full fine-tuning                      ← when you have real data and real budget
5. Continued pretraining                 ← new domain, large corpus
6. Training from scratch                 ← almost never the right answer
```
**⚠️ The most common expensive mistake is fine-tuning to fix a knowledge problem.**
Fine-tuning teaches *behaviour, style, and format* reliably; it teaches *facts* poorly and
expensively. **If the model doesn't know something, retrieve it.**

**LoRA** — freeze the base, train low-rank adapters (`W + BA`). Tiny memory footprint,
swappable adapters, near-full-fine-tuning quality on most tasks. **QLoRA** adds 4-bit
quantization of the frozen base, putting single-GPU fine-tuning of large models within
reach. Other PEFT: prefix tuning, prompt tuning, IA³, DoRA.

**Post-training / alignment**: **SFT** (supervised fine-tuning on demonstrations), then
preference optimization — **RLHF/PPO** (powerful, complex, unstable), **DPO** (much
simpler, no reward model, now the common default), and GRPO and relatives for reasoning
work. **[DURABLE] Data quality dominates method choice here** — a small, carefully curated
SFT set routinely beats a large noisy one.

**⚠️ Catastrophic forgetting is real.** Fine-tuning on a narrow task degrades general
capability. Mix in general data, use lower learning rates, prefer PEFT, and **evaluate on
capabilities you didn't train on** — not just the target task.

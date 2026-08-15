# 0014 — Optional visual design and deployment opt-in gates

**Status:** accepted · **Date:** 2026-08-14 · **Supersedes:** the entry rule in ADR-0013

## Context

The six numbered phases currently describe an interactive design/build/review
delivery set followed by an interactive/autonomous/interactive Azure deployment
set. Two user choices were missing from that lifecycle:

1. A team may want to review the complete screen and media direction before any
   unattended code is written, but another team may want to go straight from the
   product specification to BUILD.
2. A team may want a local artifact and review demo without granting Vibey any
   Azure deployment authority. Deployment must never be inferred from accepting
   the built product.

Media generation also changes faster than the numbered phase machine. A provider
that supports image generation today may not support video tomorrow, may be
region-limited, may require a separate consent boundary, or may be deprecated.
The current OpenAI video documentation, for example, announces a September 24,
2026 shutdown for the Sora 2 Videos API. A durable plan therefore needs a
capability-based media port, not a permanent model-name dependency.

## Decision

Keep six numbered phases and add two explicit, durable choices:

### Optional pre-build visual-design interstitial

After the user accepts Phase ① DESIGN, Vibey asks:

> “Do you want Vibey to plan and generate the visual, audio, and video assets
> for the screens in this run, then show them to you for approval before BUILD?”

- **No** records `VisualDesignDeclined` and routes directly to Phase ② BUILD.
- **Yes** enters an optional, unnumbered `VISUAL_DESIGN` interstitial. It is a
  first-class queue stage with human gates, durable jobs, artifacts, budgets,
  and loop-backs, but it does not renumber the six user-facing phases.

The opt-in stage must:

1. inventory every screen/route that will be created or changed, including
   responsive variants and loading, empty, error, success, permission, offline,
   and reduced-motion states;
2. derive a design system contract (tokens, typography, spacing, color,
   component patterns, interaction states, accessibility requirements, and
   content tone) from the accepted spec and any existing repository design
   context;
3. create a media manifest for each required image, audio clip, video, icon,
   illustration, animation, transcript, caption, alt description, and source or
   rights constraint;
4. generate candidate visual assets from structured prompts and the accepted
   screen specs, using the media provider registry below;
5. show a reviewable screen gallery/prototype, audio previews/transcripts, and
   video storyboards/clips to the user; and
6. enter BUILD only when every planned screen has an accepted screen spec and
   each planned asset is accepted, replaced by a user-provided asset, or
   explicitly waived by a durable user decision.

An opted-in user may explicitly waive the remaining visual stage, but that is a
recorded opt-out and BUILD must show the resulting missing-visual assumptions.
Provider failure, budget exhaustion, or unavailable modality never silently
becomes a placeholder asset: Vibey asks the user to retry, configure a provider,
upload an asset, or waive the visual stage.

### Provider-agnostic media generation and per-modality round robin

Application code owns a `MediaProvider` port with capability discovery and
idempotent operations such as `generate`, `poll_or_resume`, `download`,
`estimate_cost`, and `moderate`. A provider advertises one or more of:
`IMAGE`, `AUDIO`, and `VIDEO`, plus region, retention, input-reference,
asynchronous-job, safety, and output-format capabilities.

Provider selection is performed independently for each modality:

```text
eligible IMAGE providers → image cursor → next healthy provider
eligible AUDIO providers → audio cursor → next healthy provider
eligible VIDEO providers → video cursor → next healthy provider
```

Each cursor is persisted transactionally and advances only after a provider is
actually selected. Eligibility filters capability, user policy, region/data
residency, external-egress consent, budget, circuit state, and prompt/input
compatibility. A provider cannot be selected merely to make the fairness metric
look good, and one modality's cursor cannot starve another. Capacity exhaustion
and rate limits use the existing circuit/queue semantics; the worker parks for a
human or a provider window instead of sleeping while holding a lease.

Vibey should try a configured local/self-hosted provider first when
`media.mode = "local_first"`. Hosted providers are a fallback only when
`media.allow_external = true` and the user has seen the destination, retention,
cost, and data-handling terms. The initial registry may include OpenAI image/TTS,
Google Veo, Azure AI Foundry models, ElevenLabs, and future providers, but those
are examples discovered at runtime—not a fixed dependency or guarantee of
availability. If no eligible provider can satisfy a modality, the human gate is
the safe fallback.

Every generation records modality, provider, model/version, prompt digest,
reference-asset digests, seed/parameters when available, request/operation ID,
cost, output digest, retention policy, moderation result, and user decision.
Provider-specific API keys remain outside the ledger. Prompt and output content
is redacted where necessary and retains provenance so a later engine cannot treat
an external model's output as an instruction.

### Optional deployment choice

After Phase ③ REVIEW has no open product findings and the user accepts the build,
Vibey asks:

> “Do you want Vibey to work on Azure deployment for this run?”

- **No** records `DeploymentDeclined`, records `completion_mode = "local"`, and
  transitions to terminal `DONE`. No Azure discovery, preflight, `what-if`, or
  mutation job is enqueued. A later explicit deployment command may start a new
  deployment attempt from the accepted artifacts.
- **Yes** records `DeploymentOptedIn` and enters Phase ④ DEPLOY DESIGN. The
  existing ④–⑥ contract, consent guard, autonomous execution, verification, and
  demo rules from ADR-0013 apply unchanged.

Deployment opt-in is asked again after any delivery loop that changes the built
artifact or its acceptance criteria. A previous deployment consent cannot be
reused for a changed artifact, target, scope, environment, or recovery policy.

## Safety and quality gates

- Human confirmation is required for the visual plan and all required generated
  assets before opted-in BUILD begins.
- Visual review checks design-system consistency, contrast, keyboard/focus
  behavior, semantic labels, alt text, transcripts/captions, reduced motion, and
  screen-reader intent. AI-generated output is an accelerator, not a substitute
  for accessibility review.
- Generated media is scanned by an available content-safety provider before it is
  presented as accepted. A local or hosted provider's safety result is evidence,
  not a replacement for user review.
- Audio previews disclose that the voice is AI-generated where the selected
  provider requires it. Likeness, voice, copyrighted references, and uploaded
  source assets require user authority and policy checks.
- Generation, download, moderation, and preview are asynchronous, idempotent
  queue jobs. Large video jobs are never represented as a blocking worker call.
- Cost, token/character limits, file sizes, provider retention, and external
  egress are visible before the user opts in and enforced during execution.
- Build inputs use immutable, content-addressed visual artifacts. A later
  regeneration creates a new revision and never overwrites accepted evidence.

## Consequences

**Good.** Users can choose a fast spec-to-code path, a design-led multimodal path,
or a local-only completion path without changing the core safety guarantees.

**Good.** Media providers can be rotated, replaced, or disabled per modality as
  availability, pricing, regional policy, and model lifecycles change.

**Bad.** The phase graph, consent events, media manifest, provider registry,
  cursor persistence, artifact review, and test matrix become larger. The visual
  opt-in path and both deployment decisions need deterministic skip/accept tests.

**Bad.** A generated screen is not automatically a good screen. The plan must
  require a human design review and an independent accessibility/evidence pass.

## Research basis

- [OpenAI image and vision guide](https://developers.openai.com/api/docs/guides/images-vision)
  documents text/image input and image generation/editing, including the current
  GPT Image family.
- [OpenAI text-to-speech guide](https://developers.openai.com/api/docs/guides/text-to-speech)
  documents the speech endpoint and requires clear disclosure that the voice is
  AI-generated.
- [OpenAI video generation guide](https://developers.openai.com/api/docs/guides/video-generation)
  documents asynchronous video jobs but currently warns that the Sora 2 Videos
  API is scheduled to shut down on September 24, 2026; Vibey therefore must not
  hard-code it.
- [Google Veo generation documentation](https://ai.google.dev/gemini-api/docs/veo)
  documents long-running video operations, native generated audio, safety
  filtering, and SynthID watermarking.
- [Azure AI Foundry model catalog](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/concepts/models)
  documents image, video, and audio model families and warns that availability
  varies by region and cloud.
- [ElevenLabs text-to-speech API](https://elevenlabs.io/docs/api-reference/text-to-speech/convert)
  documents a provider-neutral audio fallback with model/voice selection and
  request/cost metadata.
- [Azure AI Content Safety](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview)
  documents image/text and AI-generated-content moderation capabilities.

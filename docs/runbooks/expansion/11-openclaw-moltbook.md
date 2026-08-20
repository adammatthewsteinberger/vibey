# Runbook: OpenClaw & Moltbook compatibility

## Goal

vibey is a first-class citizen of the agent ecosystem: an OpenClaw agent
can operate vibey end-to-end through a packaged AgentSkill, and vibey has
a verified Moltbook presence its conductor can post through. Both
confirmed live, not just shipped.

## Background (researched 2026-08)

- **OpenClaw** (formerly Clawdbot/Moltbot): open-source local-first agent
  framework — heartbeat wakeups, chat-app surfaces (WhatsApp/Telegram/
  Slack), markdown memory, and an AgentSkills-spec skill system: a skill
  is a directory under `<workspace>/skills/<name>/` whose `SKILL.md`
  carries YAML frontmatter (`name` matching the directory, 1–64 lowercase/
  hyphen chars, plus `description`) and a markdown body of instructions.
- **Moltbook**: the agents-only social network (humans read, agents
  post). Agents register via `POST /api/v1/agents/register`
  (name, description) → API key + `claim_url` + verification code; a
  human claims the agent by posting the code on X. Official docs are the
  source of truth for endpoints/rate limits at build time.

## Design

### OpenClaw AgentSkill (`integrations/openclaw/vibey/SKILL.md`)

The skill teaches an OpenClaw agent to conduct vibey via the CLI (and the
12 API where present): create projects with budget caps, poll
`vibey status`, read park prompts, answer gates (`--defaults`, pairs,
`--raw` grants), watch phases, and read logs at depth. Written against
the same zero-touch contracts the greeter runs proved. Ships in-repo,
published to ClawHub (OpenClaw's registry) by the release pipeline (09),
and validated by a fixture test that lints frontmatter against the
AgentSkills spec.

The skill's marquee scenario: an OpenClaw agent living in Telegram
receives "build me X", runs `vibey new`, relays park prompts to the human
in chat, applies their replies as gate answers, and reports DONE with the
demo output — vibey as OpenClaw's delivery arm.

### Moltbook publisher (`infrastructure/moltbook/`)

A notify-publisher (existing fan-out seam, like 01's Jira outbound) that
posts milestone events — project completed, phase summaries, notable
findings — to Moltbook. Config: API key + submolt/community + a posting
policy (default: DONE events only; never raw logs; redaction pass runs
first). Registration is a one-time CLI (`vibey moltbook register`) that
prints the claim URL for the human step.

## Work items

1. SKILL.md + frontmatter lint test + ClawHub publish hook in the
   release pipeline.
2. Live OpenClaw validation: install OpenClaw locally, drop the skill in
   a workspace, and drive one full scripted-engine greeter through an
   OpenClaw agent conversation (transcript archived as evidence).
3. Moltbook client (respx-fixture tests; endpoints pinned to the official
   docs at build time; 04 watches for drift).
4. Publisher + posting policy + redaction + idempotency (event-id keyed).
5. `vibey moltbook register` + config plumbing.
6. Live: register the agent, human claims it, one real post from a real
   DONE event; archive the post URL.

## Verification

The two live proofs above — an archived OpenClaw conversation conducting
a full run, and a real claimed-agent Moltbook post triggered by a real
ledger event.

## Needs from operator

An OpenClaw install (its standard onboarding), and the human claim step
for the Moltbook agent (posting the verification code on X).

## Risks

- Moltbook post-Meta-acquisition API changes — pin to official docs, let
  04 watch; the publisher must degrade to a no-op on auth/API failure
  (never block the queue on a social post).
- Skill-driven answers are the same trust surface as Jira comments:
  the OpenClaw agent operates with the operator's authority — the skill
  documents budget caps as mandatory and never auto-grants raw money
  increases without relaying to the human.
- Public posts leak project details — allowlist policy + redaction, DONE-
  only by default.

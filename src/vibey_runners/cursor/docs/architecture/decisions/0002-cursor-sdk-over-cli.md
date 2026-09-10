# Cursor Python SDK over the agent -p subprocess

- Status: Accepted
- Date: 2026-08-13

## Context
Autonomy needs a durable agent handle across turns. Scraping CLI streams is fragile.

## Decision
Primary AgentGateway uses cursor-sdk (`Agent.create` / `send` / `resume`). `agent -p` is an optional M5 fallback proving the port.

## Consequences
Bridge binary availability is a doctor check; CLI-fallback covers environments without it.

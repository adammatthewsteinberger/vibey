# ADR 0010: conversation_id persisted with fsync; resume degrades to a seeded fresh conversation

## Status

Accepted (2026-08-13).

## Context

A crash between turn-complete and persist loses the vendor conversation.

## Decision

meta.json is written with fsync. Resume uses LocalAgentConfig(conversation_id=…). If the vendor conversation is gone, start fresh seeded with persisted plan.md. Never persist session_id=None over a known id.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.

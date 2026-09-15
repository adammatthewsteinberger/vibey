# Completion detection

"The agent says it's done" is not evidence — models emit confident summaries
mid-task. The loop requires agreement between independent signals before a
run is COMPLETE:

- **the verdict fence** — a structured final block the session must emit;
- **the done marker** — an explicit completion token in the output;
- **empty-turn soft-fail** — a turn that produces nothing counts against
  completion instead of toward it;
- **plan reconciliation** — the plan's items are checked against what the
  session actually reported doing.

Disagreement keeps the loop running (or fails it at a bound) rather than
declaring victory. And capacity always outranks completion: a "done" emitted
while the capacity verdict says the model was starved is recorded, not
believed — see [the run loop](../architecture/run-loop.md).

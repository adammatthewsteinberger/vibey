# The sovereignty stress test, 2026-08-30

This page is the permanent record of an escalation run against the local review
lane — the "sovereign" path that carries the work when the paid lane is unavailable.
It exists because the constants it measured now govern real decisions: the fit
calculus admits or defers against them, and the doctrine that says to know your
floor is only honest if the floor has actually been found.

Every number here was measured on one machine in one session. Nothing is modelled,
estimated, or carried over from documentation.

## What was run

A harness stepped concurrency upward, rung by rung, firing that many simultaneous
generations against `qwen2.5-coder:14b` through ollama. Each generation was a real
unit of work — an open issue triaged, or a real pull-request diff reviewed — drawn
from a pool of seven artifacts ranging from 2 KB to 22 KB. A rung was recorded, then
the next rung fired.

The rule for stopping: any rung under 50% success triggers a heal (probe the lane,
restart the runner if it is unresponsive), then a full retry. Two consecutive
sub-50% results is the break.

**Machine**: 24 GB memory, 10 cores, 7 GB paging space.
**Model**: `qwen2.5-coder:14b`, ~9.7–10.5 GB resident, context 5311 growing to 9390
under load.
**Deadline**: 900 s per generation.

## The measurements

| Concurrency | Succeeded | Success | p50 | max | Throughput | Free memory |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1/1 | 100% | 166 s | 166 s | 0.36/min | 11.6% |
| 2 | 2/2 | 100% | 118 s | 118 s | 0.99/min | 11.2% |
| 3 | 3/3 | 100% | 132 s | 180 s | 0.99/min | 9.3% |
| 4 | 4/4 | 100% | 154 s | 203 s | 1.17/min | 9.4% |
| 6 | 6/6 | 100% | 59 s | 206 s | 1.72/min | 11.1% |
| 8 | 8/8 | 100% | 191 s | 375 s | 1.27/min | 10.3% |
| 12 | 12/12 | 100% | 174 s | 464 s | 1.54/min | 9.4% |
| 16 | 16/16 | 100% | 440 s | 700 s | 1.37/min | 8.6% |
| 24 | 21/24 | 87.5% | 701 s | 900 s | 1.40/min | 8.8% |
| 32 | 30/32 | 93.8% | 292 s | 900 s | 2.00/min | 9.3% |
| 48 | 24/48 | 50.0% | 900 s | 901 s | 1.60/min | 8.9% |
| 64 | 40/64 | 62.5% | 555 s | 901 s | 2.66/min | 10.0% |
| 96 | 53/96 | 55.2% | 821 s | 901 s | **3.52/min** | 9.7% |
| 128 | 23/128 | **18.0%** | 901 s | 901 s | 1.53/min | 9.1% |

**Totals**: 444 generations attempted, 243 succeeded (54.7%), 2.18 hours of wall
clock, roughly 86.5 generation-hours of compute, about 0.1 kWh of electricity.

## The envelope

- **Up to 32 concurrent** — 94–100% success. This is the comfortable operating
  region, and it is far above anything routine work has asked for.
- **48 concurrent** — exactly 50% success, with the median generation finishing at
  900.4 s against a 900 s deadline. The capacity limit, landed on to within half a
  second.
- **96 concurrent** — 55% success and **peak useful throughput of 3.52/min**, nearly
  ten times the serial baseline.
- **128 concurrent** — collapse to 18%, and the first rung where throughput itself
  fell.

## What actually failed, and how

**Every failure in the entire run was a clean timeout** reporting *"local model
unreachable or timed out"*. Not one corrupt verdict, not one malformed JSON
response, not one silent stall. The lane sheds load loudly, which is the behaviour
the no-guarantees doctrine demands at the floor.

**Payload size determined survival.** Through 96-way concurrency, only large diffs
ever failed; the small issue payloads survived every rung without a single loss. At
128 the small payloads began failing too — the signature separating *payload-bound*
slowness from genuine capacity exhaustion.

**The runner crashed twice and recovered itself both times.** At rung 64 and again
during rung 128, `llama-server` died under context pressure and ollama restarted it
in roughly fifteen to twenty seconds, unprompted. Every generation in flight at that
instant was lost; the service itself was never down for longer than the restart.
The rung that crashed at 64 still returned 62.5% and set a throughput record.

**Memory was the eventual constraint, but only at the end.** Free memory oscillated
between 8.6% and 11.6% across the entire 128× concurrency range without collapsing.
Paging space told the truer story: it reached 99.1% during rung 128, and that is
where the crashes and the collapse coincide.

## The finding that matters most

At the break, the harness ran its heal and recorded exactly this:

> `lane responsive; no heal needed`

The daemon was answering in under two milliseconds. Nothing was broken. The system
was **healthy, up, and simply unable to do that much work in the time allowed** — so
the retry ran under conditions identical to the failure and failed identically.

This is the real shape of the limit. Self-healing can restart a dead runner; it
cannot manufacture capacity. Past the saturation point the only remedies are
reducing concurrency, extending the deadline, or adding hardware — and every one of
those is a decision a person makes, not an action a machine takes. The unrecoverable
state was not a crash. It was a healthy system meeting an impossible request, which
is precisely where the binding constraint stops being mechanical and becomes
governance.

## Corrections earned along the way

Three models were proposed during the run and falsified by the next rung. They are
recorded because the corrections are the result:

1. **"Two parallel slots."** Inferred at rung 3 from flat throughput; falsified at
   rung 6, where six generations cleared in the same wall time as four. The flat
   throughput was a payload artifact — that rung had added the largest diff.
2. **"Latency grows linearly, 22 s per added job."** Fitted at rungs 8–12; falsified
   at rung 16, which came in at 700 s against a 392 s prediction.
3. **"Superlinear, therefore rung 32 breaks."** Fitted at rung 16; falsified at rung
   32, which returned 93.8% at the *highest* throughput yet. Continuous batching
   means concurrent sequences share forward passes, so added load raises aggregate
   throughput rather than merely queueing — the queueing model was structurally
   wrong for this class of server.

The lasting correction: **admission should gate on payload size, not on concurrency
count.** Small work can be fired in very large batches safely; large work needs
lower concurrency or a longer deadline. Concurrency alone is the wrong variable, and
the fit calculus was adjusted accordingly.

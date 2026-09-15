---
name: browser-rendering-pipeline
description: "Use when working on or debugging how a page gets rendered: the HTML parser that must never fail and the DOM, the CSS cascade, selector matching and why it's backwards, style invalidation as the hard part, the rendering pipeline and its key data structures (DOM → style → layout → paint → composite), the layout algorithms (block, inline, flex, grid), the compositor and the GPU, the JavaScript engine (V8, JavaScriptCore, SpiderMonkey), bindings as the underestimated layer, and the event loop and rendering lifecycle."
---

# Browser Development: HTML Parsing and the DOM, CSS and Style, Layout, Paint, Compositing, and JavaScript Integration

> **Part 2 of 5** of the *Web Browser Development* reference (plugin `web-browser-development`), covering §4–§7. Sibling skills: `browser-engine-architecture-and-networking` (§0–§3), `browser-security-and-privacy` (§8–§9), `browser-extensions-platform-and-standards` (§10–§14), `browser-development-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `browser-development-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — architecture, algorithms, or a constraint every engine has
>   independently arrived at. Does not expire.
> - **[ENGINE]** — specific to Blink/Chromium, Gecko, WebKit, or Servo/Ladybird. Verify
>   against that project's source or docs.
> - **[CONTESTED]** — the vendors genuinely disagree, often because their business models
>   differ. Both cases given, including the commercial motive where it's load-bearing.
>
> **⚠️ GOTCHA** boxes mark the mistakes that produce security holes, jank, or
> compatibility breakage that can never be undone.
>
> **The two framings that organize everything below:**
> 1. **A browser is a hostile-input execution environment that must never say no.** It
>    runs untrusted code from anyone, on documents that are frequently malformed, and it
>    is not permitted to refuse or crash. Every architectural decision — the multi-process
>    model, the error-tolerant parser, the sandbox — descends from that.
> 2. **The web's compatibility constraint is stronger than any other platform's.** You
>    cannot break existing sites. Not the well-written ones, not the abandoned ones. This
>    is why the platform accretes and rarely subtracts, and why "just fix it properly"
>    is almost never available.

---

## §4. HTML Parsing and the DOM

### 4.1 The parser must never fail

**[DURABLE] The HTML parsing algorithm is fully specified, including error recovery, and
you must implement it exactly.** This is unusual and important: HTML is not a grammar you
can choose how to recover from. The spec defines a tokenizer state machine plus a tree
construction stage with ~23 "insertion modes," and it defines the correct output for
*every* malformed input — including the famous **"adoption agency algorithm"** for
mis-nested formatting tags.

**Why it's specified this way**: before HTML5, every engine recovered differently, so
malformed pages (which is most pages) rendered differently everywhere. The spec codified
what browsers already did. **Deviating from it is a compatibility bug, not a design
choice.**

Other parser realities:
- **Speculative/preload scanning** — while the main parser is blocked on a synchronous
  script, a second scanner races ahead to find subresources and start fetching them. A
  large real-world performance win.
- **`document.write`** — can inject content into the token stream mid-parse. It is the
  single ugliest constraint on parser architecture and the reason streaming parsers have to
  be re-entrant.
- **Scripts block by default**; `async` and `defer` change the ordering guarantees.
  Getting the ordering exactly right is required for compatibility.

### 4.2 The DOM

A mutable tree with live collections, mutation observers, ranges, and shadow trees.
Implementation concerns that dominate:
- **Memory layout and node size** — multiplied by hundreds of thousands of nodes.
- **Live `NodeList`s and `HTMLCollection`s** — must reflect mutations, which means either
  recomputing or maintaining invalidation. A classic performance trap for both engine and
  page author.
- **Shadow DOM** — encapsulation boundaries that affect selector matching, event
  retargeting, and style scoping. Each of those is real work.
- **The JS binding layer** (§7.2) is where a surprising fraction of the complexity lives.

---

## §5. CSS and Style

### 5.1 The cascade

**[DURABLE] Style resolution is: for each element, find every declaration that applies,
sort by the cascade, and produce a computed value for every property.** The cascade order
(later wins):
```
1. origin & importance   user-agent < user < author < animations
                         < author !important < user !important < UA !important
                         < transitions
2. cascade layers        (@layer — later layers win within the same origin)
3. specificity           (id, class/attr/pseudo-class, type/pseudo-element)
4. order of appearance
```
Then **inheritance** for inherited properties, then computed → used → actual values.

**⚠️ Specificity is not a single number.** It's a 3-tuple compared lexicographically —
`(1,0,0)` beats `(0,99,99)`. Implementations that pack it into an integer eventually
overflow on pathological selectors, and real sites contain pathological selectors.

### 5.2 Selector matching, and why it's backwards

**[DURABLE] Match selectors right-to-left.** Given `div.container > p a`, an engine starts
at the candidate `a` element and walks *up*, because matching left-to-right would require
descending the entire subtree of every `div.container`. This single fact explains most of
CSS performance advice.

Optimizations every engine implements: **bloom filters** for ancestor checks (cheap
"definitely not a match" rejection), **rule hashing** by rightmost simple selector
(id/class/tag buckets), **style sharing caches** for elements with identical inputs, and
**invalidation sets** — precomputed knowledge of which rules could possibly be affected by
a given class/attribute change, so a `classList.toggle` doesn't restyle the document.

**[ENGINE] Servo's Stylo** — parallel style resolution in Rust — is the notable
architectural departure, and it shipped in Firefox. Style is unusually parallelizable
because sibling subtrees are largely independent; layout is much less so.

### 5.3 Invalidation is the hard part

**[DURABLE] Computing style from scratch is easy. Knowing what to recompute when something
changes is where engines live or die.** A DOM mutation, a class change, a media-query
flip, a container resize, or a `:hover` must invalidate the minimum possible set. Getting
this wrong shows up as jank, not as incorrect rendering, which makes it hard to test and
easy to regress.

**Container queries and `:has()` made this dramatically harder** — both create
dependencies that flow *up* or *sideways* rather than down the tree, breaking the
assumption that style depends only on ancestors.

---

## §6. Layout, Paint, and Compositing

### 6.1 The rendering pipeline

**[ENGINE — Chromium's RenderingNG names the stages; every engine has equivalents]:**
```
ANIMATE    mutate computed styles and property trees over time
STYLE      apply CSS to the DOM → computed styles
LAYOUT     compute size and position → the IMMUTABLE FRAGMENT TREE
PRE-PAINT  compute property trees; invalidate display lists and texture tiles
SCROLL     update scroll offsets by mutating property trees
PAINT      compute a DISPLAY LIST describing how to raster
COMMIT     copy property trees and display lists to the compositor
LAYERIZE   group display items into composited layers  (CompositeAfterPaint)
RASTER     display list → GPU texture tiles
ACTIVATE / AGGREGATE / DRAW   assemble and execute the compositor frame on the GPU
```

**[DURABLE] The crucial property: stages can be skipped.** Animating `transform` or
`opacity`, and scrolling, mutate only property trees — so they skip style, layout,
pre-paint, and paint entirely and **run on the compositor thread**, never touching the main
thread. That is exactly why "animate transform/opacity, not width/height/top/left" is the
universal performance advice, and why an engine's threading architecture is a *developer-
facing* fact.

### 6.2 The key data structures

- **Fragment tree** — LayoutNG's output. **Immutable.** The predecessor was a single
  long-lived mutable tree where each node held both inputs (available size, float
  positions) and outputs (final geometry), dirtied and re-cleaned in place. Making layout
  results immutable is what made caching and incremental layout predictable — this is the
  single most instructive architectural lesson in modern rendering.
- **Property trees** — separate transform, clip, effect, and scroll hierarchies. They
  collapse the combinatorial complexity of nested effects into one structure usable at
  every pipeline stage, and they're what lets the compositor animate without the main
  thread.
- **Display lists and paint chunks** — the input to raster and layerization.
- **Compositor frames** — surfaces, render surfaces, and GPU texture tiles.
- **Frame trees** — local and remote nodes recording which document is in which renderer
  process (this is where Site Isolation meets rendering: a cross-site iframe is a *remote*
  frame, rendered elsewhere and composited in).

### 6.3 Layout algorithms

You must implement, correctly and interoperably: **block and inline** formatting contexts
(including floats, margin collapsing, and line breaking — the oldest and gnarliest code in
any engine), **flexbox**, **grid** (and **subgrid**), **tables** (an algorithm nobody
enjoys and everybody needs), **positioned layout**, **fragmentation** (multicol, print,
and page breaking), **writing modes** (vertical text, RTL — and these interact with
everything), and **text shaping** (HarfBuzz-class complexity: ligatures, bidi per UAX #9,
grapheme clusters, font fallback).

> **⚠️ GOTCHA — text is harder than layout.** Font fallback, shaping, bidi, line-breaking
> per UAX #14, and emoji sequences are collectively a larger correctness surface than the
> box algorithms, and getting them wrong is immediately visible to users in languages the
> implementers don't read.

### 6.4 The compositor and the GPU

**[DURABLE] Two threads, and the split is the whole design.** The **main thread** runs
JS, style, layout, and paint. The **compositor thread** handles scroll, composited
animations, and frame submission. If the main thread is blocked for 500 ms, scrolling
still works — that is the entire justification for the architecture's complexity.

- **Layerization** — deciding what gets its own texture. Too few layers means repainting on
  every animation frame; too many exhausts GPU memory. `will-change` is the author-facing
  hint, and it is routinely abused into the second failure mode.
- **Raster** — display list → texture tiles, on worker threads or the GPU (Skia; Chromium's
  newer path via Dawn/**WebGPU**-adjacent infrastructure). Tiling exists so you only raster
  what's near the viewport.
- **Frame budget**: **16.6 ms at 60 Hz, 8.3 ms at 120 Hz** — and that's the budget for
  *everything*, including the compositor's own work.
- **Checkerboarding** — when the compositor needs content that isn't rastered yet, it
  shows old content or a blank pattern rather than dropping the frame. Preferring a stale
  frame to a late frame is the correct trade and worth internalizing.
- **GPU process isolation** — GPU drivers are large, buggy, vendor-supplied C code.
  Running them in a separate sandboxed process is standard, and **Chromium is deploying
  MiracleObject on the GPU main thread specifically targeting up to ~90% of UAF
  vulnerabilities there**, deliberately trading localized runtime performance for temporal
  memory safety.

---

## §7. JavaScript Integration

### 7.1 The engine

V8 (Chromium), SpiderMonkey (Gecko, and Servo), JavaScriptCore (WebKit), LibJS (Ladybird).
All modern ones are **tiered**: interpreter → baseline JIT → optimizing JIT, with
type-feedback-driven speculation, guards, and **deoptimization** back to the interpreter
when a guard fails. **Hidden classes/shapes plus inline caches** are what make dynamic
property access fast, and are the biggest single idea in dynamic-language performance.

**⚠️ Note the design tension Ladybird surfaces:** it has argued for **no JIT**, on
security and complexity grounds — JITs are a huge exploit surface and require W^X gymnastics
— at an obvious performance cost. That's a real, live trade-off, not a settled question,
and it's the same trade Apple makes by restricting JIT entitlements on iOS.

### 7.2 Bindings — the underestimated layer

**[DURABLE] The DOM is C++; the DOM is also JavaScript objects. Reconciling those two
object models is a large, subtle subsystem.** WebIDL defines the interfaces; a code
generator produces the glue. The hard parts:
- **Cross-heap garbage collection cycles.** A DOM node references a JS event listener which
  closes over the DOM node. Neither collector alone can see the cycle. Solutions: Blink's
  **Oilpan** (tracing GC for C++ DOM objects, unified with V8's collector), Gecko's
  cycle collector. **Getting this wrong means leaking every page the user visits.**
- **Wrapper lifetime and identity** — the same DOM node must yield the same JS object every
  time.
- **Security checks on every cross-origin access** — a `window` reference across origins
  exposes a tiny allow-list, and every access must be checked.
- **The cost of crossing the boundary** is real; hot DOM APIs are why engines invest in
  fast paths.

### 7.3 The event loop and rendering lifecycle

**[DURABLE] Exactly one specification governs when things happen, and page-visible
behaviour depends on it:**
```
run a task (one macrotask: event, timer, network callback)
  → drain the MICROTASK queue completely (promises, MutationObserver)
    ⚠️ microtasks that enqueue microtasks can starve the loop forever
→ if it's time to render:
     run rAF callbacks
     run ResizeObserver / IntersectionObserver
     update rendering: style → layout → paint → commit
→ idle callbacks (requestIdleCallback) if time remains
```
**⚠️ Forced synchronous layout ("layout thrashing")** — reading a geometry property
(`offsetHeight`, `getBoundingClientRect`) after a write forces layout *immediately*,
mid-task. Interleaving reads and writes in a loop turns one layout into N. This is the
single most common page-performance bug, and the engine's only defence is to expose it in
DevTools.

**Scheduling** is now a first-class engine concern: task prioritization, `scheduler.yield()`,
`isInputPending`, long-task attribution, and — the metric that made all of this visible —
**INP** (Interaction to Next Paint), which measures the *full* interaction lifecycle rather
than just input delay.

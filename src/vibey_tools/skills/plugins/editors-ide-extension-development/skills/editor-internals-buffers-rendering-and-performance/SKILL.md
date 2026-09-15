---
name: editor-internals-buffers-rendering-and-performance
description: "Use when building an editor or diagnosing one that is slow: text buffer data structures from gap buffers to piece tables and ropes, rendering and viewport virtualisation, indexing and code intelligence, how the JetBrains platform differs, terminal UI programming, and the editor performance work — startup, large files, input latency — that decides whether an editor feels fast."
---

# Editors and IDEs: Text Buffer Data Structures, Rendering, Indexing, the JetBrains Platform, Terminal UI, and Editor Performance

> **Part 4 of 5** of the *Editors, IDEs and Extension Development* reference (plugin `editors-ide-extension-development`), covering §18–§23. Sibling skills: `editor-choosing-vim-neovim-and-emacs` (§0–§5), `editor-vscode-architecture-and-the-protocol-layer` (§6–§11), `editor-vscode-extension-development` (§12–§17), `editor-reference` (§24–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Modal editing, buffer data structures and the protocols are stable. Two areas moved. See §24 → `editor-reference` for the AI and agent layer in editors, and the editor landscape itself.

> **⚠️ The organizing insight, and it reframes the whole "editor wars" conversation:**
> ⚠️ **the important layer stopped being the editor and became the PROTOCOLS.** **In the
> 2010s each editor reimplemented completion, go-to-definition and highlighting for every
> language — an editors × languages problem.** ⚠️ **LSP and Tree-sitter collapsed that
> into editors + languages, which is why new editors can be competitive within a year and
> why "which editor" matters far less than it used to** (§9 → `editor-vscode-architecture-and-the-protocol-layer`).
>
> **Complements a programming-languages reference (parsing and compilers), a
> GitHub/Jira reference (the surrounding workflow), and a frontend reference (webview UI).**
>
> **⚠️ GOTCHA** boxes mark things that waste days — extension activation, buffer
> assumptions, and the performance traps.
>
> **The three ideas that organize this document:**
> 1. **⚠️ Editor choice is mostly preference; the protocol support is the substance**
>    (§9–§11 → `editor-vscode-architecture-and-the-protocol-layer`). **Ask what LSP and Tree-sitter integration looks like, not what the theme
>    looks like.**
> 2. **⚠️ Modal editing is a language, not a set of shortcuts** (§3 → `editor-choosing-vim-neovim-and-emacs`). **Operators compose
>    with motions and text objects — learning that grammar is the whole payoff, and
>    memorizing keybindings is the failure mode.**
> 3. **⚠️ Everything in an editor is a latency budget** (§18–§20). **Text buffers,
>    rendering and parsing are all solved problems whose solutions exist because naive
>    approaches feel slow at scale.**

---

## §18. ⚠️ Text Buffer Data Structures

**⚠️ The classic interview question that is also a real engineering decision. A naive
string is O(n) per edit and unusable at scale.**
```
⚠️ GAP BUFFER      a gap at the cursor; insertion at the gap is O(1),
   moving the gap is O(distance). ⚠️ Excellent for typing (edits cluster),
   poor for scattered edits. Emacs uses this
⚠️ PIECE TABLE     original buffer + append-only add buffer + a list of
   PIECES describing the current document as spans of each.
   ⚠️ Edits never mutate existing text — which gives cheap undo and
   natural change tracking. ⚠️ VS Code uses a piece table variant
⚠️ ROPE            balanced tree of string chunks. O(log n) insert, delete,
   index. ⚠️ Excellent for very large files and concurrent editing.
   Used by Zed (and its ancestors), xi, and several Rust editors
LINE ARRAY         simple, and O(n) for line insertion in the middle
```
> **⚠️ GOTCHA — the operations that decide the structure are not the ones people
> optimize.** ⚠️ **You need fast line-number ↔ offset conversion (for every LSP message,
> every diagnostic, every jump), fast slicing for rendering the visible region, and cheap
> snapshots for background work.** **⚠️ A structure with fast insert but O(n) line lookup
> will feel slow in ways profiling attributes to the wrong place.**

**⚠️ Encoding is a persistent trap**: ⚠️ **UTF-8 storage, UTF-16 offsets in LSP (§9 → `editor-vscode-architecture-and-the-protocol-layer`),
grapheme clusters for cursor movement, and code points for regex** — **four different
notions of "position," and mixing them produces bugs that only appear with emoji, CJK
text or combining characters.**

---

## §19. Rendering

**⚠️ Virtualization is mandatory**: ⚠️ **render only the visible lines plus a small
overscan.** **A 100k-line file must not create 100k DOM nodes or draw calls.**
**⚠️ The hard parts**: **variable-width glyphs and font metrics, ligatures, bidirectional
text, tabs vs spaces alignment, soft wrapping (⚠️ which breaks the clean line-number ↔
visual-row mapping and complicates everything downstream), and cursor/selection geometry.**
**⚠️ DOM vs GPU**: ⚠️ **VS Code renders in the DOM (with a canvas-based minimap); Zed
renders on the GPU with a custom framework, which is where its frame-rate claims come
from** (§24.2 → `editor-reference`). **⚠️ The tradeoff is accessibility and platform text-input integration —
DOM gets screen readers, IME and selection semantics largely for free, and a custom GPU
renderer must reimplement all of it.**
**⚠️ Input latency is the metric users actually feel** — **not throughput** — **and the
budget is roughly a frame.**

---

## §20. Indexing and Code Intelligence

**⚠️ How an IDE answers "find all references" across a million lines instantly.**
```
⚠️ SYMBOL INDEX     built on open/change, persisted across sessions
⚠️ INCREMENTAL      recompute only what a change invalidates — this is the
   whole ballgame. ⚠️ Salsa-style demand-driven computation with memoized
   queries and dependency tracking is the modern approach (rust-analyzer)
⚠️ LAZY / ON-DEMAND  don't fully analyze what nobody has asked about
FUZZY MATCHING      ⚠️ the scoring function is what makes a file-picker
   feel good or bad; consecutive-match and word-boundary bonuses matter
```
**⚠️ The JetBrains difference** (§21): ⚠️ **it builds and persists its own full semantic
model rather than delegating to a language server**, **which is why its refactorings and
cross-language analysis go deeper — and why indexing a large project takes visible time
and memory.** **That's the tradeoff, stated plainly.**

---

## §21. The JetBrains Platform

**⚠️ Plugin development targets the IntelliJ Platform, shared across IDEA, PyCharm,
WebStorm, GoLand, Rider and the rest.**
**Core concepts**: **PSI (Program Structure Interface — ⚠️ the semantic tree, richer than a
syntax tree), VFS (virtual file system), actions, inspections (⚠️ with quick-fixes),
intentions, run configurations, and extension points declared in `plugin.xml`.**
**⚠️ Built with Gradle via the IntelliJ Platform Gradle Plugin; distributed through the
JetBrains Marketplace.**
**⚠️ Honest comparison**: ⚠️ **the IntelliJ Platform is substantially more complex to learn
than the VS Code API and gives you access to a far richer semantic model.** **If your
plugin needs deep type-aware analysis or refactoring, that's the tradeoff you're buying.**

---

## §22. Terminal UI Programming

**⚠️ If you're building a terminal editor or TUI:**
**ANSI escape sequences, alternate screen buffer, raw mode, terminal capabilities
(terminfo), and ⚠️ the resize signal (SIGWINCH).**
**Libraries**: **ncurses, `crossterm`/`ratatui` (Rust), `bubbletea` (Go), `blessed`/`ink`
(Node), `prompt_toolkit`/`textual` (Python).**
**⚠️ The perennial gotchas**: ⚠️ **terminals vary enormously in capability; true-colour
support is inconsistent; wide (CJK) and zero-width characters break naive column
arithmetic; and mouse support requires explicit mode-setting and is inconsistently
implemented.**

---

## §23. Editor Performance

```
⚠️ STARTUP        lazy-load everything; measure with extension profiling
⚠️ INPUT LATENCY  the metric users feel. Budget ~one frame
⚠️ LARGE FILES    virtualize (§19); many editors degrade or disable
   features past a size threshold — that's a deliberate choice, not a bug
⚠️ EXTENSION COST  one badly-activated extension taxes every startup (§13)
⚠️ FILE WATCHERS  ⚠️ watching node_modules is the classic resource fire.
   Configure files.watcherExclude and search.exclude
⚠️ LANGUAGE SERVERS  usually the biggest memory consumer in a VS Code session
```
**⚠️ Diagnosing**: **"Developer: Show Running Extensions" and the startup performance view;
`--disable-extensions` to bisect; ⚠️ and process-level inspection, because the extension
host and each language server are separate processes and the memory attribution is not
where people look.**

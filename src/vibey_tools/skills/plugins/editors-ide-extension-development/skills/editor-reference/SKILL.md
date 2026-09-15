---
name: editor-reference
description: "Use when checking an editor anti-pattern or misconception, looking up a startup, latency or file-size figure, finding the resources, or needing a picker — plus the current state of the AI and agent layer in editors and the editor landscape. Companion to the other editors and IDEs skills."
---

# Editors and IDEs: What's Live, Anti-Patterns, Misconceptions, Numbers, and Resources

> **Part 5 of 5** of the *Editors, IDEs and Extension Development* reference (plugin `editors-ide-extension-development`), covering §24–§30. Sibling skills: `editor-choosing-vim-neovim-and-emacs` (§0–§5), `editor-vscode-architecture-and-the-protocol-layer` (§6–§11), `editor-vscode-extension-development` (§12–§17), `editor-internals-buffers-rendering-and-performance` (§18–§23). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Modal editing, buffer data structures and the protocols are stable. Two areas moved. See §24 for the AI and agent layer in editors, and the editor landscape itself.

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
> 3. **⚠️ Everything in an editor is a latency budget** (§18–§20 → `editor-internals-buffers-rendering-and-performance`). **Text buffers,
>    rendering and parsing are all solved problems whose solutions exist because naive
>    approaches feel slow at scale.**

---

## §24. What's Live — verified August 2026

### 24.1 ⚠️ The AI/agent layer became part of the editor platform
**⚠️ For extension authors this is the most consequential API change in years: the model
became a resource the editor exposes, not a feature one vendor owns.**

- **⚠️ Microsoft open-sourced the GitHub Copilot Chat extension under the MIT license**
  (announced at Build 2025, repository `microsoft/vscode-copilot-chat`), **exposing the
  full implementation of agent mode, what contextual data is sent to models, the system
  prompt design, and telemetry mechanisms.** ⚠️ **The stated rationale is worth noting:
  advances in LLMs reduced the value of proprietary prompting, keeping prompts secret is
  impractical against community reverse-engineering, and openness was judged better for
  security given increased targeting of developer tools.**
- **⚠️ Bring-your-own-key (BYOK) is now a first-class capability.** **Copilot Business and
  Enterprise users can use their own API keys for providers including Anthropic, Gemini,
  OpenAI, OpenRouter and Azure, plus local models via Ollama and Foundry Local
  (changelog dated 22 April 2026).** ⚠️ **BYOK models work anywhere in VS Code Chat
  including agent mode and custom agents; usage is billed by the provider and does NOT
  count against Copilot quotas; and code completions are excluded — they stay on Copilot
  infrastructure.** **⚠️ BYOK was subsequently extended to air-gapped environments.**
- **⚠️ The extension-facing surface is the Language Model Chat Provider API**, ⚠️ **which
  means an extension can CONTRIBUTE models to the editor's picker** — **this is what turns
  the model layer into an ecosystem rather than a product.**
- **⚠️ Agent infrastructure is now editor-level**: **an Agents window shipped to Stable as
  preview in May 2026; sessions hold conversation, workspace, changes and execution state
  so work can be paused and resumed; ⚠️ and worktree support lets Copilot, Claude or Codex
  sessions each work in an isolated copy of the repository.** **MCP servers are the
  documented way to extend agents with external tools.**

> **⚠️ GOTCHA — a versioning constraint that catches teams on locked-down VS Code
> versions.** ⚠️ **Copilot Chat releases in LOCKSTEP with VS Code because of deep UI
> integration: every new Copilot Chat version is only compatible with the newest VS Code
> release, and only the latest Copilot Chat gets the latest models** — **because even minor
> model upgrades require prompt changes in the extension.** **⚠️ If your organization pins
> VS Code versions, you are also pinning model access.**

**⚠️ And note the economics changed underneath** (see a GitHub/Jira reference §26.2):
⚠️ **Copilot moved from flat premium-request units to token-based AI Credits on 1 June
2026**, **which is why BYOK matters — it routes heavy usage to a provider you bill
directly.**

### 24.2 ⚠️ The editor landscape: dominance plus genuine new entrants
**⚠️ VS Code remains dominant and the surrounding field got materially more interesting.**

- **⚠️ Stack Overflow's 2025 survey (49,000+ respondents, 177 countries) put VS Code at
  75.9%**, **up from 73.6% in 2024** — ⚠️ **more than triple its nearest competitor.**
  **IntelliJ IDEA at 27.1%; ⚠️ among Java developers specifically, IntelliJ reportedly rose
  from 71% to 84%.** **⚠️ Terminal editors remain substantial: Vim 24.3%, Neovim 14%.**
- **⚠️ AI-native editors posted the fastest debuts recorded**: **Cursor entering at 17.9%,
  Claude Code at 9.7%, Zed at 7.3%, Windsurf at 4.9%.** ⚠️ **Cursor is a VS Code fork,
  which is itself the story — the extension ecosystem and the Monaco/workbench foundation
  made forking viable.**
- **⚠️ Zed is the substantive non-Electron entrant**: **built in Rust by Nathan Sobo
  (Atom co-creator) and Max Brunsfeld (Tree-sitter's creator), rendered on the GPU via a
  custom framework, GPL-3.0, with full LSP support for 80+ languages.** ⚠️ **Windows and
  Linux support reportedly matured in early 2026, which was its main practical gap.**
- **⚠️ Neovim 0.12 (reported March 2026) added a built-in plugin manager plus LSP and UI
  upgrades** — ⚠️ **continuing the pattern of absorbing into core what previously required
  plugins.** **Vim 9.2 (reported February 2026) added fuzzy completion, Wayland support
  and XDG config.**
- **⚠️ JetBrains discontinued Fleet in December 2025 after 3+ years in preview**, **reported
  replaced by an agent-first product; treat the successor's details as unsettled.**

> **⚠️ GOTCHA — the strategic point, and it's the §9 → `editor-vscode-architecture-and-the-protocol-layer`/§11 → `editor-vscode-architecture-and-the-protocol-layer` thesis confirmed.** ⚠️ **New
> editors are viable within a year or two precisely BECAUSE LSP and Tree-sitter exist.**
> **Helix and Zed baked both in from day one rather than reimplementing language support;
> Neovim shipped an LSP client in core from 0.5.** **⚠️ One 2026 analysis puts it directly:
> hooking into the standards is far cheaper than building a new editor.**
> **⚠️ The corollary for anyone building tooling: target the PROTOCOL, not an editor.**
> **A language server or a Tree-sitter grammar works everywhere; a VS Code extension works
> in VS Code and its forks.**

**⚠️ One protocol to watch, flagged as early**: **the Agent Client Protocol (ACP), debuted
by Zed in August 2025, is reported adopted during 2026 by JetBrains across IntelliJ and
PyCharm, by Google's Gemini CLI, and by GitHub's Copilot CLI, with a shared agent
registry and 25+ agents reported speaking it.** ⚠️ **It is being described as "the LSP of
AI coding," which is a strong claim from a young protocol** — **the LSP analogy is
plausible given the identical M×N problem shape, and I'd treat the adoption numbers as
reported rather than verified.**

---

## §25. Anti-Patterns

```
⚠️ "activationEvents": ["*"] — taxing every user's startup (§13)
⚠️ Not pushing disposables onto context.subscriptions (§12)
⚠️ Building custom UI in a webview when a tree view or quick pick would do (§15)
⚠️ Hardcoded colours in a webview instead of --vscode-* variables (§15)
⚠️ Writing files directly instead of a WorkspaceEdit — breaks undo (§14)
⚠️ Assuming the extension host is local — it isn't over SSH/containers (§8)
⚠️ Putting all logic behind the vscode API, making it untestable (§17)
⚠️ Ignoring cancellation tokens in a language server (§9, §16)
⚠️ Assuming byte offsets where LSP specifies UTF-16 code units (§9, §18)
⚠️ A parser that fails on incomplete code — code is broken while typed (§11, §16)
⚠️ Regex where Tree-sitter queries or ast-grep would be structural (§11)
⚠️ Naive string buffer; O(n) line lookup (§18)
⚠️ Rendering all lines instead of virtualizing (§19)
⚠️ Watching node_modules (§23)
⚠️ Publishing only to the Microsoft Marketplace if you want reach (§17)
⚠️ Memorizing vim keybindings instead of learning the grammar (§3)
⚠️ Infinite editor-config tinkering as a substitute for work (§4)
```

---

## §26. Misconceptions

| Misconception | Correction |
|---|---|
| Which editor you use determines your language support | ⚠️ **The language SERVER does** (§9 → `editor-vscode-architecture-and-the-protocol-layer`) |
| Vim is about memorizing shortcuts | ⚠️ **It's operator + motion/text-object grammar** (§3 → `editor-choosing-vim-neovim-and-emacs`) |
| Vim's `y` register survives a delete | ⚠️ **Use `"0` — the yank register** (§3 → `editor-choosing-vim-neovim-and-emacs`) |
| Neovim is Vim with a different name | ⚠️ **Built-in LSP, Tree-sitter, Lua, real async** (§4 → `editor-choosing-vim-neovim-and-emacs`, §24.2) |
| Extensions can manipulate VS Code's DOM | ⚠️ **Separate process. Use contributions or a webview** (§6 → `editor-vscode-architecture-and-the-protocol-layer`) |
| Monaco = embeddable VS Code | ⚠️ **The editor widget only; no workbench or extensions** (§6 → `editor-vscode-architecture-and-the-protocol-layer`) |
| VS Code extensions always run locally | ⚠️ **The host runs on the remote** (§8 → `editor-vscode-architecture-and-the-protocol-layer`) |
| Syntax highlighting needs regex grammars | ⚠️ **Tree-sitter parses structure** (§11 → `editor-vscode-architecture-and-the-protocol-layer`) |
| Tree-sitter can replace a language server | ⚠️ **Syntax vs semantics. You need both** (§11 → `editor-vscode-architecture-and-the-protocol-layer`) |
| LSP positions are byte offsets | ⚠️ **UTF-16 code units by default** (§9 → `editor-vscode-architecture-and-the-protocol-layer`) |
| A parser can assume valid input | ⚠️ **Code is invalid most of the time while typing** (§11 → `editor-vscode-architecture-and-the-protocol-layer`, §16 → `editor-vscode-extension-development`) |
| A text buffer can be a string | ⚠️ **O(n) edits; use rope/piece table/gap buffer** (§18 → `editor-internals-buffers-rendering-and-performance`) |
| Piece tables are exotic | ⚠️ **VS Code uses one** (§18 → `editor-internals-buffers-rendering-and-performance`) |
| Extensions can't slow startup much | ⚠️ **Activation events are the top complaint source** (§13 → `editor-vscode-extension-development`) |
| Cursor is a from-scratch editor | ⚠️ **A VS Code fork** (§24.2) |
| VS Code is losing to AI editors | ⚠️ **75.9% and rising; the entrants grew the field** (§24.2) |
| Copilot Chat is closed source | ⚠️ **MIT-licensed since 2025** (§24.1) |
| You must use Copilot's models in VS Code | ⚠️ **BYOK, including local models** (§24.1) |
| Pinning VS Code versions is harmless | ⚠️ **It pins your model access too** (§24.1) |

---

## §27. Numbers

```
⚠️ VS Code usage (SO 2025, n>49,000)   75.9% (73.6% in 2024)
⚠️ IntelliJ IDEA 27.1% · Vim 24.3% · Neovim 14%
⚠️ AI-native debuts  Cursor 17.9% · Claude Code 9.7% · Zed 7.3% · Windsurf 4.9%
⚠️ Zed LSP language support  80+
⚠️ LSP transport  JSON-RPC over stdio; positions in UTF-16 code units
⚠️ Buffer structures  gap buffer (Emacs) · piece table (VS Code) · rope (Zed)
⚠️ Input latency budget  ~one frame
⚠️ Copilot AI Credits billing  from 1 June 2026
⚠️ ACP debut Aug 2025; reported 25+ agents by 2026
```

---

## §28. Resources

| Source | Why |
|---|---|
| **VS Code Extension API docs** | ⚠️ **Genuinely excellent — start here, not with a tutorial** |
| **`microsoft/vscode-extension-samples`** | ⚠️ **The fastest way to learn a contribution point** |
| **LSP specification (microsoft.github.io/language-server-protocol)** | §9 → `editor-vscode-architecture-and-the-protocol-layer` |
| **DAP specification** | §10 → `editor-vscode-architecture-and-the-protocol-layer` |
| **Tree-sitter docs + playground** | ⚠️ **The query playground is the best way to learn queries** |
| **`rust-analyzer` architecture docs** | ⚠️ **§16 → `editor-vscode-extension-development`, §20 → `editor-internals-buffers-rendering-and-performance`. The best writing on incremental analysis** |
| **VS Code's "Text Buffer Reimplementation" blog post** | ⚠️ **§18 → `editor-internals-buffers-rendering-and-performance`, with real measurements** |
| **`microsoft/vscode-copilot-chat`** | ⚠️ **§24.1 — read a real agent implementation** |
| **IntelliJ Platform SDK docs** | §21 → `editor-internals-buffers-rendering-and-performance` |
| **`vimtutor`** (ships with vim) | ⚠️ **30 minutes, and the correct starting point** |
| **`:help` in vim, `:h lsp` in neovim** | ⚠️ **Vim's built-in docs are unusually good** |
| **Open VSX** | §17 → `editor-vscode-extension-development`'s other registry |

---

## §29. Quick Reference

### 29.1 Picker
| Question | Where |
|---|---|
| I'm stuck in vim | ⚠️ **`Esc` then `:q!`** (§3 → `editor-choosing-vim-neovim-and-emacs`) |
| How do I get good at vim? | ⚠️ **Learn operator+motion+text-object, not keys** (§3 → `editor-choosing-vim-neovim-and-emacs`) |
| Vim or Neovim? | ⚠️ **Neovim unless you need bare-server portability** (§4 → `editor-choosing-vim-neovim-and-emacs`, §24.2) |
| Language support is bad in my editor | ⚠️ **It's the language server, not the editor** (§9 → `editor-vscode-architecture-and-the-protocol-layer`) |
| Building tooling — which editor to target? | ⚠️ **Target the PROTOCOL** (§24.2) |
| Syntax highlighting or structural search | ⚠️ **Tree-sitter / ast-grep** (§11 → `editor-vscode-architecture-and-the-protocol-layer`) |
| Cross-project semantics | ⚠️ **LSP** (§9 → `editor-vscode-architecture-and-the-protocol-layer`) |
| VS Code is slow to start | ⚠️ **Show Running Extensions; check activation** (§13 → `editor-vscode-extension-development`, §23 → `editor-internals-buffers-rendering-and-performance`) |
| Extension needs custom UI | ⚠️ **Native contributions first; webview last** (§15 → `editor-vscode-extension-development`) |
| Simple language feature, one language | ⚠️ **In-process provider** (§14 → `editor-vscode-extension-development`) |
| Heavy analysis or non-Node toolchain | ⚠️ **Write a language server** (§16 → `editor-vscode-extension-development`) |
| Extension breaks over SSH | ⚠️ **Check `extensionKind` and path assumptions** (§8 → `editor-vscode-architecture-and-the-protocol-layer`) |
| Building an editor — buffer choice? | ⚠️ **Rope or piece table; check line lookup cost** (§18 → `editor-internals-buffers-rendering-and-performance`) |
| Want a different model in VS Code | ⚠️ **BYOK** (§24.1) |

### 29.2 Extension checklist
- [ ] ⚠️ **Narrow activation events; startup cost measured** (§13 → `editor-vscode-extension-development`)
- [ ] ⚠️ **Every disposable pushed to `context.subscriptions`** (§12 → `editor-vscode-extension-development`)
- [ ] Logic separated from the `vscode` API for testability (§17 → `editor-vscode-extension-development`)
- [ ] ⚠️ **Works when the extension host is remote** (§8 → `editor-vscode-architecture-and-the-protocol-layer`)
- [ ] `WorkspaceEdit` for file changes, not direct writes (§14 → `editor-vscode-extension-development`)
- [ ] Webview: CSP, nonce, `asWebviewUri`, theme variables (§15 → `editor-vscode-extension-development`)
- [ ] ⚠️ **Cancellation tokens honoured; requests debounced** (§9 → `editor-vscode-architecture-and-the-protocol-layer`)
- [ ] `engines.vscode` accurate; `.vscodeignore` trimmed (§12 → `editor-vscode-extension-development`, §17 → `editor-vscode-extension-development`)
- [ ] ⚠️ **Published to Open VSX as well, if reach matters** (§17 → `editor-vscode-extension-development`)

---

## §30. Method

**§1–§23 → `editor-choosing-vim-neovim-and-emacs`, `editor-vscode-architecture-and-the-protocol-layer`, `editor-vscode-extension-development`, `editor-internals-buffers-rendering-and-performance` rests on stable material** — **modal editing, the VS Code process model, the LSP
and DAP specifications, Tree-sitter, buffer data structures and rendering.** ⚠️ **The
protocols have been stable for years and the buffer structures are decades old; none of it
needed verification.**

**Two searches were run in August 2026**, on **the AI/agent layer in VS Code** and **the
editor landscape** — ⚠️ **the first because it introduced genuinely new extension APIs, the
second because the competitive picture changed enough to affect what you target.**

**Confidence.** **High** in §9 → `editor-vscode-architecture-and-the-protocol-layer` and §11 → `editor-vscode-architecture-and-the-protocol-layer`, and the protocol framing in the header is the
argument I'd most defend: ⚠️ **the shift from editors × languages to editors + languages is
the structural change that explains why new editors are viable, why editor choice matters
less, and why tooling should target protocols.** **One 2026 analysis states it directly —
hooking into the standards is cheaper than building a new editor — and Helix, Zed and
Neovim all demonstrate it.**

**High** in §12–§17 → `editor-vscode-extension-development`'s extension mechanics and §18 → `editor-internals-buffers-rendering-and-performance`'s buffer structures, which come from
primary documentation and are long-stable.

**High** in §24.1's facts, which trace to GitHub's own changelog and VS Code's blog:
⚠️ **the MIT open-sourcing of Copilot Chat, the BYOK provider list and its exclusion of
code completions, the Language Model Chat Provider API, and the lockstep versioning
constraint are all from primary sources.** **The lockstep point is from the repository's
own README and is the one I'd most want a reader on a pinned VS Code version to see.**

**Moderate-to-high** in §24.2's numbers. ⚠️ **The Stack Overflow figures (VS Code 75.9%,
IntelliJ 27.1%, Vim 24.3%, Neovim 14%) and the AI-native debut percentages come from
secondary reporting of the survey rather than from the survey directly in my results, and
different sources cite 2024 vs 2025 waves — I've dated them and would verify against
Stack Overflow's own publication before quoting.** **⚠️ The Neovim 0.12 and Vim 9.2 release
details come from an aggregator and are marked as reported.**

⚠️ **ACP is deliberately flagged as early and reported rather than established.** **The
adoption claims (JetBrains, Gemini CLI, Copilot CLI, 25+ agents, shared registry) come
from a single tech-analysis source.** **The "LSP of AI coding" framing is plausible — the
M×N problem shape is identical — but a protocol roughly a year old is not yet a standard,
and I'd rather say that than repeat the marketing.** ⚠️ **Sourcing caution generally: much
of the editor-comparison material comes from review sites and tool directories with
affiliate relationships; I anchored on primary changelogs and specifications wherever the
claim mattered.**

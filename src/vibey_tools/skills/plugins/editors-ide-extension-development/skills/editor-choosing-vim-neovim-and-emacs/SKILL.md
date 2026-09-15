---
name: editor-choosing-vim-neovim-and-emacs
description: "Use when learning or configuring a terminal editor, or when someone asks which editor to use: choosing honestly rather than by tribe, nano and the cases it fits, vim's actual model of operators, motions, text objects and counts as a composable grammar, configuring vim and Neovim including Lua configuration and plugin managers, and what Emacs is and why its users stay. Includes the router for the whole editors and IDEs reference."
---

# Editors and IDEs: Choosing an Editor, nano, Vim's Actual Model, Configuring Vim and Neovim, and Emacs

> **Part 1 of 5** of the *Editors, IDEs and Extension Development* reference (plugin `editors-ide-extension-development`), covering §0–§5. Sibling skills: `editor-vscode-architecture-and-the-protocol-layer` (§6–§11), `editor-vscode-extension-development` (§12–§17), `editor-internals-buffers-rendering-and-performance` (§18–§23), `editor-reference` (§24–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ Modal editing is a language, not a set of shortcuts** (§3). **Operators compose
>    with motions and text objects — learning that grammar is the whole payoff, and
>    memorizing keybindings is the failure mode.**
> 3. **⚠️ Everything in an editor is a latency budget** (§18–§20 → `editor-internals-buffers-rendering-and-performance`). **Text buffers,
>    rendering and parsing are all solved problems whose solutions exist because naive
>    approaches feel slow at scale.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| Editor selection, honestly | §1 |
| nano | §2 |
| **⚠️ vim/neovim's model** | **§3** |
| Configuring vim | §4 |
| Emacs | §5 |
| **VS Code architecture** | **§6 → `editor-vscode-architecture-and-the-protocol-layer`** |
| Config and workspaces | §7 → `editor-vscode-architecture-and-the-protocol-layer` |
| Remote development | §8 → `editor-vscode-architecture-and-the-protocol-layer` |
| **⚠️ LSP** | **§9 → `editor-vscode-architecture-and-the-protocol-layer`** |
| DAP | §10 → `editor-vscode-architecture-and-the-protocol-layer` |
| **Tree-sitter** | **§11 → `editor-vscode-architecture-and-the-protocol-layer`** |
| **⚠️ Extension anatomy** | **§12 → `editor-vscode-extension-development`** |
| Contribution points and activation | §13 → `editor-vscode-extension-development` |
| API surfaces | §14 → `editor-vscode-extension-development` |
| Webviews | §15 → `editor-vscode-extension-development` |
| **Writing a language server** | **§16 → `editor-vscode-extension-development`** |
| Publishing | §17 → `editor-vscode-extension-development` |
| **⚠️ Text buffer data structures** | **§18 → `editor-internals-buffers-rendering-and-performance`** |
| Rendering | §19 → `editor-internals-buffers-rendering-and-performance` |
| Indexing and code intelligence | §20 → `editor-internals-buffers-rendering-and-performance` |
| JetBrains platform | §21 → `editor-internals-buffers-rendering-and-performance` |
| Terminal UI | §22 → `editor-internals-buffers-rendering-and-performance` |
| Editor performance | §23 → `editor-internals-buffers-rendering-and-performance` |
| **What's live** | **§24 → `editor-reference`** |
| Anti-patterns, misconceptions | §25–§26 → `editor-reference` |
| Numbers, resources, quick ref | §27–§29 → `editor-reference` |

---

## §1. Choosing, Honestly

```
⚠️ nano        always present, zero learning curve. ⚠️ Know it because you
   WILL land in it on a strange server (§2)
⚠️ vim         ⚠️ ubiquitous on servers. Learn enough to survive regardless
   of your daily editor
⚠️ neovim      the modern fork: Lua config, built-in LSP and Tree-sitter (§24.2)
EMACS          ⚠️ an elisp environment that edits text. Unmatched at Org-mode
   and Magit; a lifestyle commitment
⚠️ VS Code     the default. Enormous extension ecosystem, Electron cost
JETBRAINS      ⚠️ deepest static analysis and refactoring, per-language IDEs
ZED / HELIX    newer, native, protocol-first (§24.2)
SUBLIME        fast, proprietary, small curated ecosystem
```
> **⚠️ GOTCHA — most editor arguments are about preference dressed as objectivity.**
> ⚠️ **What genuinely differs: the depth of static analysis (JetBrains still leads for
> large typed codebases because it builds its own semantic model rather than delegating to
> a language server), resource usage, extension ecosystem size, and how much configuration
> you must do before it's useful.** **⚠️ Everything else — speed of typing, "power" — is
> mostly familiarity.**
> **⚠️ The one non-negotiable: learn basic vim.** **Not as a lifestyle — because `vi` is on
> essentially every Unix system and you will eventually need to edit a config file on a box
> with nothing else** (§3).

---

# PART I — TERMINAL EDITORS

## §2. nano

**⚠️ Underrated for exactly one reason: it tells you the keybindings at the bottom of the
screen, which makes it the correct choice when someone else needs to edit a file.**
```
^O  write out (save)      ^X  exit          ^K  cut line     ^U  paste
^W  search                ^\  replace       ^G  help         M-U undo
⚠️ ^ means Ctrl, M- means Alt/Meta — the display convention confuses people
```
**⚠️ Worth knowing**: **`nano -w` disables line wrapping (⚠️ important when editing config
files where a wrapped long line becomes a broken long line), and `nano +N file` opens at
line N.**
**⚠️ `/etc/nanorc` for syntax highlighting**; ⚠️ **and on many systems `nano` is what
`EDITOR` points at, which is what `visudo` and `git commit` will use.**

---

## §3. ⚠️ Vim's Actual Model

**⚠️ The thing to understand: vim is a LANGUAGE with a grammar, not a set of shortcuts.**
```
⚠️ OPERATOR + [COUNT] + MOTION-OR-TEXT-OBJECT
   d (delete) · c (change) · y (yank) · > (indent) · gu/gU (case) · = (format)
```
**⚠️ Motions**: **`w` word, `b` back, `e` end, `0` line start, `^` first non-blank,
`$` end, `gg`/`G` file start/end, `}`/`{` paragraph, `f<char>`/`t<char>` find/till on
line, `%` matching bracket.**
**⚠️ TEXT OBJECTS are the part people miss and the part that pays:**
```
⚠️ i = "inner", a = "a/around" (includes delimiters)
   ciw  change inner word          ci"  change inside quotes
   ci(  change inside parens       dap  delete a paragraph
   dit  delete inside HTML tag     ya{  yank a block with braces
⚠️ These work from ANYWHERE in the object — you don't position first
```
⚠️ **Learn the composition and you get combinations you were never taught.** **`d` +
`i` + `(` is not a memorized shortcut — it's the grammar producing a result.**

**⚠️ Modes**: **Normal (default — ⚠️ vim is a normal-mode editor that occasionally lets you
insert), Insert, Visual (char/line/block), Command-line, Replace.**
**⚠️ Registers**: ⚠️ **`"a`–`"z` named, `""` unnamed (the default), `"0` last yank
(survives deletes — which is the fix for "I deleted something and lost my copy"), `"+`
system clipboard, `"%` filename.**
**⚠️ Survival minimum for the server-at-3am case:**
```
i  insert    Esc  normal    :w  write    :q  quit    :wq  both
⚠️ :q!  quit without saving  ← THE one people need and don't know
dd  delete line    u  undo    Ctrl-r  redo    /text  search    n  next
```
**⚠️ Macros are underused**: **`qa` record into register a, `q` stop, `@a` play, `@@`
repeat, `10@a` ten times.** ⚠️ **A recorded macro beats a hand-written regex for most
repetitive edits, and it's testable one step at a time.**
**⚠️ The dot command `.` repeats the last change** — **and structuring edits so `.` can
repeat them is the actual expert skill.**

---

## §4. Configuring Vim and Neovim

```
VIM        ~/.vimrc, Vimscript (⚠️ Vim9script in Vim 9)
⚠️ NEOVIM  ~/.config/nvim/init.lua, LUA. ⚠️ Faster, saner, better tooling
```
**⚠️ Neovim's structural advantages over Vim** (§24.2 → `editor-reference`): ⚠️ **a built-in LSP client, built-in
Tree-sitter, Lua config and plugins, real async, and a plugin ecosystem that increasingly
targets Neovim exclusively.**
**⚠️ The modern Neovim stack**: **`lazy.nvim` (plugin manager), `nvim-lspconfig` +
`mason.nvim` (language servers), `nvim-treesitter`, `telescope.nvim` (fuzzy finding),
`gitsigns.nvim`.**
**⚠️ Distributions — LazyVim, NvChad, AstroNvim, kickstart.nvim** — ⚠️ **flatten the
on-ramp enormously, and the tradeoff is that you inherit someone else's decisions and
debug their abstractions.** **`kickstart.nvim` is the honest middle: a single readable
file you're expected to modify.**
**⚠️ The config trap worth naming**: ⚠️ **time spent configuring the editor is not time
spent working**, **and "endless config tinkering" is a recognized failure mode for
exactly the personality that enjoys vim.** **Set a budget.**

---

## §5. Emacs

**⚠️ Not really a text editor — a Lisp environment with an editor bundled.** **That's why
it can host a mail client, a Git porcelain and an outliner as first-class citizens.**
**⚠️ What genuinely has no equivalent elsewhere**: ⚠️ **Magit (widely considered the best
Git interface in any editor, by a margin) and Org-mode (outlining, literate programming,
task management, publishing).** **Those two are the honest reasons to use Emacs.**
**Modern practice**: **Doom Emacs and Spacemacs (⚠️ with vim keybindings via Evil, which is
what most vim-users-in-Emacs actually do), `use-package`, and native compilation for
performance.**
**⚠️ The cost is real**: **a genuine learning investment, and the keybinding conventions
predate and conflict with every modern convention.**

---

# PART II — VS CODE

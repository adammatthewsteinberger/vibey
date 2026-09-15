---
name: editor-vscode-extension-development
description: "Use when building a VS Code extension end to end: the anatomy of an extension and its manifest, contribution points and activation events, the API surfaces for commands, editors, tasks and tree views, webviews with their message passing and content security constraints, writing a language server, and testing and publishing to the marketplace."
---

# Editors and IDEs: Anatomy of a VS Code Extension, Contribution Points, API Surfaces, Webviews, Writing a Language Server, and Publishing

> **Part 3 of 5** of the *Editors, IDEs and Extension Development* reference (plugin `editors-ide-extension-development`), covering §12–§17. Sibling skills: `editor-choosing-vim-neovim-and-emacs` (§0–§5), `editor-vscode-architecture-and-the-protocol-layer` (§6–§11), `editor-internals-buffers-rendering-and-performance` (§18–§23), `editor-reference` (§24–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ Everything in an editor is a latency budget** (§18–§20 → `editor-internals-buffers-rendering-and-performance`). **Text buffers,
>    rendering and parsing are all solved problems whose solutions exist because naive
>    approaches feel slow at scale.**

---

## §12. ⚠️ Anatomy of a VS Code Extension

```
my-extension/
├── package.json        ⚠️ THE MANIFEST — contributions, activation, engines
├── src/extension.ts    activate() and deactivate()
├── tsconfig.json
└── .vscodeignore       ⚠️ what to exclude from the package
```
```typescript
export function activate(context: vscode.ExtensionContext) {
  const d = vscode.commands.registerCommand('ext.hello', () => {
    vscode.window.showInformationMessage('Hello');
  });
  // ⚠️ ALWAYS push disposables — this is the leak everyone creates
  context.subscriptions.push(d);
}
export function deactivate() {}
```
**⚠️ Scaffold with `yo code`; develop by pressing F5, which launches an Extension
Development Host window with your extension loaded.**
**⚠️ The disposable pattern is not optional**: ⚠️ **every registration, listener, and
watcher returns a Disposable, and anything not pushed onto `context.subscriptions` leaks
across reloads** — **which shows up as duplicate handlers firing, not as a memory warning.**

---

## §13. Contribution Points and Activation

**⚠️ Contributions are DECLARATIVE — declared in `package.json`, not registered in code:**
```
commands · menus · keybindings · configuration · languages · grammars ·
snippets · themes · views / viewsContainers · problemMatchers ·
debuggers · taskDefinitions · customEditors · walkthroughs
```
> **⚠️ GOTCHA — activation events are the #1 extension performance mistake, and users feel
> it as "VS Code is slow to start."** ⚠️ **`"activationEvents": ["*"]` activates your
> extension on every startup regardless of relevance.** **⚠️ Use the narrowest trigger:
> `onLanguage:python`, `onCommand:...`, `workspaceContains:**/pyproject.toml`,
> `onView:...`.**
> **⚠️ Modern VS Code infers many activation events automatically from your contributions**
> — **a declared command implies `onCommand` — so the explicit list is often unnecessary.**
> **⚠️ Check your startup cost with the built-in "Developer: Show Running Extensions."**

**⚠️ `when` clauses** control menu and keybinding visibility (`editorLangId == python &&
editorHasSelection`), ⚠️ **and custom context keys via `setContext` let you drive UI state
from your own logic.**

---

## §14. API Surfaces

```
window      ⚠️ messages, quick pick, input box, status bar, output channel,
            terminals, editors, webviews, progress
workspace   ⚠️ folders, file system, configuration, text documents,
            FILE SYSTEM WATCHERS, edits
languages   ⚠️ register providers: completion, hover, definition, code
            actions, formatting, diagnostics. ⚠️ Use these instead of an
            LSP server for simple, single-language, in-process features
commands    register and execute (⚠️ including built-in commands)
debug · tasks · extensions · env · authentication · lm (§24.1)
```
**⚠️ Choosing between in-process providers and a language server** (§16): ⚠️ **in-process
is simpler and locks you to VS Code and to Node; an LSP server is more work and runs
anywhere, in any language, in its own process.** **⚠️ If the analysis is heavy or the
language has an existing toolchain in another language, write a server.**
**⚠️ `WorkspaceEdit`** is how you make multi-file changes atomically with undo support —
⚠️ **don't write files directly when a WorkspaceEdit will do, because direct writes break
undo and don't participate in refactoring previews.**

---

## §15. Webviews

**⚠️ An isolated iframe for custom UI, with a `postMessage` bridge.**
```
⚠️ SECURITY  set a Content-Security-Policy; use a nonce for scripts;
   ⚠️ use webview.asWebviewUri() for local resources — plain file paths
   will not load
STATE        ⚠️ getState/setState, or retainContextWhenHidden (expensive)
   — webviews are DISPOSED when hidden by default
THEMING      ⚠️ use the CSS variables VS Code injects (--vscode-*) so your
   UI follows the user's theme. Hardcoded colours look broken in half of them
```
**⚠️ The judgement call**: ⚠️ **webviews are heavy and step outside the native UI, so
prefer native contributions (tree views, quick picks, status bar) where they'll do.**
**⚠️ Custom editors and notebook APIs exist for document-shaped and cell-shaped UI
respectively, and are usually better than a hand-rolled webview for those cases.**

---

## §16. Writing a Language Server

**⚠️ The practical path — use the SDK for your language:**
```
Node/TS   vscode-languageserver / vscode-languageclient
Rust      tower-lsp
Python    pygls
Go        go.lsp / gopls internals as reference
```
**⚠️ Minimum viable server**: **initialize handshake declaring capabilities → document
sync → publish diagnostics on change → completion → hover.** ⚠️ **Diagnostics first: it's
the highest-value feature and doesn't require the user to ask for anything.**
**⚠️ Architecture that works** (§11 → `editor-vscode-architecture-and-the-protocol-layer`): ⚠️ **parse incrementally and error-tolerantly, keep a
document store keyed by URI, debounce analysis, honour cancellation, and separate the
syntactic layer (fast, per-file) from the semantic layer (slow, project-wide).**
**⚠️ The hardest parts, in order**: ⚠️ **incremental re-analysis without re-doing the whole
project, resolving imports and building a project model, cancellation and concurrency, and
graceful degradation when the project doesn't build.**
**⚠️ rust-analyzer is the best-documented modern reference implementation** — **its
architecture notes on salsa-style incremental computation are worth reading regardless of
language.**

---

## §17. Testing and Publishing

**⚠️ Testing**: **`@vscode/test-electron` runs integration tests in a real VS Code
instance; unit-test pure logic separately.** ⚠️ **Keep as much logic as possible OUT of
the `vscode` API surface so it's testable without launching an editor** — **this is the
single best structural decision in extension code.**
**⚠️ Packaging and publishing**: **`vsce package` → `.vsix`; `vsce publish` to the VS Code
Marketplace via an Azure DevOps PAT.** ⚠️ **Open VSX is the separate, vendor-neutral
registry that VSCodium, Zed-adjacent forks and other non-Microsoft builds use** —
**publish to both if you want reach beyond Microsoft's distribution.**
**⚠️ Note the licensing constraint**: ⚠️ **the Microsoft Marketplace's terms restrict use to
Microsoft's own products**, **which is precisely why Open VSX exists and why forks can't
simply point at it.**

---

# PART V — BUILDING AN EDITOR

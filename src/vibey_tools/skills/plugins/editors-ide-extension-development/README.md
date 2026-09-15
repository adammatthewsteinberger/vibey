# Editors, IDEs and Extension Development Plugin

Text editors and IDE engineering, organised around the insight that reframes the editor wars: the important layer stopped being the editor and became the protocols. Choosing an editor honestly, nano, vim and Neovim's modal model, Emacs; VS Code's multi-process architecture, configuration and remote development; LSP, DAP and Tree-sitter; VS Code extension development end to end including webviews and language servers; and the internals of building an editor — text buffer data structures, rendering, incremental parsing, indexing and performance.

One reference, split into 5 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (verified August 2026) flags what goes stale first.

## Skills

- **editor-choosing-vim-neovim-and-emacs** — Choosing an Editor, nano, Vim's Actual Model, Configuring Vim and Neovim, and Emacs (§0–§5): Routing; Choosing, Honestly; nano; ⚠️ Vim's Actual Model; Configuring Vim and Neovim; Emacs.
- **editor-vscode-architecture-and-the-protocol-layer** — VS Code Architecture, Configuration and Workspaces, Remote Development, LSP, DAP, and Tree-sitter (§6–§11): Architecture; Configuration and Workspaces; Remote Development; ⚠️ LSP; DAP; Tree-sitter.
- **editor-vscode-extension-development** — Anatomy of a VS Code Extension, Contribution Points, API Surfaces, Webviews, Writing a Language Server, and Publishing (§12–§17): ⚠️ Anatomy of a VS Code Extension; Contribution Points and Activation; API Surfaces; Webviews; Writing a Language Server; Testing and Publishing.
- **editor-internals-buffers-rendering-and-performance** — Text Buffer Data Structures, Rendering, Indexing, the JetBrains Platform, Terminal UI, and Editor Performance (§18–§23): ⚠️ Text Buffer Data Structures; Rendering; Indexing and Code Intelligence; The JetBrains Platform; Terminal UI Programming; Editor Performance.
- **editor-reference** — What's Live, Anti-Patterns, Misconceptions, Numbers, and Resources (§24–§30): What's Live; Anti-Patterns; Misconceptions; Numbers; Resources; Quick Reference; Method.

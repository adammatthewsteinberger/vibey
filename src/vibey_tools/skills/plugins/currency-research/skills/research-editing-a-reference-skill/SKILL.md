---
name: research-editing-a-reference-skill
description: Use when editing a SKILL.md in a split multi-skill reference plugin — changing a dated claim without disturbing section numbering, cross-references or the header block, and then updating the manifests that mirror it. Triggers on editing a skill file, SKILL.md structure, section cross-references, the "§N → skill" annotation, plugin.json version bump, marketplace.json mirror, README plugin table, and running the repository checkers before opening a pull request.
---

# Editing a Reference Skill

The mechanics of changing one claim inside a generated reference plugin without breaking the
five other things that point at it.

Read this **before** making any edit. The structures below are load-bearing, and several of
them are not obvious from looking at a single file.

---

## Anatomy of a generated SKILL.md

```
---
name: <matches the directory name>
description: "<the trigger — what makes Claude load this skill>"
---

# <Plugin short name>: <Part title>

> **Part 3 of 6** of the *<Display Name>* reference (plugin `<plugin>`), covering §13–§18.
> Sibling skills: `x` (§0–§5), `y` (§6–§12), … . Section numbers are shared across the set;
> a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** <one or two sentences>. See §27 → `foo-reference` for <what moved>.

> <the document's own scope blockquote — identical in every skill of the plugin>

---

## §13. <Section title>
…
---

## §14. <Section title>
…
```

Three consequences:

- **The header blockquote is generated,** not authored. Do not hand-edit the `Part i of n`
  line or the sibling list; they are derived from the split.
- **The scope blockquote is duplicated across every skill in the plugin.** If a currency edit
  touches it, it must be changed identically in all of them or the plugin becomes inconsistent.
- **Section numbers are shared across the whole plugin**, not per skill. `§14` means the same
  section whichever skill you are reading.

---

## The cross-reference rule

Within a plugin, a reference to a section **that lives in a sibling skill** is annotated:

```
… as covered in §20 → `foo-isa-simulation-and-specialization`, the …
```

A reference to a section **in the same skill** stays bare (`§14`). A range lists only the
non-local targets: ``§7–§12 → `x`, `y` ``.

**If your edit adds a new `§N` reference, you must annotate it yourself** using the same rule:
find which skill owns §N (look at the sibling list in the header), and append `` → `that-skill` ``
if it is not the skill you are editing.

### ⚠️ Citations of *other documents* must stay bare

The marketplace's references cite each other. Those citations use the *other* document's
section numbers and **must never be annotated**, or they turn into links into the wrong
plugin — which is worse than no link, because it looks authoritative.

Four phrasings occur. All of them mean "another document's §N":

```
see a power engineering reference §12          ← 'a … reference' then the ref
a peripherals reference (§5's wireless HID)    ← ref opens the parenthetical
a robotics-software reference (§14 there)      ← ref followed by 'there'
§6 of a communications reference               ← ref before the words
```

And two lookalikes that **are** internal and stay annotated:

```
The IA reference (§3)                                    ← a books-table entry; note "The", not "a"
a security reference (§20's hierarchy … recurs there)    ← our §20, recurring over there
```

The distinguishing signals are the **indefinite article** (`a`/`an` introduces another
document; `The` usually introduces a titled work) and **`there` vs `here`**. When a citation
is genuinely ambiguous, leave it bare and say so in the pull request.

---

## Byte discipline

The section bodies are byte-identical to the source documents they were split from, and
tooling checks that. So:

- **Change only the characters that must change.** Do not reflow paragraphs, normalise
  punctuation, convert quotes, retab tables or "tidy" whitespace.
- **Keep the line wrapping style of the surrounding text.** These files are hand-wrapped at
  roughly 90 characters; a re-wrapped paragraph produces an enormous, unreviewable diff for a
  one-word change.
- **Preserve the markers.** The ⚠️ prefixes, the bold runs, the confidence tags and the table
  shapes are all deliberate.
- **Do not renumber sections.** Ever, in a currency edit. Numbering is shared across the
  plugin, cited by sibling skills and sometimes cited by *other* plugins.

---

## What else must change when you edit

Work through this list every time; the repository's checkers enforce most of it.

1. **`plugins/<plugin>/.claude-plugin/plugin.json`** — bump `version`. A currency edit is a
   patch or minor revision; follow whatever the plugin is already using (`0.1.0` → `0.2.0`
   is this repository's convention for "revised").
2. **`.claude-plugin/marketplace.json`** — mirror the new `version`. Mirror `description`
   and `category` too if they changed. **A mismatch here breaks installation**, and the
   validator fails the build.
3. **`plugins/<plugin>/README.md`** — update the skill bullet only if the section list changed.
4. **Root `README.md` plugin table** — update the version cell for that plugin, and the
   "Covers" cell only if the topic list genuinely changed.
5. **Counts** — only if you added or removed a whole skill or plugin, which a currency edit
   should not do. If it somehow does, the plugin and skill counts appear in `README.md`,
   `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/index.md`, `docs/usage.md`,
   `docs/hooks.py`, `docs/gen_reference.py`, `pyproject.toml`, `mkdocs.yml` and
   `.github/workflows/ci.yml`.
6. **Package version** — `src/vibey_skills/__init__.py` and `marketplace.json`'s
   `metadata.version` must stay equal. Bump them together, or not at all; the validator
   asserts they match.

Do **not** hand-edit anything under `docs/reference/` — that tree is generated from
`plugins/**` at build time.

---

## Before opening the pull request

Both must exit 0:

```bash
python3 tools/validate_manifests.py
python3 tools/check_links.py
```

`validate_manifests.py` catches name/version/frontmatter drift and duplicate skill names.
`check_links.py` enforces the absolute-vs-relative link rule (root Markdown uses absolute
GitHub URLs; files under `docs/` use relative links) and is hermetic, so it needs no network.

If the edit changed anything under `docs/` or `mkdocs.yml`, also run:

```bash
mkdocs build --strict
```

⚠️ **A currency edit that fails a checker is not ready.** Fix it or drop that edit from the
pull request — never disable a check to get a change through.

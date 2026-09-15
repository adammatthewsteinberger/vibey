# A guided first session

The goal: in under thirty minutes, install `vibey-gh` on one repository you
own and watch it verify itself — no releases, no risk, nothing published.

Never used a terminal? It is the text window where you type instructions to
your computer and press Enter — on a Mac it's the app called **Terminal**, on
Windows **PowerShell**. Every grey block below is one instruction: copy it,
paste it there, press Enter. That is the whole skill this page needs.

## 1. Install the tool (2 minutes)

```bash
pip install vibey-gh
```

That installs one command, `vibey-gh`, with no other dependencies — it will
not change your project's dependency tree.

## 2. Point it at a repository (3 minutes)

From inside any git repository you own:

```bash
vibey-gh install
```

This writes a handful of files: git hooks (small scripts that run when you
commit, adding a provenance line automatically) and workflow files under
`.github/workflows/` (the instructions GitHub runs in the cloud). Nothing has
executed yet — you can read every file it wrote, and `git diff` shows exactly
what changed.

## 3. Ask it whether things are healthy (2 minutes)

```bash
vibey-gh check
```

`check` verifies the pieces it installed are intact and consistent. A clean
run prints one `ok` line. If it complains, the message names the file and the
fix — nothing here is fatal, because nothing is live yet.

```bash
vibey-gh doctor
```

`doctor` goes further: it reads your configuration and predicts whether the
automation would actually work on GitHub — before you push anything. It runs
entirely offline and needs no passwords or tokens.

## 4. Make one commit and watch the hook work (5 minutes)

```bash
echo "hello" > hello.txt
git add hello.txt
git commit -m "chore: try the commit hook"
git log -1 --format=%B
```

The last command shows your commit message — with a `Made-With:` line the
hook added for you. That line is the provenance trailer: proof, on every
commit, of the tooling that produced it. You never have to remember it again.

## 5. What just happened, and what didn't

You now have: hooks that stamp provenance on every commit, and workflow files
ready to review, merge, version, and release for you — **but none of the
cloud automation is running yet**, because you haven't pushed and the
repository settings that let it act (tokens, permissions) aren't configured.
That is deliberate: nothing acts on your repository until you connect it.

## Where to go next

- [Adoption](../adoption.md) — the full map: what to configure, in what
  order, and every trap nine real adoptions found.
- [The glossary bridge](glossary.md) — the project words you just met
  (provenance, gate, merge train...), each linked to its full story.

---

**The short version, again**: you installed one tool, pointed it at one
folder of code, and watched it prove itself — nothing left your machine.
**Your next step**: skim [the glossary bridge](glossary.md), then let
[Adoption](../adoption.md) take you from this rehearsal to the real thing.

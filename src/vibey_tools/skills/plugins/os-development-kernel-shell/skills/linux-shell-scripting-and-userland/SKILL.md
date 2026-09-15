---
name: linux-shell-scripting-and-userland
description: "Use when writing, reviewing, or debugging shell scripts, or choosing a shell. Covers the expansion order and the traps ranked by damage (word splitting, globbing, the limits of set -e, rm -rf with an unset variable), parameter expansion, POSIX sh vs bash vs zsh vs fish vs nushell and bash 5.3, the defensive script template (set -Eeuo pipefail, ERR traps and cleanup, validated inputs, atomic file replacement, real locks, retry with backoff), the safety cases, and the coreutils and systemd userland tools worth genuinely knowing."
---

# Linux Kernel & Shell: Shell Semantics, Choosing a Shell, Defensive Scripting, and the Userland

> **Part 3 of 5** of the *OS Development — Linux Kernel and Shell* reference (plugin `os-development-kernel-shell`), covering §8–§11. Sibling skills: `linux-kernel-architecture-and-code` (§0–§3), `linux-syscalls-ebpf-boot-and-init` (§4–§7), `linux-kernel-debugging-process-and-hardening` (§12–§14), `linux-kernel-shell-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `linux-kernel-shell-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — architecture, algorithms, or semantics that have been stable for
>   decades and will outlive this document.
> - **[VERSIONED]** — depends on a kernel version, a shell version, or a distro. Check
>   `Documentation/`, the man page, or the source for your version.
> - **[CONTESTED]** — the kernel community itself disagrees, publicly and at length.
>   Both cases given.
>
> **⚠️ GOTCHA** boxes mark the mistakes that produce kernel oopses, data loss, silent
> corruption, or a patch rejected on the mailing list.
>
> **The framing that matters most:** the kernel is not "a big program." It is a
> **hostile-input state machine running with no memory protection, no exceptions, a
> hard limit on stack depth, and a promise never to break userspace**. Almost every
> kernel-specific rule below descends from one of those five facts.

---

## §8. Shell Semantics — the part that causes the bugs

**[DURABLE] The shell is a macro language over process execution, and its evaluation
order is the source of nearly every shell bug.** Learn the order and most mysteries
dissolve.

### 8.1 The expansion order

For each command word, in this exact sequence:
```
1. Brace expansion            {a,b}  {1..5}          (bash/zsh; NOT POSIX)
2. Tilde expansion            ~  ~user
3. Parameter expansion        $var  ${var:-def}  ${var#pat}  ${var//a/b}
   Command substitution       $(cmd)   `cmd`
   Arithmetic expansion       $(( ... ))
4. WORD SPLITTING             ← splits UNQUOTED results on $IFS   ★ the bug lives here
5. Pathname expansion (glob)  *  ?  [abc]           ← on UNQUOTED results   ★ and here
6. Quote removal
```
**Steps 4 and 5 do not happen inside double quotes.** That single fact is why the rule is
"quote everything."

```bash
file="my report.txt"
rm $file        # → rm my report.txt   → tries to remove TWO files. Data loss.
rm "$file"      # → rm 'my report.txt' → correct.

files=$(ls)     # word-splits AND globs the output. Filenames with spaces or * break it.
                # Also: NEVER parse ls. Use a glob or find -print0.
```

### 8.2 The traps, ranked by how much damage they cause

> **⚠️ 1. Unquoted variables.** Covered above. `shellcheck` flags every instance.
> This is the number one shell bug and it is 100% mechanically detectable.

> **⚠️ 2. `$@` vs `$*`.** `"$@"` expands to one word per argument, preserving them
> exactly. `"$*"` joins them into a single word with the first `$IFS` char. **Always
> `"$@"`, always quoted.** Unquoted `$@` word-splits again and defeats the purpose.

> **⚠️ 3. The pipeline exit status.** By default `$?` is the **last** command's status:
> `false | true` succeeds. `set -o pipefail` makes the pipeline fail if any element
> fails. `${PIPESTATUS[@]}` (bash) has the individual statuses.

> **⚠️ 4. Pipelines create subshells.** `... | while read x; do count=$((count+1)); done`
> leaves `count` unchanged in bash, because the loop ran in a subshell. Fix with process
> substitution: `while read x; do ...; done < <(cmd)`, or `shopt -s lastpipe`.
> **zsh does not have this problem** — it runs the last pipeline element in the current
> shell.

> **⚠️ 5. `set -e` does not do what you think.** It is full of exceptions: it doesn't
> trigger for commands in a condition (`if`, `while`, `&&`, `||`), or for any command
> except the last in a pipeline (without `pipefail`), or inside a function called in a
> condition context — where it is disabled for the *entire* function. It is a useful
> default, **not** a substitute for checking return codes on anything that matters.
> The `set -e` critique (the "BashFAQ 105" position) is worth reading before relying on it.

> **⚠️ 6. `[` vs `[[`.** `[` is the `test` command — its arguments undergo word splitting
> and globbing, so `[ $x = y ]` breaks when `$x` is empty or has spaces. `[[ ]]` is shell
> syntax (bash/zsh/ksh, **not POSIX**) with no splitting inside, plus `=~` and `&&`.
> **Use `[[ ]]` in bash/zsh; quote religiously in POSIX `sh`.**
> Note also: **POSIX.1-2024 removed `-a` and `-o` from `test`** — use `&&`/`||` between
> separate `[ ]` invocations.

> **⚠️ 7. Arithmetic and leading zeros.** `$((08))` is an error in bash — leading zero
> means octal. Bites date handling every August and September. Use `10#$var`.

> **⚠️ 8. `read` mangles input by default.** `read -r` (don't interpret backslashes),
> `IFS= read -r line` (don't strip leading/trailing whitespace). The canonical loop is
> `while IFS= read -r line; do ...; done < file`.

> **⚠️ 9. Filenames can contain anything except `/` and NUL** — including newlines,
> spaces, and leading `-`. Use `find -print0 | xargs -0`, or `find -exec ... +`, and
> `--` to end option parsing (`rm -- "$f"`).

> **⚠️ 10. `cd` can fail.** `cd /some/dir; rm -rf *` deletes the wrong thing when the
> `cd` fails. Always `cd /some/dir || exit 1`.

### 8.3 Parameter expansion — the underused half of the language

```bash
${var:-default}   # use default if unset/empty (doesn't assign)
${var:=default}   # assign default if unset/empty
${var:?message}   # ERROR OUT if unset/empty  ← excellent for required arguments
${var:+alt}       # use alt only if var IS set
${#var}           # length
${var#prefix}     ${var##prefix}    # strip shortest / longest matching prefix
${var%suffix}     ${var%%suffix}    # strip shortest / longest matching suffix
${var/old/new}    ${var//old/new}   # replace first / all (bash/zsh, not POSIX)
${var:offset:len}                   # substring
${array[@]}  ${#array[@]}  ${!array[@]}   # elements, count, indices
```
`${var#*/}` and `${var%/*}` replace `basename`/`dirname` without forking a process —
meaningful inside a loop.

---

## §9. Choosing a Shell

### 9.1 The comparison

| | **bash** | **zsh** | **fish** | **nushell** | **POSIX sh** (dash) |
|---|---|---|---|---|---|
| Version (Aug 2026) | **5.3** (July 2025) | **5.9.1** (May 2026) | **4.7** (May 2026) | 0.111+ (pre-1.0) | — |
| Written in | C | C | **Rust** (since 4.0) | Rust | C |
| Default on | Most Linux distros | **macOS since Catalina** | none | none | Debian `/bin/sh` |
| POSIX-compatible | Yes (mostly) | Mostly | **No, by design** | **No** | Yes, by definition |
| Runs bash scripts | — | Mostly unmodified | No | No | Only POSIX ones |
| Interactive out of box | Poor | Good with plugins | **Excellent** | Good | Minimal |
| Structured data | No | No | No | **Yes — tables, JSON, SQLite natively** | No |
| Best for | **Scripts, portability, servers** | Daily interactive on macOS/Linux with bash compat | Best interactive UX | Data wrangling in the terminal | `#!/bin/sh` scripts, containers |

**Adoption reality**: Stack Overflow's 2025 survey put Bash/shell scripting at **49% of
developers**, ranking fifth among all languages, ahead of TypeScript. Apple's 2019 switch
of the macOS default to zsh is the single largest driver of zsh adoption. Fish sits around
7% among developers.

### 9.2 The version that matters: bash 5.3

**[VERSIONED] Bash 5.3 (3 July 2025)** — the first release in three years. What's
actually new and useful:
- **`${ command; }`** — command substitution that **runs in the current shell context, no
  fork**, capturing stdout. And **`${| command; }`**, which runs in the current shell and
  leaves the result in `REPLY`. This is the headline feature and it matters for
  performance in loops.
- **`GLOBSORT`** — control pathname-completion/glob sort order by name, size, blocks,
  mtime, atime, ctime, numeric, or none, ascending or descending.
- `source -p PATH` to search a given PATH instead of `$PATH`.
- **Executing the RHS of `&&`/`||` no longer forks when unnecessary** — a real scripting
  speedup.
- `local -` saves and restores single-letter shell options for the function's duration.
- `compgen`/`complete -o nosort`; `wait` can now wait on the most recent process
  substitution; `unset var[0]` behaves like `${var[0]}`.
- **Source updated for C23 conformance — bash no longer compiles with K&R C compilers.**
- Readline 8.3 alongside: case-insensitive search option, `export-completions`,
  `force-meta-prefix`, `rl_print_keybinding`.

> **⚠️ GOTCHA — macOS ships bash 3.2.** Apple has not shipped a newer bash since the
> GPLv3 licence change in 2007. Any script relying on associative arrays (bash 4.0),
> `${var,,}` case conversion (4.0), `readarray`/`mapfile` (4.0), or `${ ... }` (5.3) will
> fail on a stock Mac. Either target POSIX sh, or require `brew install bash` and use
> `#!/usr/bin/env bash`.

### 9.3 The pragmatic answer

**[DURABLE, and the consensus across essentially every practitioner comparison]:**
> **Use whatever you like interactively. Write bash (or POSIX sh) for anything that has
> to run somewhere else.**

fish and nushell are genuinely better interactive shells and genuinely worse scripting
targets — fish requires rewriting with `set`, `if…end`, and function-scoped variables;
nushell requires rethinking (no subshells, no `$(...)`, structured pipelines). The
recurring, practical friction with fish: version managers (nvm, rbenv, pyenv, asdf,
sdkman) all ship bash/zsh hooks, and fish users depend on community wrappers that lag.
And — a distinctly 2026 problem — **AI coding agents shell out to the system default
shell**, so a non-POSIX default shell introduces a whole class of tooling breakage.

For **portable scripts**, target POSIX `sh` and test with `dash`. Bash-isms silently work
on a bash-as-/bin/sh system and break on Debian/Ubuntu where `/bin/sh` is `dash`, and in
Alpine containers where it's busybox `ash`. `shellcheck -s sh` catches this.

---

## §10. Defensive Shell Scripting

### 10.1 The template

```bash
#!/usr/bin/env bash
# Purpose: one line. Usage: script.sh <input> [output]
set -Eeuo pipefail
#   -E  ERR trap is inherited by functions and subshells
#   -e  exit on error (KNOW ITS LIMITS — §8.2 trap 5)
#   -u  error on unset variable      ← catches the rm -rf "$TYPO/" class
#   -o pipefail  a pipeline fails if ANY element fails
IFS=$'\n\t'                          # remove space from IFS: safer word splitting

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# --- cleanup that actually runs, on every exit path -------------------------
readonly TMPDIR_="$(mktemp -d)"      # mktemp -d, never a predictable /tmp path
cleanup() {
    local rc=$?
    rm -rf -- "$TMPDIR_"
    exit "$rc"
}
trap cleanup EXIT                    # EXIT fires for normal exit, set -e, and signals
trap 'die "interrupted"' INT TERM

die()  { printf '%s: %s\n' "${0##*/}" "$*" >&2; exit 1; }
log()  { printf '[%s] %s\n' "$(date -Is)" "$*" >&2; }   # logs to stderr, not stdout

# --- required inputs, validated ---------------------------------------------
: "${INPUT_FILE:?INPUT_FILE must be set}"        # ${:?} is the cheapest validation
[[ -r $INPUT_FILE ]] || die "cannot read: $INPUT_FILE"

need() { command -v "$1" >/dev/null 2>&1 || die "missing dependency: $1"; }
need jq; need curl

main() {
    local out="${1:-/dev/stdout}"
    # ... work ...
}
main "$@"
```

### 10.2 The rules

1. **`shellcheck` in CI, non-negotiable.** It is the single highest-value tool in shell
   development and catches the entire quoting class mechanically. `shfmt` for formatting.
2. **Quote every expansion.** `"$var"`, `"$@"`, `"${arr[@]}"`. The exceptions are rare
   and deliberate.
3. **`local` every function variable.** Shell variables are global by default; a function
   that forgets `local i` will silently corrupt its caller's loop.
4. **Never parse `ls`.** Use globs (`for f in ./*.txt`) or `find -print0 | while IFS= read
   -r -d '' f`.
5. **`--` before user-controlled arguments**: `rm -- "$f"`. A file named `-rf` is legal.
6. **Prefix globs with `./`**: `rm ./*` not `rm *`, for the same reason.
7. **`mktemp`, always.** Predictable temp paths are a symlink-attack primitive.
8. **`trap ... EXIT` for cleanup**, not cleanup code at the end (which `set -e` skips).
9. **Log to stderr; put data on stdout.** This is what makes a script composable.
10. **Exit codes mean something**: 0 success, 1 general, 2 usage, 126 not executable,
    127 not found, 128+N killed by signal N.
11. **Idempotence.** Assume the script will be re-run after failing halfway.
12. **`set -x` / `PS4='+ ${BASH_SOURCE}:${LINENO}: '`** for tracing, and
    `bash -n script.sh` for a syntax-only check.
13. **When it exceeds ~200 lines or needs real data structures — stop and use Python.**
    This is the most commonly ignored and most valuable rule in the list.

### 10.3 The safety cases

```bash
# THE classic. With set -u, a typo'd or empty variable exits instead of deleting /.
rm -rf "${BUILD_DIR:?BUILD_DIR not set}"/*

# Confirm before anything destructive when interactive
if [[ -t 0 ]]; then read -r -p "Delete ${count} files? [y/N] " a; [[ $a == [yY] ]] || exit 1; fi

# Atomic file replacement — same recipe as §1.5, in shell
tmp="$(mktemp -- "${target}.XXXXXX")"
generate > "$tmp" && mv -- "$tmp" "$target"     # mv within a filesystem is atomic

# Concurrency: a real lock, not a PID file
exec 9>/var/lock/myjob.lock
flock -n 9 || die "already running"

# Retry with backoff
for i in 1 2 4 8 16; do curl -fsS "$url" && break; sleep "$i"; done
```

---

## §11. The Userland

### 11.1 Tools worth genuinely knowing

| Domain | Tools |
|---|---|
| Text | `grep`(`-r -n -F -w -o -P`), `sed`, `awk`, `cut`, `tr`, `sort`(`-u -n -k -t`), `uniq -c`, `join`, `comm`, `paste`, `column -t`, `fmt` |
| Structured | **`jq`** (JSON), `yq`, `xmlstarlet`, `csvkit`, `miller`(mlr) |
| Files | `find`(`-print0 -exec +`), `xargs -0 -P`, `rsync -aHAX --delete`, `stat`, `install`, `readlink -f` |
| Processes | `ps aux`, `pgrep/pkill`, `kill -l`, `nohup`, `setsid`, `timeout`, `nice`, `ionice`, `taskset`, `chrt` |
| Observability | `top`/`htop`/`btop`, `iostat`, `vmstat`, `mpstat`, `pidstat`, `sar`, **`ss`** (not `netstat`), **`ip`** (not `ifconfig`), `lsof`, `fuser`, `dstat` |
| Introspection | `strace`, `ltrace`, `perf`, `bpftrace`, `/proc/PID/{maps,status,fd,stack,limits}` |
| Disks | `lsblk`, `blkid`, `df -h`, `du -sh`, `ncdu`, `smartctl`, `fio`, `badblocks` |
| Build/pack | `make`, `ninja`, `meson`, `cmake`, `pkg-config`, `dpkg/rpm`, `ldd`, `objdump`, `readelf`, `nm`, `strings` |
| Modern rewrites | `rg`(ripgrep), `fd`, `bat`, `eza`, `delta`, `zoxide`, `atuin`, `starship`, `dust`, `sd` |

**[DURABLE] The pipeline idioms that never stop being useful:**
```bash
sort | uniq -c | sort -rn | head          # frequency ranking. Works on anything.
awk '{s+=$3} END {print s}'               # sum a column
awk -F: '$3 >= 1000 {print $1}' /etc/passwd
find . -type f -print0 | xargs -0 -P"$(nproc)" -n1 process   # parallel over files
comm -13 <(sort a) <(sort b)              # lines in b not in a (process substitution)
```

**⚠️ GNU vs BSD vs busybox.** `sed -i` takes an argument on macOS/BSD and not on GNU;
`date` options differ completely; `readlink -f` doesn't exist on old macOS. **Test the
target's userland, or install GNU coreutils, or stay strictly POSIX.** Note also that
Ubuntu has begun shipping **uutils** (a Rust coreutils reimplementation) — behavioural
differences from GNU coreutils are a new source of surprises.

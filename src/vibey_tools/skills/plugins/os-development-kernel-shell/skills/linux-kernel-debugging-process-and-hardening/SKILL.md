---
name: linux-kernel-debugging-process-and-hardening
description: "Use when debugging a kernel problem, contributing a patch, or hardening a Linux system. Covers the kernel debug configs to build with, reading an oops, the tracing hierarchy (ftrace, perf, bpftrace, flame graphs), kernel testing (KUnit, kselftest, syzkaller), how change actually happens (maintainers, mailing lists, merge windows), versioning and stable trees, the CVE flood, the kernel attack surface, the defenses (KASLR, CFI, lockdown, LSMs), and an honest kernel-hardening posture."
---

# Linux Kernel & Shell: Debugging and Observability, the Kernel Development Process, and Hardening

> **Part 4 of 5** of the *OS Development — Linux Kernel and Shell* reference (plugin `os-development-kernel-shell`), covering §12–§14. Sibling skills: `linux-kernel-architecture-and-code` (§0–§3), `linux-syscalls-ebpf-boot-and-init` (§4–§7), `linux-shell-scripting-and-userland` (§8–§11), `linux-kernel-shell-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §12. Debugging and Observability

### 12.1 The kernel debug configs to build with

**[DURABLE] Turn these on in development. Every one of them turns a heisenbug into a
reproducible splat:**
```
CONFIG_DEBUG_KERNEL=y
CONFIG_DEBUG_INFO=y CONFIG_DEBUG_INFO_BTF=y     # BTF also required for CO-RE BPF
CONFIG_KASAN=y                                   # use-after-free, OOB. ~2-3x slowdown
CONFIG_UBSAN=y                                   # undefined behaviour
CONFIG_KCSAN=y                                   # data races
CONFIG_PROVE_LOCKING=y                           # lockdep — deadlock detection
CONFIG_DEBUG_ATOMIC_SLEEP=y                      # sleeping in atomic context
CONFIG_PROVE_RCU=y
CONFIG_DEBUG_OBJECTS=y
CONFIG_SLUB_DEBUG_ON=y                           # redzoning, poisoning
CONFIG_DEBUG_PAGEALLOC=y
CONFIG_FAULT_INJECTION=y                         # make allocations fail on purpose
CONFIG_KFENCE=y                                  # low-overhead; safe for PRODUCTION
```
**KASAN + lockdep together find the overwhelming majority of new kernel bugs before they
reach anyone else.** KFENCE is the one you can leave on in production (sampling-based,
near-zero overhead).

### 12.2 Reading an oops

```
BUG: kernel NULL pointer dereference, address: 0000000000000010
#PF: supervisor read access in kernel mode
Oops: 0000 [#1] PREEMPT SMP NOPTI
CPU: 3 PID: 1234 Comm: myapp Tainted: G           O       6.18.40 #1
RIP: 0010:foo_read+0x42/0x180 [mymod]     ← WHERE. function+offset/size [module]
...
Call Trace:
 <TASK>
 vfs_read+0xb4/0x330
 ksys_read+0x6b/0xf0
 do_syscall_64+0x5c/0x90
```
Read it in this order:
1. **The first line** — what kind of fault, and the bad address. `0x10` means a NULL
   pointer plus a small struct offset; `0x6b6b6b6b...` is SLUB poison (use-after-free);
   `0xffffffffffffffff` is often an unchecked `ERR_PTR`.
2. **`RIP: function+offset/size`** — the exact instruction. Resolve with
   `./scripts/faddr2line vmlinux foo_read+0x42/0x180` or `addr2line`.
3. **`Tainted:`** — `G` clean-ish, `O` out-of-tree module loaded, `P` proprietary,
   `D` previous oops, `W` previous warning. **Maintainers will ask about taint first.**
4. **Call trace** — the path in. Entries with `?` are stale stack values, not real frames.
5. **`[#1]`** — first oops. A second one after the first is usually corruption from the
   first; only the first is trustworthy.

`decode_stacktrace.sh` symbolizes the whole thing. `panic_on_oops=1` and `kdump`/`crash`
give you a full vmcore for post-mortem analysis with `crash` or `drgn`.

### 12.3 Tracing — the hierarchy

| Tool | Overhead | Use for |
|---|---|---|
| `printk`/`pr_debug` + **dynamic debug** | high if hot | Coarse. `echo 'file foo.c +p' > /sys/kernel/debug/dynamic_debug/control` |
| **ftrace** (`/sys/kernel/tracing`) | low | Function graph tracing, latency tracers, per-event tracepoints. Built in, no tooling needed |
| **`trace-cmd` / KernelShark** | low | ftrace with a usable interface |
| **perf** | low-medium | CPU profiling, `perf record/report`, `perf top`, `perf trace`, hardware counters, **flame graphs** |
| **bpftrace** | low | One-liners with real logic. The modern first reach |
| **BCC / libbpf tools** | low | Prewritten: `execsnoop`, `opensnoop`, `biolatency`, `tcpconnect`, `runqlat`, `offcputime` |
| **LTTng** | low | High-volume production tracing with a stable format |
| **`strace` / `ltrace`** | **very high** | Userspace syscall/library tracing. ptrace-based — do not use on a hot production process |
| **KGDB / KDB** | — | Interactive source-level kernel debugging (needs a serial console or VM) |
| **QEMU + gdb** | — | **The best kernel development loop.** `qemu -s -S` then `gdb vmlinux` |

```bash
# The five bpftrace one-liners worth memorizing
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { @[comm] = count(); }'
bpftrace -e 'kprobe:vfs_read { @bytes = hist(arg2); }'
bpftrace -e 'tracepoint:sched:sched_process_exec { printf("%s %s\n", comm, str(args->filename)); }'
bpftrace -e 'kretprobe:do_sys_openat2 /retval < 0/ { @errs[comm, -retval] = count(); }'
bpftrace -e 'profile:hz:99 { @[kstack] = count(); }'      # sampled kernel stacks

# ftrace without any tooling
cd /sys/kernel/tracing
echo function_graph > current_tracer && echo do_sys_openat2 > set_graph_function
echo 1 > tracing_on; cat trace_pipe

# perf → flame graph
perf record -F 99 -a -g -- sleep 30 && perf script | stackcollapse-perf.pl | flamegraph.pl > fg.svg
```

### 12.4 Testing

`kunit` (in-kernel unit tests, run under UML or QEMU), `kselftest`
(`tools/testing/selftests`), **syzkaller** (coverage-guided syscall fuzzer — the single
largest source of kernel bug reports in existence), `xfstests` for filesystems, LTP.
**Send a syzkaller reproducer with your bug report and you will get a fix; send a
description and you may not.**

---

## §13. The Kernel Development Process

### 13.1 How change actually happens

```
you → patch → subsystem mailing list + MAINTAINERS entries (get_maintainer.pl)
   → review (expect several rounds; v2, v3, v4 are normal and not an insult)
      → maintainer's -next tree → linux-next (integration testing)
         → MERGE WINDOW (2 weeks after a release) → Linus's tree
            → rc1 … rc7 (~7 weeks of stabilization)
               → release (~9–10 week cadence)
                  → -stable backports (Fixes: tag / Cc: stable@vger.kernel.org)
```

**Practical mechanics:**
- `scripts/get_maintainer.pl -f path/to/file.c` tells you exactly who to send to. Use it.
- `scripts/checkpatch.pl --strict` before every send.
- **Plain-text email, no HTML, no attachments.** `git send-email`, or `b4` which is now
  the ergonomic path for both sending and applying series.
- Subject: `[PATCH v3 2/5] subsystem: short imperative summary`.
- A **`Fixes: <12-char-sha> ("subject")`** tag is how a fix gets auto-backported to stable.
- Changelog **below** the `---` line for the version history; commit message above.
- `Reviewed-by`, `Acked-by`, `Tested-by`, `Reported-by`, `Closes:` are meaningful and
  tracked.
- Response to review is expected within a reasonable time; silence means the patch dies.

**[DURABLE] The commit message matters as much as the code.** Explain *why*, not *what* —
the diff shows what. A maintainer reading it in three years during a bisect needs the
reasoning.

### 13.2 Versioning and stable trees [VERSIONED — this changed in 2026]

**Version numbers carry no semantic meaning.** Linus increments the major number when the
minor gets uncomfortably large, not at milestones. **Linux 7.0 released 12 April 2026**
after 6.19, and **7.1 and 7.2 followed** on the ordinary ~9–10 week cadence; it is "a
normal continuation, not a major architectural break."

| Tree | Meaning |
|---|---|
| **mainline** | Linus's tree. `rc` releases during stabilization |
| **stable** | Point releases of the current release, weeks of support |
| **longterm (LTS)** | Multi-year support. **Each new LTS starts with a ~2-year projected EOL that gets extended if industry helps maintain it** |

**Current LTS set (Aug 2026):** 5.10, 5.15, 6.1, 6.6, 6.12, 6.18. In **February 2026**
Greg Kroah-Hartman **extended support for 6.6, 6.12, and 6.18** after discussions with
device manufacturers and embedded vendors — 6.18 now runs to at least **December 2028**.
**5.10 and 5.15 both EOL 31 December 2026** — if you're on either, the clock is running.

> **⚠️ GOTCHA — non-LTS releases get only a few months.** 7.0 reached EOL on
> **27 June 2026**, roughly ten weeks after release. Shipping a product on a non-LTS
> kernel means shipping a kernel that stops getting security fixes almost immediately.
> **Anchor products to an LTS.**

### 13.3 CVEs — and the flood

**[VERSIONED, and a genuine operational problem.]** In February 2024 **kernel.org became
its own CNA**. Two consequences designed in from the start: CVEs are assigned only *after*
a fix exists, and the team **errs on the side of assigning CVEs to all fixes** — because,
as the documentation puts it, almost any bug might be exploitable and exploitability is
usually not evident when the bug is fixed.

The result: **the Linux kernel is now the single largest issuer of CVEs**, at roughly
fifty a week, **with no severity scores attached**, because the kernel community treats a
CVE as an identifier for a fix rather than an alarm. In July 2026, **432 kernel CVEs were
published in under 48 hours**, prompting a public argument on oss-sec about whether
per-CVE prioritization is even feasible at that volume.

**[CONTESTED] Whether this is good.** *For:* it's honest — other vendors avoid assigning
CVEs unless exploitability is unambiguous, which systematically undercounts risk; and the
kernel's advice ("run a maintained stable kernel and take the point releases") is the
correct advice regardless. *Against:* a stream of unscored CVEs destroys the signal that
CVE was created to provide, and pushes triage cost onto every downstream consumer.

**The practical consequence, and it is now a legal one:** severity triage is the device
maker's job. Under the **EU Cyber Resilience Act** — vulnerability and incident reporting
obligations start **11 September 2026**, full obligations **11 December 2027** — the
kernel is a component in your SBOM and its vulnerabilities are your duty to handle.
**The cheapest compliant strategy is exactly what the kernel community has always
recommended: stay on a maintained LTS and take the point releases.** Do not attempt to
cherry-pick individual "important" fixes at a rate of fifty a week.

---

## §14. Security and Hardening

### 14.1 The kernel attack surface

**[DURABLE] Everything reachable from an unprivileged process is attack surface**: every
syscall, every ioctl, every `/proc` and `/sys` write, every netlink socket, every
filesystem parser (mounting an untrusted filesystem image is executing an untrusted
parser in ring 0), every network protocol, every driver bound to a device a user can
plug in. The kernel's size is its security problem.

Dominant bug classes, in the order they appear in CVEs: **use-after-free** (especially
refcount errors and races on teardown), **out-of-bounds read/write**, **race conditions /
double-free**, **integer overflow feeding a size calculation**, **type confusion**, and
**info leaks** (uninitialized kernel memory copied to userspace — always
`memset` structs you `copy_to_user`, and mind the padding).

### 14.2 The defenses

| Mechanism | What it does |
|---|---|
| **KASLR** / KPTI | Randomize kernel base; separate page tables (Meltdown) |
| **SMEP / SMAP** (x86), PAN/PXN (arm64) | Kernel can't execute or access user pages accidentally |
| **Stack protector**, `CONFIG_STACKLEAK` | Canaries; erase kernel stack on syscall return |
| **`CONFIG_FORTIFY_SOURCE`** | Compile-time and runtime bounds checks on str/mem functions |
| **`CONFIG_RANDSTRUCT`**, `CONFIG_STRUCTLEAK` | Randomize struct layout; zero-init |
| **CFI** (`CONFIG_CFI_CLANG`), arm64 **BTI/PAC**, x86 **IBT** | Control-flow integrity |
| **Lockdown LSM** | `integrity`/`confidentiality` modes: block `/dev/mem`, kexec of unsigned images, some BPF, some MSR writes, hibernation. **Auto-enabled under Secure Boot** |
| **Module signing** (`module.sig_enforce`) | Only signed modules load |
| **seccomp-bpf** | Per-process syscall filter. **The single most effective userspace sandbox primitive** |
| **LSMs**: SELinux, AppArmor, Smack, Tomoyo, **Landlock**, **BPF-LSM**, Yama, IMA/EVM | Mandatory access control. Stackable since 5.1 (`lsm=` on the cmdline) |
| **Landlock** | **Unprivileged** sandboxing — a process can restrict *itself* without root. Genuinely new capability |
| Namespaces + cgroups | Isolation and resource bounds (§7.3 → `linux-syscalls-ebpf-boot-and-init`) |

**Sysctls worth knowing** (`/proc/sys/kernel/`, `/proc/sys/net/`):
```
kernel.kptr_restrict=2            # hide kernel pointers from /proc
kernel.dmesg_restrict=1           # dmesg needs CAP_SYSLOG
kernel.perf_event_paranoid=3      # restrict perf
kernel.unprivileged_bpf_disabled=1
kernel.yama.ptrace_scope=1        # only ptrace descendants (2 = admin only)
kernel.io_uring_disabled=2        # see §4.3
kernel.kexec_load_disabled=1
user.max_user_namespaces=0        # if you don't need rootless containers
vm.mmap_min_addr=65536            # blocks NULL-deref exploit mapping
fs.protected_symlinks=1  fs.protected_hardlinks=1  fs.protected_fifos=2  fs.protected_regular=2
```

**[DURABLE] Reduce surface before adding mitigations.** Blocklist unused modules (Ubuntu
already does some of this), build a config with only what you need, disable unused
protocols and filesystems, and don't expose ioctls you don't need. A driver that isn't
compiled in cannot be exploited.

**Attack-surface note that catches people**: `modprobe` autoloading means an unprivileged
process opening a socket with an obscure protocol family can cause a rarely-audited module
to load. That's how several CVEs became reachable. `install <module> /bin/true` in
`/etc/modprobe.d/` blocks it.

### 14.3 Kernel hardening posture, honestly

- **Run a maintained LTS and take the point releases** (§13.3). This single practice
  beats every mitigation config in expected value.
- **Enable KASAN and lockdep in test, KFENCE in production.**
- **Use seccomp + an LSM for every service** — or use systemd's sandboxing options
  (§7.1 → `linux-syscalls-ebpf-boot-and-init`), which are seccomp and namespaces with a friendlier interface.
- **Threat-model before disabling things.** io_uring, user namespaces, and eBPF are all
  simultaneously large attack surfaces and genuinely valuable features. There is no
  universal right answer, only a right answer for your exposure.

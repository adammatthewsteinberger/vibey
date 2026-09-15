---
name: linux-syscalls-ebpf-boot-and-init
description: "Use when working at the kernel/userspace boundary or on system startup: 'we do not break userspace', syscall mechanics and the ABI, io_uring, what eBPF actually is (the verifier, maps, program types) and sched_ext (writing a CPU scheduler in BPF), the boot chain (firmware → bootloader → kernel → init, Secure Boot, initramfs), systemd as the reference userland and its sandboxing directives, cgroup v2, and namespaces — what a container actually is."
---

# Linux Kernel & Shell: Syscalls and the ABI, eBPF and sched_ext, Boot, Init, cgroups, and Containers

> **Part 2 of 5** of the *OS Development — Linux Kernel and Shell* reference (plugin `os-development-kernel-shell`), covering §4–§7. Sibling skills: `linux-kernel-architecture-and-code` (§0–§3), `linux-shell-scripting-and-userland` (§8–§11), `linux-kernel-debugging-process-and-hardening` (§12–§14), `linux-kernel-shell-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §4. Syscalls and the Userspace ABI

### 4.1 "We do not break userspace"

**[DURABLE — the kernel's foundational social contract.]** If a change makes a working
userspace program stop working, it is a kernel regression and gets reverted, regardless
of whether the program was relying on documented behaviour. Linus enforces this
personally and the mailing-list archives are full of it.

Practical consequences:
- Syscall numbers and semantics are permanent.
- `struct` layouts in `include/uapi/` are permanent. **Extend with padding fields and a
  size/flags field designed in from the start** — the modern pattern
  (`sched_setattr`, `openat2`, `clone3`, `bpf`) passes a struct plus its size so the
  kernel can distinguish old callers from new.
- New functionality goes in new syscalls or new flags, not changed behaviour.
- `/sys` and `/proc` output formats are ABI once shipped. Adding a column to a
  space-separated file breaks parsers and has caused real reverts.

### 4.2 Mechanics

```
userspace → libc wrapper → syscall instruction (x86-64: `syscall`, arm64: `svc`)
  → arch entry (arch/x86/entry/) → sys_call_table → SYSCALL_DEFINEn(name, ...)
    → work → return negative errno on failure
      → libc sets errno = -ret, returns -1
```
- **vDSO** (`linux-vdso.so.1`) is a small shared object the kernel maps into every
  process so hot, harmless calls (`clock_gettime`, `gettimeofday`, `getcpu`) can be
  serviced **without a syscall at all**. If you're wondering why `clock_gettime` costs
  ~20 ns, this is why.
- `SYSCALL_DEFINE`, `__user` annotations, `copy_from_user`/`copy_to_user` (which can
  fault and therefore can sleep — never under a spinlock), and `access_ok()`.

> **⚠️ GOTCHA — TOCTOU on userspace memory.** Never read a userspace value twice and
> assume it's the same. Copy it into kernel memory once, validate the copy, and use the
> copy. Userspace can change it between your check and your use — this is a classic
> privilege-escalation pattern.

### 4.3 io_uring — the modern async I/O interface, and its reputation

`io_uring` (kernel 5.1+, Jens Axboe) uses shared submission and completion ring buffers
so batches of I/O can be submitted and reaped **without syscalls per operation**. It is
genuinely fast and now underpins high-performance storage and networking userspace.

**It is also the kernel's most notorious recent attack surface.** Google reported that
**~60% of kernel exploit submissions to its VRP in one period targeted io_uring**, paying
out roughly **$1M** in io_uring bounties out of ~$1.8M total for kernel exploits.
Consequences: Google **disabled io_uring in ChromeOS**, restricted it on Android via
seccomp-bpf and SELinux, and containerd's default seccomp profile disallows io_uring
syscalls. A published proof-of-concept **rootkit performs all its operations through
io_uring specifically to evade syscall-based monitoring** — which is the structural
problem: **you cannot write fine-grained seccomp filters for io_uring**, because the
actual operations are opaque to BPF at the syscall boundary. It's effectively all-or-
nothing.

**Practical control:** `sysctl kernel.io_uring_disabled=2` disables it entirely
(`=1` restricts to a group). The trade-off is real — some PostgreSQL-style I/O-heavy
benchmarks claim 2–3× gains. **Decide from a threat model, not a benchmark or a
headline.**

---

## §5. eBPF and sched_ext

### 5.1 What eBPF actually is

A **verified, JIT-compiled, sandboxed in-kernel VM.** You compile restricted C (or Rust)
to BPF bytecode, the kernel's **verifier** proves it terminates and accesses only memory
it's allowed to, and it's JITed to native code and attached to a hook.

**The verifier's guarantees** [DURABLE]: it does a DAG check to reject loops and
unreachable code (bounded loops are allowed in modern kernels), then symbolically
executes every path tracking register types and value ranges. It rejects reads of
uninitialized registers, out-of-bounds access, invalid pointer arithmetic, and unbounded
loops. **This is what makes it safe to let unprivileged-ish code run in ring 0.**

**Attach points**: kprobes/kretprobes, fentry/fexit (BTF-based, cheaper), tracepoints,
USDT, perf events, LSM hooks (**BPF-LSM**), XDP (at the driver, before `skb` allocation —
the fastest packet path in Linux), tc/clsact, cgroup hooks, socket ops, and
**struct_ops** (implementing a kernel interface in BPF — used for TCP congestion control,
HID drivers, and schedulers).

**Key infrastructure**: **BTF** (BPF Type Format — kernel type info, requires
`CONFIG_DEBUG_INFO_BTF=y`), **CO-RE** (Compile Once, Run Everywhere — relocations against
the running kernel's BTF, which is what makes portable BPF binaries possible), maps
(hash, array, ringbuf, per-CPU, LRU), `libbpf`, `bpftool`, and the higher-level
`bpftrace`, `bcc`, and Rust's `aya`.

```c
// A minimal CO-RE tracing program (libbpf skeleton style)
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct { __uint(type, BPF_MAP_TYPE_RINGBUF); __uint(max_entries, 256*1024); } rb SEC(".maps");

SEC("fentry/do_unlinkat")           // fentry: cheaper than kprobe, needs BTF
int BPF_PROG(on_unlink, int dfd, struct filename *name)
{
        struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
        if (!e) return 0;                                  // ALWAYS check
        e->pid = bpf_get_current_pid_tgid() >> 32;
        bpf_probe_read_kernel_str(&e->file, sizeof(e->file), name->name);
        bpf_ringbuf_submit(e, 0);
        return 0;
}
char LICENSE[] SEC("license") = "GPL";   // required for most helpers
```

> **⚠️ GOTCHA — "the verifier rejected my program" is the whole BPF learning curve.**
> Common causes: an unchecked pointer (every map lookup can return NULL), a loop the
> verifier can't bound, exceeding the instruction/complexity limit, reading kernel memory
> without `bpf_probe_read_kernel`, or a helper not allowed in that program type. Read the
> verifier log from the *bottom* — the last lines are usually the real problem.

### 5.2 sched_ext — writing a CPU scheduler in BPF

**[VERSIONED] Merged in Linux 6.12.** `sched_ext` is a scheduling class that delegates
policy to a BPF program via `struct_ops`, letting you **load and hot-swap a CPU scheduler
at runtime without rebooting**. This is a genuinely significant change: scheduler
experimentation used to require a kernel patch, a build, and a reboot.

Concepts: **DSQs** (dispatch queues) mediate tasks between core kernel and the BPF
scheduler; callbacks include `select_cpu`, `enqueue`, `dispatch`, `running`, `stopping`.
**Safety mechanisms are the point**: if the BPF scheduler errors, stalls a runnable task,
or you hit SysRq-S, **the kernel aborts it and reverts every task to the fair class**.
`SCX_OPS_SWITCH_PARTIAL` lets only `SCHED_EXT` tasks use it while everything else stays
on EEVDF.

Required config: `CONFIG_BPF=y CONFIG_SCHED_CLASS_EXT=y CONFIG_BPF_SYSCALL=y
CONFIG_BPF_JIT=y CONFIG_DEBUG_INFO_BTF=y`. **`CONFIG_DEBUG_INFO_BTF` matters more than it
looks** — without BTF, CO-RE relocations can't resolve and every BPF scheduler fails to
load with an unhelpful "relocation failed."

The `scx` project ships real schedulers: `scx_simple`, `scx_rusty` (hybrid Rust userspace
+ BPF hot path), `scx_lavd` (latency-aware, gaming), `scx_bpfland`, `scx_layered` (match
tasks into layers by name/cgroup/nice and give each layer a policy). **Meta has deployed
sched_ext schedulers in production for web workloads.**

Distro status (2026): Fedora, Arch, CachyOS, NixOS unstable, and openSUSE Tumbleweed ship
SCX-enabled kernels; Ubuntu 26.04 LTS has it in the HWE kernel but not GA; Debian stable
needs backports or a self-build. Check with `cat /sys/kernel/sched_ext/state` and
`/sys/kernel/sched_ext/root/ops`.

---

## §6. Boot

### 6.1 The chain

```
Power on
 → Firmware (UEFI, or legacy BIOS, or U-Boot/SPL on embedded, or coreboot)
    → optional: TF-A / BL31 on arm64
    → Bootloader: GRUB2 | systemd-boot | U-Boot | rEFInd | direct EFI stub
       → Kernel image (bzImage / Image / zImage+DTB) + kernel command line
          → decompress, set up paging, arch init, start_kernel()
             → init subsystems, mount initramfs (a cpio archive in RAM)
                → /init in the initramfs: load modules, assemble RAID/LVM,
                  unlock LUKS, find the real root
                   → switch_root / pivot_root to the real rootfs
                      → exec /sbin/init (PID 1: systemd, OpenRC, runit, s6, busybox)
                         → units/services → login (getty / display manager)
```

**Things worth knowing precisely:**
- **The initramfs exists because of a bootstrapping problem**: the kernel needs a driver
  or a decryption key to mount root, and that driver is a module living on root. The
  initramfs is a self-contained RAM filesystem with just enough to solve it.
- **UKI (Unified Kernel Image)** is the modern packaging: kernel + initramfs + command
  line + signature in **one signed EFI binary**. This closes a real gap — with a separate
  initramfs, Secure Boot verified the kernel but not the initramfs or the command line.
  `systemd-stub` and `ukify` build them; **note the version coupling: systemd-stub v258+
  requires ukify v257.9/v258+**.
- **Secure Boot** chain: firmware db/KEK/PK → shim (signed by Microsoft, holds the
  distro key) → GRUB/systemd-boot → kernel → **kernel module signature enforcement**
  (`module.sig_enforce`) → **lockdown LSM** (§14.2 → `linux-kernel-debugging-process-and-hardening`). Each link is only as good as the
  next; an unsigned initramfs or an unlocked-down kernel breaks it.
- **The kernel command line** is where you'll spend real time: `root=`, `ro`,
  `console=ttyS0,115200`, `quiet`, `nomodeset`, `init=/bin/sh` (the recovery escape
  hatch), `systemd.unit=rescue.target`, `isolcpus=`/`nohz_full=` for RT,
  `kernel.io_uring_disabled` (sysctl, not cmdline), `lsm=`, `slub_debug=`.
- **Boot debugging**: `earlyprintk=`/`earlycon=` gets you output before the real console
  is up. This is the difference between "black screen" and "a stack trace."

---

## §7. Init, cgroups, and Containers

### 7.1 systemd — like it or not, the reference userland

**[VERSIONED — v258/v259/v260 removed a lot, so check your target.]**

Core model: **units** (`.service`, `.socket`, `.timer`, `.mount`, `.target`, `.slice`,
`.path`, `.device`) with declarative dependencies, socket activation, cgroup-based
resource control, and a journal. PID 1 supervises; `systemd --user` does the same
per-session.

```ini
# /etc/systemd/system/myapp.service — a hardened service, which is the point
[Unit]
Description=My App
After=network-online.target
Wants=network-online.target

[Service]
Type=notify                       # exec | simple | forking | oneshot | notify | idle
ExecStart=/usr/bin/myapp
Restart=on-failure
RestartSec=5s
User=myapp
DynamicUser=yes                   # transient UID, no /etc/passwd entry needed

# Sandboxing — systemd's most underused feature. Check with `systemd-analyze security`
NoNewPrivileges=yes
ProtectSystem=strict              # /usr, /boot, /etc read-only
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
RestrictNamespaces=yes
SystemCallFilter=@system-service
SystemCallArchitectures=native
MemoryDenyWriteExecute=yes
StateDirectory=myapp              # → /var/lib/myapp, created with right ownership

[Install]
WantedBy=multi-user.target
```
`systemd-analyze security myapp.service` scores this and tells you what's missing. It is
the cheapest hardening win available on a modern Linux system.

**Recent removals that will break things** [VERSIONED]:
- **v258 removed cgroup v1 entirely** (legacy and hybrid hierarchies). cgroup v2 only.
  Monitoring tools with hardcoded v1 paths break.
- **v258 removed System V runlevel compatibility** (`initctl`, `runlevel`, `telinit`) and
  made OpenSSL the only crypto backend for resolved/importd.
- **v259 deprecated SysV service script support**; **v260 (2026) removed
  `systemd-sysv-generator`, `systemd-rc-local-generator`, and `systemd-sysv-install`.**
  A package still shipping only an LSB init script now silently does nothing.
- **v259 made journald persistent by default** (previously it only wrote to disk if
  `/var/log/journal` existed) and **dropped iptables/libiptc NAT in networkd and nspawn —
  nftables only.**
- v260 raises minimums to kernel 5.10, glibc 2.34, OpenSSL 3.0, Python 3.9.

**[CONTESTED] systemd.** *For:* declarative dependencies, socket activation, correct
process supervision (no more PID files and double-forking), cgroup integration, unified
logging, and the security sandboxing above — all things shell-script init genuinely could
not do reliably. *Against:* scope creep into DNS, NTP, boot, containers, home
directories, and login; a binary log format; tight coupling that makes non-systemd
distros progressively harder to maintain; and a design philosophy that trades Unix
composability for integration. Both sides have shipped working systems for a decade;
this argument will not be resolved by anyone reading this document.

### 7.2 cgroup v2

**[DURABLE] Unified hierarchy** (v1's per-controller hierarchies are gone). Controllers:
`cpu`, `memory`, `io`, `pids`, `cpuset`, `hugetlb`, `rdma`, `misc`.

Key files: `cpu.max` (quota/period), `cpu.weight`, `memory.max` (hard limit → OOM),
**`memory.high`** (throttle + reclaim pressure, no kill — usually what you actually
want), `memory.low` (protection), `io.max`, `pids.max`, and **`*.pressure`** (PSI per
cgroup — the best signal for "this workload is starved").

**The "no internal processes" rule**: a cgroup with children can't have processes of its
own (except the root). This trips up hand-rolled cgroup management constantly.

### 7.3 Namespaces — what a container actually is

| Namespace | Isolates |
|---|---|
| `mnt` | Mount table |
| `pid` | Process IDs (your PID 1 is the container's init) |
| `net` | Network stack: interfaces, routes, netfilter, ports |
| `ipc` | SysV IPC, POSIX message queues |
| `uts` | Hostname, domainname |
| `user` | **UID/GID mapping — the basis of rootless containers** |
| `cgroup` | cgroup root view |
| `time` | Boot/monotonic clock offsets |

**[DURABLE] "Container" is not a kernel object.** It is a process created with
namespace flags, confined by cgroups, restricted by seccomp and an LSM, using
**overlayfs** for the layered image, and usually **pivot_root**ed into it. Docker, Podman,
LXC, and systemd-nspawn are all different userspace assemblies of the same primitives.
Knowing this is the difference between debugging a container and being confused by one.

**User namespaces** are how rootless containers work: root inside maps to an unprivileged
UID outside. They are also historically a **major source of privilege-escalation CVEs**,
because they let unprivileged users reach kernel code paths that previously required root.
Several distros restrict them (`kernel.unprivileged_userns_clone`,
`user.max_user_namespaces`) — a live security-vs-usability tradeoff.

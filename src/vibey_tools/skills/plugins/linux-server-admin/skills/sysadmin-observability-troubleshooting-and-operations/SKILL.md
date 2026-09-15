---
name: sysadmin-observability-troubleshooting-and-operations
description: "Use when a server is slow, broken, or needs operating at scale: performance methodology rather than tool trivia, reading memory correctly, CPU and profiling, eBPF as the modern observability layer, metrics and logs, a troubleshooting sequence and the four-places-state problem, containers and the namespaces and cgroups underneath them, configuration management and automation, and backup and recovery that actually restores."
---

# Linux Server Administration: Observability, Troubleshooting, Containers, Automation, and Backup

> **Part 4 of 5** of the *Linux Server Administration* reference (plugin `linux-server-admin`), covering §10–§14. Sibling skills: `sysadmin-filesystem-permissions-and-processes` (§0–§3), `sysadmin-systemd-storage-and-networking` (§4–§6), `sysadmin-packages-boot-and-hardening` (§7–§9), `sysadmin-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The core — POSIX semantics, kernel subsystems, systemd, networking — is stable; distribution lifecycle dates and kernel LTS windows move. See §17 → `sysadmin-reference` for the dated table.

> **How to read this.** Command-dense and operational. Assumes you can already use a
> shell; this is about understanding the machine well enough to fix it under pressure.
>
> **⚠️ GOTCHA** boxes mark what causes outages or silent data loss.
>
> **The three mental models that make everything else make sense:**
> 1. **⚠️ Everything is a file descriptor, and the kernel is the only thing that can
>    actually do anything.** Userspace asks via syscalls. **When something "doesn't work,"
>    the question is always: which syscall failed, and what errno?** — and `strace` will
>    tell you (§12).
> 2. **⚠️ State lives in four places and they disagree**: what's on disk, what's in the
>    kernel's memory, what the running process loaded at start, and what your config
>    management thinks. **Most confusing bugs are a disagreement between these** (§11.2).
> 3. **⚠️ A server is a cache of your configuration management, not a pet.** If you cannot
>    rebuild it from source control, you don't have a server — you have an artifact
>    nobody understands (§15 → `sysadmin-reference`).

---

## §10. Observability and Performance

### 10.1 The method, not the tools
**⚠️ Brendan Gregg's USE method**, applied to every resource (CPU, memory, disk, network):
```
Utilization   — how busy
Saturation    — ⚠️ queued work; usually the number that actually matters
Errors        — ⚠️ check these FIRST; they're cheap and often decisive
```
**And the 60-second triage:**
```
uptime              load trend
dmesg -T | tail     ⚠️ OOM kills, hardware errors, resets
vmstat 1            r, b, si/so (⚠️ swap!), us/sy/id/wa
mpstat -P ALL 1     ⚠️ per-CPU — one hot core is a different problem
pidstat 1           per-process CPU
iostat -xz 1        await, aqu-sz, %util
free -m             ⚠️ read "available", not "free"
sar -n DEV 1        network throughput
sar -n TCP,ETCP 1   retransmits, errors
top / htop
```

### 10.2 Memory, read correctly
> **⚠️ GOTCHA — "free" memory is not the number you want.** Linux uses free RAM for page
> cache deliberately. **A healthy busy server shows very little free memory and that is
> correct.** **Read `available`** — it accounts for reclaimable cache.
> ⚠️ **Panicking about low "free" and adding RAM is the most common false diagnosis in
> Linux administration.**

**Real pressure signals**: **swap in/out activity** (`si`/`so` in vmstat — ⚠️ **not swap
*used*, which can be stale and harmless**), **OOM kills in dmesg**, and
**PSI** — `cat /proc/pressure/{cpu,memory,io}` — ⚠️ **which is the modern, direct measure
of contention and is far better than inferring from utilization.**

### 10.3 CPU and profiling
`perf top`, `perf record -F 99 -g -p PID -- sleep 30` then `perf report`.
**Flame graphs** for stack aggregation. ⚠️ **`%steal` in a VM means the hypervisor is
taking your CPU — no amount of guest tuning fixes it.**

### 10.4 eBPF — the modern layer
**⚠️ Why it displaced the older tools**: `strace` uses ptrace and **stops the process on
every syscall** — profiling a high-throughput service with it is an incident waiting to
happen. **eBPF runs verified, sandboxed programs inside the kernel with near-zero
overhead, no module loading, no reboots.** SystemTap needed debug symbols and compiled
kernel modules; **eBPF with CO-RE (Compile Once, Run Everywhere) is portable.**

```
# BCC tools (apt install bpfcc-tools / dnf install bcc-tools) — 80+ ready scripts
execsnoop      ⚠️ every process exec — brilliant for "what keeps spawning?"
opensnoop      file opens — "which config is it ACTUALLY reading?"
biosnoop       block I/O with latency per operation
biolatency     I/O latency histogram
tcplife        TCP sessions with duration and bytes
tcpconnect / tcpaccept / tcpretrans
runqlat        ⚠️ scheduler run-queue latency — CPU saturation without high utilization
cachestat      page cache hit ratio
memleak        outstanding allocations
profile        CPU stack sampling
```
```
# bpftrace — awk for the kernel
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'
bpftrace -e 'tracepoint:syscalls:sys_enter_read /comm=="nginx"/ { @ = hist(args->count); }'
bpftrace -l 'tracepoint:syscalls:*'     ⚠️ list available probes
```
**⚠️ Two cautions**: overhead is low but **not zero — tracing every scheduler context
switch on a busy box will hurt**; filter or sample. And **kprobes attach to kernel
internals that can change between versions** — ⚠️ **prefer tracepoints (stable API) over
kprobes where one exists.**

**Adjacent**: **Cilium/Hubble** (Kubernetes networking and observability), **Falco**
(runtime security), **Pixie**, **Inspektor Gadget**.

### 10.5 Metrics and logs
**Prometheus + node_exporter + Grafana** is the default stack; **Loki** or the
**ELK/OpenSearch** stack for logs; **OpenTelemetry** for traces.
**⚠️ Alert on symptoms users feel** (latency, error rate, saturation), **not on causes**
(CPU 80%). **Every alert should have a runbook, and an alert nobody acts on should be
deleted.**

---

## §11. Troubleshooting Methodology

### 11.1 The sequence
```
1. ⚠️ What CHANGED?  deploys, package updates, config management runs, certs, DNS,
                      upstream, traffic pattern. Check this BEFORE theorizing.
2. Define the symptom precisely — who, what, since when, how often, all or some?
3. Bisect the stack:  client → DNS → network → LB → host → service → dependency → storage
4. Read the errors:   journalctl -p err -b · dmesg -T · the app's own log
5. Form ONE hypothesis, test it cheaply, record the result
6. Fix, verify, and write down what it was
```
**⚠️ The single highest-yield question is "what changed?" and it is the one people skip
while forming theories.**

### 11.2 The four-places-state problem
**⚠️ When behaviour makes no sense, check whether these agree:**
```
On disk           cat the actual file — ⚠️ and check for .rpmnew (§7)
Kernel/live       sysctl -a · ip a · nft list ruleset · systemctl show
Process memory    ⚠️ the process loaded config at START — it may be running old config
                  ls -l /proc/PID/exe · /proc/PID/environ · restart to be sure
Config management ⚠️ is Ansible/Puppet about to revert your manual fix?
```
**⚠️ "I fixed it and it broke again 30 minutes later" is config management reverting you.**

### 11.3 Specific scenarios
**Disk full but `du` disagrees** → ⚠️ **deleted-but-open files: `lsof +L1`** (§1.2 → `sysadmin-filesystem-permissions-and-processes`).
Also check for a filesystem mounted *over* a populated directory hiding its contents.
**Out of inodes** → `df -i` (§1.2 → `sysadmin-filesystem-permissions-and-processes`).
**Service won't start** → `systemctl status -l`, `journalctl -xeu NAME`,
`systemd-analyze verify unit`, ⚠️ **and check SELinux with `ausearch -m avc -ts recent`.**
**Port already in use** → `ss -tulpn | grep :PORT`.
**Slow but idle CPU** → ⚠️ **`runqlat`, PSI, `%steal`, I/O `await`** — saturation without
utilization.
**Intermittent DNS** → ⚠️ **`resolvectl status`, check search domains and `ndots`, compare
`dig @server` against `dig`.**
**Clock drift** → `timedatectl`, `chronyc tracking` — ⚠️ **breaks TLS, Kerberos, and
log correlation in ways that look like other problems.**
**Certificate expiry** → `openssl s_client -connect host:443 </dev/null 2>/dev/null |
openssl x509 -noout -dates`. ⚠️ **Monitor this; it is a fully preventable, recurring
outage cause.**

---

## §12. Containers and Namespaces

**⚠️ A container is not a VM.** It is a normal process with restricted visibility, built
from kernel primitives:
```
Namespaces  mnt, pid, net, ipc, uts, user, cgroup, time   ⚠️ WHAT IT CAN SEE
cgroups v2  cpu, memory, io, pids                          ⚠️ WHAT IT CAN USE
capabilities, seccomp, LSM (SELinux/AppArmor)              ⚠️ WHAT IT CAN DO
overlayfs                                                  layered images
```
```
lsns · nsenter -t PID -n ip a          ⚠️ enter a container's netns from the host
systemd-cgls · systemd-cgtop           cgroup tree and live resource use
cat /proc/PID/cgroup                   which cgroup is this process in
podman / docker / nerdctl · crictl     runtimes
```
**⚠️ The security consequence**: the kernel is **shared**. A kernel vulnerability crosses
the container boundary. **Run rootless (podman, or userns-remap), drop capabilities, apply
seccomp, and never `--privileged` in production.**

**⚠️ Systemd and containers overlap deliberately** — `systemd-nspawn`, and `Delegate=yes`
for cgroup delegation. **A hardened systemd unit (§4.3 → `sysadmin-systemd-storage-and-networking`) gives you most of a container's
isolation without the image.**

---

## §13. Automation and Configuration Management

**⚠️ The principle: the box is disposable, the source of truth is the repo.**
**Ansible** (agentless over SSH, ⚠️ **the low-friction default**), **Puppet/Chef/Salt**
(agent-based, stronger for continuous enforcement), **Terraform/OpenTofu** for
infrastructure, **cloud-init** for first boot, **Packer** for images.

**⚠️ Idempotence is the property that matters** — running twice must equal running once.
**Test with `--check --diff` before applying.**

**Immutable infrastructure** — build an image, deploy it, ⚠️ **never patch in place;
replace.** **Reduces drift to zero, at the cost of build pipeline complexity.**

**⚠️ Practical discipline that pays for itself**: everything in git including `/etc`
(consider `etckeeper`), **change one thing at a time**, **stage before production**, and
**a documented rollback for anything you can't undo in five minutes.**

---

## §14. Backup and Recovery

**⚠️ 3-2-1: three copies, two media, one offsite — and now "one offline or immutable,"
because ransomware targets the backup server first.**

**Tools**: `restic` and `borg` (⚠️ **deduplicating, encrypted, and the sane defaults for
most people**), `rsync` (⚠️ **`--link-dest` for hardlinked incrementals**), `zfs
send`/`btrfs send` for filesystem-native, `tar` for archives.

> **⚠️ GOTCHA — an untested backup is not a backup.** **Schedule restores.** The
> recurring failure modes are: backups silently stopped weeks ago, the encryption key was
> only on the machine that died, the restore takes 40 hours and RTO is 4, and the database
> backup is a file copy of a running database and is therefore corrupt.
> **⚠️ Databases need their own consistent dump or snapshot mechanism** — `pg_dump`,
> `mysqldump --single-transaction`, or a filesystem snapshot with the DB quiesced.

**Document and test**: RPO (how much data can you lose), RTO (how fast must you be back),
and ⚠️ **a written recovery procedure someone who isn't you can follow at 3am.**

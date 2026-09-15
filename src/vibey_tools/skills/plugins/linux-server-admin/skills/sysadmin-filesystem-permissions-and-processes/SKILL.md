---
name: sysadmin-filesystem-permissions-and-processes
description: "Use when working with files, identity or running processes on a Linux server: the filesystem layout, the file semantics that surprise people (hard links, inodes, deleted-but-open files, atime), the special filesystems, users, groups and the permission model stated precisely, capabilities as the modern answer to setuid root, account management, and processes, signals, scheduling and resource limits including cgroups. Includes the router for the whole linux-server-admin reference."
---

# Linux Server Administration: The Filesystem, Users and Permissions, and Processes

> **Part 1 of 5** of the *Linux Server Administration* reference (plugin `linux-server-admin`), covering §0–§3. Sibling skills: `sysadmin-systemd-storage-and-networking` (§4–§6), `sysadmin-packages-boot-and-hardening` (§7–§9), `sysadmin-observability-troubleshooting-and-operations` (§10–§14), `sysadmin-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    tell you (§12 → `sysadmin-observability-troubleshooting-and-operations`).
> 2. **⚠️ State lives in four places and they disagree**: what's on disk, what's in the
>    kernel's memory, what the running process loaded at start, and what your config
>    management thinks. **Most confusing bugs are a disagreement between these** (§11.2 → `sysadmin-observability-troubleshooting-and-operations`).
> 3. **⚠️ A server is a cache of your configuration management, not a pet.** If you cannot
>    rebuild it from source control, you don't have a server — you have an artifact
>    nobody understands (§15 → `sysadmin-reference`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| Filesystem layout and file semantics | §1 |
| **Users, permissions, capabilities** | **§2** |
| Processes, signals, resources | §3 |
| **systemd and journald** | **§4 → `sysadmin-systemd-storage-and-networking`** |
| Storage: block, LVM, filesystems | §5 → `sysadmin-systemd-storage-and-networking` |
| **Networking** | **§6 → `sysadmin-systemd-storage-and-networking`** |
| Packages and distributions | §7 → `sysadmin-packages-boot-and-hardening` |
| Boot process | §8 → `sysadmin-packages-boot-and-hardening` |
| **Security hardening** | **§9 → `sysadmin-packages-boot-and-hardening`** |
| SSH | §9.4 → `sysadmin-packages-boot-and-hardening` |
| **Observability and performance** | **§10 → `sysadmin-observability-troubleshooting-and-operations`** |
| eBPF | §10.4 → `sysadmin-observability-troubleshooting-and-operations` |
| **Troubleshooting methodology** | **§11 → `sysadmin-observability-troubleshooting-and-operations`** |
| Containers and namespaces | §12 → `sysadmin-observability-troubleshooting-and-operations` |
| Automation and config management | §13 → `sysadmin-observability-troubleshooting-and-operations` |
| Backup and recovery | §14 → `sysadmin-observability-troubleshooting-and-operations` |
| Anti-patterns | §15 → `sysadmin-reference` |
| Numbers and limits | §16 → `sysadmin-reference` |
| **Lifecycle dates** | **§17 → `sysadmin-reference`** |
| Books | §18 → `sysadmin-reference` |
| Command reference | §19 → `sysadmin-reference` |

---

## §1. Filesystem and Files

### 1.1 Layout (FHS)
```
/etc      configuration          ⚠️ this is what you back up
/var      variable data — logs, spool, databases, containers
/usr      read-only program data (/usr/bin, /usr/lib, /usr/share)
/opt      third-party packages
/srv      service data
/home     users
/tmp      ⚠️ often tmpfs (RAM), cleared on boot
/run      ⚠️ tmpfs, runtime state, PIDs, sockets — gone on reboot BY DESIGN
/proc     kernel/process interface (virtual)
/sys      kernel object interface (virtual)
/dev      device nodes
/boot     kernel, initramfs, bootloader
```
**⚠️ `/usr` merge**: `/bin`, `/sbin`, `/lib` are symlinks into `/usr` on modern systems.
Stop treating them as distinct.

### 1.2 File semantics that surprise people
**Inodes hold metadata; directory entries map names to inodes.** Consequences:
- **⚠️ Deleting a file with an open descriptor doesn't free the space** — the inode
  survives until the last FD closes. **This is the classic "disk full but `du` shows
  nothing" incident.** Find it with `lsof +L1` or `lsof | grep deleted`, then restart the
  holder or truncate via `/proc/PID/fd/N`.
- **Hard links** share an inode (⚠️ **same filesystem only**); **symlinks** are separate
  inodes containing a path.
- **⚠️ You can exhaust inodes while free space remains** — `df -i`. Common with mail
  spools and small-file caches.
- **`rename(2)` is atomic within a filesystem** — ⚠️ **which is why "write to temp, fsync,
  rename" is the correct way to update a config file safely.**

**⚠️ Durability**: `write()` returns when data is in the page cache, not on disk.
**`fsync()` is what makes it durable**, and **you must also fsync the parent directory**
for the rename to survive a crash. **This is where people lose data.**

### 1.3 Special filesystems worth knowing
```
/proc/PID/{cmdline,environ,fd/,maps,status,limits,cgroup}   ⚠️ per-process truth
/proc/{meminfo,loadavg,mounts,net/,sys/}
/sys/class/net/*/statistics/                                interface counters
/sys/block/*/queue/{scheduler,rotational,nr_requests}
/proc/sys/...  ← the same tree sysctl writes to
```
**⚠️ `/proc/PID/limits` shows the actual limits of a running process** — not what your
shell has, not what the unit file says. **When a limit seems unapplied, check here.**

---

## §2. Users, Permissions, Capabilities

### 2.1 The basics, precisely
```
rwx rwx rwx    user / group / other
4=r 2=w 1=x
```
**⚠️ On a directory**: `x` = may traverse into it (needed to access anything inside);
`r` = may *list* it; `w` = may create/delete entries. **⚠️ Delete permission on a file
comes from the DIRECTORY's `w`, not the file's** — which is why you can delete a file you
can't write.

**Special bits**: **setuid** (4000 — runs as file owner), **setgid** (2000 — on a
directory, ⚠️ **new files inherit the group; the standard trick for shared directories**),
**sticky** (1000 — ⚠️ **on `/tmp`: only the owner may delete their own files**).

**⚠️ umask subtracts**: default 022 gives 755 for dirs, 644 for files. Services often set
their own.

**ACLs** for finer control: `getfacl` / `setfacl -m u:alice:rw file`.
⚠️ **`ls -l` shows a `+` when ACLs exist — and people miss it.**

### 2.2 Capabilities — the modern answer to setuid root
**⚠️ Root is decomposed into ~40 capabilities.** Grant one instead of everything:
```
getcap /usr/bin/ping                      → cap_net_raw+ep
setcap cap_net_bind_service=+ep /path/to/binary   ⚠️ bind <1024 without root
capsh --print                             what does this shell have
```
**Common ones**: `CAP_NET_BIND_SERVICE`, `CAP_NET_ADMIN`, `CAP_SYS_ADMIN`
(⚠️ **effectively root — "the new root"; granting it is not hardening**), `CAP_DAC_OVERRIDE`,
`CAP_CHOWN`, `CAP_SETUID`.

**⚠️ In systemd, prefer `AmbientCapabilities=` over a setuid binary** (§4.3 → `sysadmin-systemd-storage-and-networking`) — it's
auditable and scoped to the unit.

### 2.3 Accounts
`/etc/passwd` (⚠️ **no passwords — they're in `/etc/shadow`**), `/etc/group`,
`/etc/sudoers` (⚠️ **edit with `visudo` only — a syntax error locks you out of sudo**).
**Service accounts should be `--system --shell /usr/sbin/nologin --no-create-home`.**
**PAM** (`/etc/pam.d/`) governs authentication, session setup, and limits —
⚠️ **`pam_limits` is why `/etc/security/limits.conf` applies to login sessions but NOT to
systemd services** (§4.3 → `sysadmin-systemd-storage-and-networking`).

---

## §3. Processes and Resources

**States**: R (running/runnable), S (interruptible sleep), **D (uninterruptible sleep —
⚠️ usually blocked on I/O, and cannot be killed; a pile of D-state processes means a
storage problem)**, Z (zombie — ⚠️ **exited, parent hasn't reaped; harmless unless
numerous, and the fix is fixing or restarting the parent**), T (stopped).

**Signals worth knowing**:
```
SIGTERM (15)  ⚠️ polite: "shut down" — catchable, the default for kill and systemd
SIGKILL  (9)  ⚠️ uncatchable, no cleanup — data loss risk, use last
SIGHUP   (1)  traditionally "reload config"
SIGINT   (2)  Ctrl-C
SIGSTOP/SIGCONT  pause/resume
SIGUSR1/2     application-defined (⚠️ nginx: reopen logs / graceful)
```
**⚠️ `kill -9` as a first move is a bad habit.** It skips flush-and-close. Try TERM, wait,
then KILL.

**Load average** is **runnable + uninterruptible (D-state)** processes averaged over
1/5/15 min. ⚠️ **Because D-state counts, high load on Linux can mean I/O wait, not CPU
saturation — this differs from other Unixes and is a persistent source of misdiagnosis.**
**Divide by core count for a rough utilization read.**

**Limits**: `ulimit -a` for the shell, ⚠️ **`/proc/PID/limits` for reality**, and
`LimitNOFILE=` etc. in unit files for services (§4.3 → `sysadmin-systemd-storage-and-networking`).

**⚠️ The OOM killer**: when memory is exhausted, the kernel picks a victim by `oom_score`.
Check `dmesg | grep -i oom` or `journalctl -k | grep -i oom`. **Tune with
`oom_score_adj`; in systemd, `OOMScoreAdjust=` and `MemoryMax=`.** ⚠️ **Overcommit
(`vm.overcommit_memory`) means malloc can succeed and the OOM killer fires later — the
allocation is not the failure point.**

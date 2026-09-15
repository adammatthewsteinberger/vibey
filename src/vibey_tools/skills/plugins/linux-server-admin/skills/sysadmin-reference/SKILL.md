---
name: sysadmin-reference
description: "Use when checking a sysadmin anti-pattern, looking up a kernel or system limit, confirming a distribution lifecycle or kernel LTS date (verified August 2026), finding the books, or needing the fifteen commands that carry most of the load, a first-five-minutes routine for an unfamiliar sick box, and a pre-change checklist. Companion to the other linux-server-admin skills."
---

# Linux Server Administration: Anti-Patterns, Limits, Lifecycle Dates, and Command Reference

> **Part 5 of 5** of the *Linux Server Administration* reference (plugin `linux-server-admin`), covering §15–§20. Sibling skills: `sysadmin-filesystem-permissions-and-processes` (§0–§3), `sysadmin-systemd-storage-and-networking` (§4–§6), `sysadmin-packages-boot-and-hardening` (§7–§9), `sysadmin-observability-troubleshooting-and-operations` (§10–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The core — POSIX semantics, kernel subsystems, systemd, networking — is stable; distribution lifecycle dates and kernel LTS windows move. See §17 below for the dated table.

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
>    nobody understands (§15).

---

## §15. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| **Disabling SELinux** | ⚠️ **Fix the label. Two commands** (§9.2 → `sysadmin-packages-boot-and-hardening`) |
| Editing vendor unit files in `/usr/lib` | ⚠️ **Overwritten on update. Use `systemctl edit`** (§4.1 → `sysadmin-systemd-storage-and-networking`) |
| Forgetting `daemon-reload` | Your edit isn't loaded (§4.1 → `sysadmin-systemd-storage-and-networking`) |
| `Requires=` without `After=` | ⚠️ **Starts in parallel; fails** (§4.2 → `sysadmin-systemd-storage-and-networking`) |
| `/dev/sdX` in fstab | ⚠️ **Names aren't stable. Use UUID** (§5.3 → `sysadmin-systemd-storage-and-networking`) |
| Rebooting without `mount -a` | ⚠️ **Stranded at emergency shell** (§5.3 → `sysadmin-systemd-storage-and-networking`) |
| `kill -9` first | Skips flush and cleanup (§3 → `sysadmin-filesystem-permissions-and-processes`) |
| Panicking about low "free" memory | ⚠️ **Read `available`. Cache is doing its job** (§10.2 → `sysadmin-observability-troubleshooting-and-operations`) |
| Enabling a firewall before allowing SSH | ⚠️ **Lockout** (§6.3 → `sysadmin-systemd-storage-and-networking`) |
| Changing firewall rules with no rollback timer | Same (§6.3 → `sysadmin-systemd-storage-and-networking`) |
| Password SSH auth | ⚠️ **Keys only is the biggest single win** (§9.4 → `sysadmin-packages-boot-and-hardening`) |
| Reloading sshd without `sshd -t` | Console trip (§9.4 → `sysadmin-packages-boot-and-hardening`) |
| `net.ipv4.tcp_tw_recycle` | ⚠️ **Removed from the kernel; broke NAT clients** (§6.4 → `sysadmin-systemd-storage-and-networking`) |
| Ignoring `.rpmnew`/`.dpkg-dist` | ⚠️ **Running old config plus a file you never read** (§7 → `sysadmin-packages-boot-and-hardening`) |
| Using `strace` on a hot production process | ⚠️ **ptrace stops it on every syscall** (§10.4 → `sysadmin-observability-troubleshooting-and-operations`) |
| Treating LVM snapshots as backups | They fill and break (§5.2 → `sysadmin-systemd-storage-and-networking`) |
| Untested backups | ⚠️ **Not backups** (§14 → `sysadmin-observability-troubleshooting-and-operations`) |
| File-copying a running database | ⚠️ **Corrupt restore** (§14 → `sysadmin-observability-troubleshooting-and-operations`) |
| `--privileged` containers | Kernel is shared (§12 → `sysadmin-observability-troubleshooting-and-operations`) |
| Alerting on CPU% instead of symptoms | Noise, then ignored alerts (§10.5 → `sysadmin-observability-troubleshooting-and-operations`) |
| Manual fixes with config management running | ⚠️ **Reverted in 30 minutes** (§11.2 → `sysadmin-observability-troubleshooting-and-operations`) |
| Theorizing before asking "what changed?" | ⚠️ **The highest-yield question** (§11.1 → `sysadmin-observability-troubleshooting-and-operations`) |
| Volatile journal on a production box | ⚠️ **No logs from the crash** (§4.4 → `sysadmin-systemd-storage-and-networking`) |
| Running as root because it's easier | Capabilities and systemd sandboxing exist (§2.2 → `sysadmin-filesystem-permissions-and-processes`, §4.3 → `sysadmin-systemd-storage-and-networking`) |
| `ifconfig`/`netstat` muscle memory | Deprecated; `ip`/`ss` show more (§6.1 → `sysadmin-systemd-storage-and-networking`) |

---

## §16. Numbers and Limits

```
SIGNALS      TERM 15 · KILL 9 · HUP 1 · INT 2 · QUIT 3 · USR1 10 · USR2 12
PERMISSIONS  r4 w2 x1 · setuid 4000 · setgid 2000 · sticky 1000 · umask 022
EXIT CODES   0 ok · 1 general · 2 misuse · 126 not executable · 127 not found
             ⚠️ 128+N = killed by signal N (137 = SIGKILL, 143 = SIGTERM)
PORTS        <1024 privileged (⚠️ or CAP_NET_BIND_SERVICE)
             22 SSH · 25 SMTP · 53 DNS · 80/443 HTTP(S) · 123 NTP · 3306 MySQL
             5432 Postgres · 6379 Redis · 9090 Prometheus
LIMITS       Default nofile often 1024 ⚠️ (far too low for servers — set 65535)
             PID max default 4194304 on 64-bit
             Ephemeral ports default 32768–60999
LOAD         Divide by core count; ⚠️ includes D-state (I/O), not just CPU
FS           ext4 max file 16 TiB · XFS ⚠️ cannot shrink · inode exhaustion is separate
TIME         ⚠️ Always UTC on servers. `timedatectl set-timezone UTC`
```

---

## §17. Lifecycle Dates — verified August 2026

**⚠️ Lifecycle dates are the one genuinely perishable thing in this document. Verify
against the vendor before planning a migration.**

| Distribution | Status as of August 2026 |
|---|---|
| **RHEL 10** | Released **20 May 2025**. Full support to ~**May 2030**, maintenance to ~**May 2035**. Latest minor **10.2** (May 2026) |
| **RHEL 9** | Full support to **31 May 2027**, maintenance to **31 May 2032** |
| **RHEL 8** | ⚠️ **Full support ended 31 May 2024**; 8.10 is the final minor, maintenance to **31 May 2029** |
| **RHEL 7** | ⚠️ **Maintenance ended 30 June 2024**; ELS extended to **31 May 2029** |
| **Ubuntu 26.04 LTS** | Current LTS, released **April 2026**, standard support to **30 April 2031** |
| **Ubuntu 24.04 LTS** | Supported to **31 May 2029** |
| **Ubuntu 25.10** | ⚠️ **EOL 1 July 2026** — interim releases get 9 months |

**⚠️ RHEL's lifecycle is unusually complex** — overlapping **Full Support → Maintenance
Support → Extended Life → ELS** phases, each meaning something different about which
patches you actually receive. **"Is it EOL?" is the wrong question; "which phase, and does
that phase still ship security errata?" is the right one.** **Ubuntu LTS is 5 years
standard, extendable via Pro/ESM.**

**⚠️ Kernel LTS windows have been volatile**: historically six years, **cut to a 2-year
default in 2023** as maintainers cited burnout, then **partially extended again in early
2026 after industry pushback.** ⚠️ **But upstream kernel.org lifecycle usually isn't what
governs you — your distribution's backporting is.** **A RHEL 9 kernel gets security fixes
long after the upstream branch is dead.**

⚠️ **One claim I encountered and am flagging rather than repeating as fact**: a source
asserts a **Linux 7.0** release in 2026 following the 6.x series. **I could not corroborate
this against kernel.org and have not built anything in this document on it.** Version
numbering in Linux is arbitrary by policy, so it's plausible — **verify before quoting.**

**eBPF tooling** (§10.4 → `sysadmin-observability-troubleshooting-and-operations`) is mature and stable in interface: **BCC** ships **80+ ready-made
tools**, **bpftrace** is the one-liner language, and **libbpf + CO-RE** is the production
path for custom programs. ⚠️ **This is now baseline knowledge rather than specialist
tooling.**

---

## §18. Books

| Author | Work | Why |
|---|---|---|
| **Nemeth et al.** | ***UNIX and Linux System Administration Handbook*** | ⚠️ **The one book. Comprehensive, opinionated, current** |
| **Gregg** | ***Systems Performance*** | ⚠️ **§10 → `sysadmin-observability-troubleshooting-and-operations`'s method. The definitive performance text** |
| **Gregg** | ***BPF Performance Tools*** | §10.4 → `sysadmin-observability-troubleshooting-and-operations`, from the person who built most of them |
| **Love** | *Linux System Programming* | What syscalls actually do |
| **Bovet & Cesati** | *Understanding the Linux Kernel* | Deeper, older, still clarifying |
| **Kerrisk** | ***The Linux Programming Interface*** | ⚠️ **The syscall reference. Enormous and authoritative** |
| **Beyer et al.** | ***Site Reliability Engineering*** | ⚠️ **Free online. The operational philosophy** |
| **Limoncelli et al.** | *The Practice of System and Network Administration* | The process side |
| **Barrett et al.** | *SSH: The Definitive Guide* | §9.4 → `sysadmin-packages-boot-and-hardening` in depth |
| **Ward** | *How Linux Works* | ⚠️ **The best entry point if the model isn't solid yet** |

**Primary and practical**: **`man` pages** (⚠️ **`man 7 capabilities`, `man 5 systemd.exec`
and `man 7 signal` in particular — better than most blog posts**), **`systemd.io`**,
**Arch Wiki** (⚠️ **the best Linux documentation on the internet regardless of your
distro**), **Red Hat and Ubuntu documentation**, **`brendangregg.com`**, **`ebpf.io`**,
**`endoflife.date`** for §17.

---

## §19. Command Reference

### 19.1 The fifteen that carry most of the load
```
systemctl status|list-units --failed|cat|edit      service truth
journalctl -u X -f | -p err -b | -b -1             log truth
ss -tulpn                                          what's listening
ip -br a · ip r get IP                             network truth
lsblk -f · df -h · df -i                           storage truth
du -xh --max-depth=1 /                             where did the space go
lsof +L1                                           ⚠️ deleted-but-open files
free -m                                            ⚠️ read "available"
vmstat 1 · iostat -xz 1 · mpstat -P ALL 1          saturation
dmesg -T | tail -50                                ⚠️ OOM, hardware, resets
ps auxf · pstree -p                                process tree
strace -f -p PID  /  execsnoop, opensnoop          ⚠️ what is it actually doing
ausearch -m avc -ts recent                         SELinux denials
nft list ruleset                                   firewall truth
find /etc -name '*.rpmnew' -o -name '*.dpkg-dist'  ⚠️ config drift after updates
```

### 19.2 First five minutes on an unfamiliar sick box
```
uptime; w                          load, who's on, how long up
systemctl list-units --failed      ⚠️ start here
journalctl -p err -b --no-pager | tail -50
dmesg -T | tail -50                ⚠️ OOM? disk errors? link flaps?
df -h; df -i                       ⚠️ both
free -m                            available, and swap activity
ss -tulpn                          expected listeners present?
vmstat 1 5; iostat -xz 1 5         where's the saturation
ip -br a; ip r                     network sane?
timedatectl                        ⚠️ clock right? NTP synced?
last -n 20; journalctl -u sshd | tail   who's been on
```

### 19.3 Pre-change checklist
- [ ] Do I know what this currently does, and have I captured it? (`systemctl cat`, backup the file)
- [ ] Is there a rollback, and can I execute it without network access? (§6.3 → `sysadmin-systemd-storage-and-networking`)
- [ ] Second SSH session open before touching sshd or the firewall? (§9.4 → `sysadmin-packages-boot-and-hardening`)
- [ ] `sshd -t` / `nft -c` / `visudo` / `mount -a` — syntax validated? (§5.3 → `sysadmin-systemd-storage-and-networking`, §9.4 → `sysadmin-packages-boot-and-hardening`)
- [ ] `daemon-reload` after unit changes? (§4.1 → `sysadmin-systemd-storage-and-networking`)
- [ ] Will config management revert this? (§11.2 → `sysadmin-observability-troubleshooting-and-operations`)
- [ ] Is this change in source control? (§13 → `sysadmin-observability-troubleshooting-and-operations`)
- [ ] Do I know how to tell whether it worked, and whether anything else broke?

---

## §20. Method

**§1–§16 → `sysadmin-filesystem-permissions-and-processes`, `sysadmin-systemd-storage-and-networking`, `sysadmin-packages-boot-and-hardening`, `sysadmin-observability-troubleshooting-and-operations` and §19 rest on stable material** — POSIX file semantics, kernel subsystems,
systemd, TCP/IP, and standard tooling — plus the reference works in §18, chiefly
**Nemeth**, **Gregg's *Systems Performance*** for the observability method, and
**Kerrisk** for syscall behaviour. ⚠️ **None of that needed web verification; the man
pages and those books are the authority and they change slowly.**

**Two searches were run in August 2026**, confined to what genuinely perishes:
**distribution lifecycle dates** and the **eBPF tooling landscape**.

**Confidence.** **High** in §1–§16 → `sysadmin-filesystem-permissions-and-processes`, `sysadmin-systemd-storage-and-networking`, `sysadmin-packages-boot-and-hardening`, `sysadmin-observability-troubleshooting-and-operations` and §19 — these are mechanisms and commands I've stated
with their failure modes, and the failure modes are the valuable part. **High** in §10.4 → `sysadmin-observability-troubleshooting-and-operations`'s
eBPF characterization, which is consistent across sources and matches the primary tooling
documentation.

⚠️ **Lower confidence on §17's dates specifically, and I want to be direct about why.**
**Most sources returned for lifecycle questions are EOL-tracking aggregator sites**, several
of which are commercial services with an interest in urgency, and they occasionally
disagree at the margins. **The RHEL dates are consistent across several of them and align
with Red Hat's published phase structure; the Ubuntu dates follow the documented
5-year LTS policy.** **But before you plan a migration on these, check Red Hat's own
lifecycle page or Canonical's release-cycle page** — ⚠️ **vendors extend ELS windows, and
RHEL 7's ELS extension to 2029 is exactly that kind of change.**

⚠️ **And I have explicitly declined to assert one claim**: a source stated Linux 7.0
shipped in 2026. **I could not corroborate it and nothing here depends on it.** Version
numbers in Linux are chosen arbitrarily rather than by semantic rule, so it is plausible —
but **an uncorroborated version claim is not something to put in a reference document
unflagged.**

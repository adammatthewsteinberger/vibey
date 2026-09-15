---
name: sysadmin-systemd-storage-and-networking
description: "Use when configuring the core services of a machine: the systemd unit model, the dependency-versus-ordering distinction people get wrong, the hardening and resource directives, journald and timers over cron; the storage stack including LVM, filesystem choice and I/O tuning; and networking with the modern commands, a diagnosis order that works, firewalling and the tuning that actually matters."
---

# Linux Server Administration: systemd, Storage, and Networking

> **Part 2 of 5** of the *Linux Server Administration* reference (plugin `linux-server-admin`), covering §4–§6. Sibling skills: `sysadmin-filesystem-permissions-and-processes` (§0–§3), `sysadmin-packages-boot-and-hardening` (§7–§9), `sysadmin-observability-troubleshooting-and-operations` (§10–§14), `sysadmin-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §4. systemd

### 4.1 The model
**Units**: `.service`, `.socket`, `.timer`, `.mount`, `.target`, `.path`, `.slice`,
`.device`. **Targets replace runlevels.**
```
systemctl status|start|stop|restart|reload|enable|disable|mask NAME
systemctl daemon-reload            ⚠️ ALWAYS after editing a unit file
systemctl list-units --failed      ⚠️ the first thing to run on a sick box
systemctl cat NAME                 effective unit, including drop-ins
systemctl show NAME                every resolved property
systemctl edit NAME                ⚠️ creates a drop-in — the RIGHT way to override
systemd-analyze blame              boot time by unit
systemd-analyze critical-chain     ⚠️ the actual boot critical path
```
> **⚠️ GOTCHA — never edit vendor unit files in `/usr/lib/systemd/system/`.**
> A package update overwrites them. **Use `systemctl edit NAME` (drop-in in
> `/etc/systemd/system/NAME.d/`) or copy the whole unit to `/etc/systemd/system/`.**
> `/etc` beats `/usr`. **`systemctl cat` shows you what's actually in effect.**

### 4.2 Dependency and ordering — the distinction people get wrong
**⚠️ `Wants=`/`Requires=` express *dependency*. `After=`/`Before=` express *ordering*.
They are independent.** `Requires=foo.service` without `After=foo.service` starts both in
parallel and your service probably fails.
- **`Requires=`** — if the dep fails, this unit fails. **`Wants=`** — weaker; proceed
  regardless. **`BindsTo=`** — stronger; stop if the dep stops.
- ⚠️ **`Requires=` + `After=` is the combination you almost always want.**

### 4.3 The hardening and resource directives
**⚠️ This is systemd's best feature and it's underused.** Per-service sandboxing:
```
[Service]
User=svc                       Group=svc
NoNewPrivileges=true           ⚠️ blocks setuid escalation
ProtectSystem=strict           /usr, /boot, /etc read-only
ProtectHome=true               /home, /root, /run/user inaccessible
PrivateTmp=true                ⚠️ private /tmp — kills a whole class of symlink attacks
PrivateDevices=true            minimal /dev
ProtectKernelTunables=true     ProtectKernelModules=true
ProtectControlGroups=true      RestrictSUIDSGID=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
SystemCallFilter=@system-service
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
ReadWritePaths=/var/lib/svc
MemoryMax=2G                   CPUQuota=50%     TasksMax=512
LimitNOFILE=65535              ⚠️ limits.conf does NOT apply here
Restart=on-failure             RestartSec=5s
```
**⚠️ `systemd-analyze security NAME` scores a unit's exposure** and tells you what's
missing. Run it on everything you write.

**⚠️ `Type=` matters**: `simple` (default, ⚠️ **considered started immediately — no
readiness signal**), `exec`, `forking` (⚠️ **needs `PIDFile=`**), `oneshot`
(+ `RemainAfterExit=`), **`notify`** (⚠️ **the process signals readiness via sd_notify —
the correct choice if the software supports it**).

### 4.4 journald
```
journalctl -u NAME -f                  follow one unit
journalctl -u NAME --since "1 hour ago" --until "10 min ago"
journalctl -p err -b                   ⚠️ errors this boot
journalctl -b -1                       previous boot ⚠️ (crash forensics)
journalctl -k                          kernel messages
journalctl -o json-pretty              structured fields
journalctl --disk-usage · --vacuum-time=30d · --vacuum-size=1G
journalctl -f _SYSTEMD_UNIT=x.service _PID=1234    field matching
```
**⚠️ By default the journal may be volatile** (`/run/log/journal`) and lost on reboot.
**For persistence: `Storage=persistent` in `journald.conf` and `mkdir -p
/var/log/journal`.** ⚠️ **A surprising number of "we have no logs from the crash"
incidents are this.**

### 4.5 Timers over cron
```
[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true          ⚠️ run on boot if the last run was missed
RandomizedDelaySec=300   ⚠️ avoid thundering herd across a fleet
```
**⚠️ Timers beat cron because**: you get journald logging, dependency ordering, resource
limits, and `systemctl list-timers`. **`systemd-analyze calendar "EXPR"` validates the
schedule before you deploy it.**

---

## §5. Storage

### 5.1 The stack
```
Physical device → partition → [LUKS] → [LVM PV → VG → LV] → [RAID] → filesystem → mount
```
```
lsblk -f                     ⚠️ the best single overview: tree + FS + UUID + mountpoint
blkid                        UUIDs and types
df -h · df -i                ⚠️ run BOTH — inodes exhaust independently
du -xh --max-depth=1 /path   ⚠️ -x stops it crossing filesystems
ncdu -x /                    interactive
```

### 5.2 LVM
```
pvcreate /dev/sdb1 · vgcreate vg0 /dev/sdb1 · lvcreate -L 50G -n data vg0
lvextend -L +20G -r /dev/vg0/data      ⚠️ -r resizes the filesystem too
vgs · lvs · pvs                        status
lvcreate -s -L 5G -n snap /dev/vg0/data   snapshot
```
**⚠️ LVM snapshots are copy-on-write and will fill up and break** if the origin churns
past the snapshot size. **They are a backup *staging* mechanism, not a backup.**

### 5.3 Filesystems
| FS | Use | ⚠️ Notes |
|---|---|---|
| **ext4** | Default, boring, reliable | ⚠️ **Cannot shrink while mounted** |
| **XFS** | RHEL default, large files, parallel I/O | ⚠️ **CANNOT SHRINK AT ALL. Ever.** |
| **btrfs** | Snapshots, checksums, subvolumes | ⚠️ **Avoid RAID5/6 — long-standing write hole** |
| **ZFS** | Checksums, snapshots, send/recv, ARC | ⚠️ **Out-of-tree licensing; wants RAM and ECC** |

**⚠️ `/etc/fstab` mistakes strand a box at boot.** Use **UUID= or LABEL=**, never
`/dev/sdX` (⚠️ **device names are not stable across reboots**). **Add `nofail` to
non-critical mounts.** ⚠️ **Always `mount -a` after editing fstab and before rebooting —
this one habit prevents a genuine class of console-access-required incidents.**

**Useful mount options**: `noatime` (⚠️ **reduces write amplification; `relatime` is the
modern default and usually fine**), `nodev,nosuid,noexec` on data mounts, `discard` vs
periodic `fstrim.timer` (⚠️ **prefer the timer; inline discard can hurt latency**).

### 5.4 I/O
`iostat -xz 1` — ⚠️ **`%util` near 100% means the device is busy, but for SSDs and arrays
that does NOT mean saturated** (they handle parallel requests). **Look at `await`,
`aqu-sz` and throughput instead.** `iotop`, `biolatency`/`biosnoop` (§10.4 → `sysadmin-observability-troubleshooting-and-operations`).
**Schedulers**: `cat /sys/block/sda/queue/scheduler` — ⚠️ **`none`/`mq-deadline` for NVMe,
`bfq` for desktop-ish latency, `mq-deadline` for spinning rust.**

---

## §6. Networking

### 6.1 The modern commands
**⚠️ `ifconfig`, `netstat`, `route` and `arp` are deprecated. Learn `ip` and `ss`.**
```
ip a · ip -br a                  ⚠️ -br is the readable one
ip r · ip r get 8.8.8.8          ⚠️ shows which route/interface a dest actually uses
ip -s link                       per-interface error/drop counters
ip neigh                         ARP/NDP table
ss -tulpn                        ⚠️ listening TCP/UDP with process — replaces netstat
ss -s                            socket summary
ss -tan state time-wait | wc -l  TIME_WAIT count
```

### 6.2 Diagnosis, in order
```
ip a                    do I have an address?
ip r                    do I have a route?
ping -c3 <gateway>      is L2/L3 up locally?
ping -c3 1.1.1.1        is routing working? (⚠️ ICMP may be filtered — not proof of down)
dig @1.1.1.1 example.com   is DNS working, bypassing local resolver?
dig example.com         does the SYSTEM resolver work?  ⚠️ compare with the above
curl -v https://host/   does the application layer work?
mtr -rwc100 host        ⚠️ where is loss/latency introduced, per hop
ss -tulpn               am I actually listening, and on which address?
tcpdump -ni any port 443 -c 50   what's on the wire
```
**⚠️ The single most common network "outage" is DNS**, and the second most common is a
service listening on `127.0.0.1` instead of `0.0.0.0`. **`ss -tulpn` distinguishes them
instantly.**

**⚠️ Resolution on modern systems**: `/etc/resolv.conf` may be a symlink managed by
`systemd-resolved` — **use `resolvectl status` and `resolvectl query name`**, because
editing `/etc/resolv.conf` directly gets silently overwritten.

### 6.3 Firewalling
**⚠️ `nftables` is the modern backend; `iptables` commands are usually a shim onto it.**
```
nft list ruleset                        ⚠️ the source of truth
firewall-cmd --list-all                 (RHEL family)
firewall-cmd --permanent --add-service=https && firewall-cmd --reload
ufw status verbose · ufw allow 443/tcp  (Debian/Ubuntu)
```
**⚠️ Two rules that prevent lockouts**: **allow SSH before enabling any firewall**, and
**when changing rules remotely, schedule a rollback first** —
`echo "nft flush ruleset" | at now + 5 minutes` or a `systemd-run --on-active=5m` revert.
Cancel it once you've confirmed you're still connected.

### 6.4 Tuning that actually matters
```
net.core.somaxconn = 4096              ⚠️ listen backlog cap — raise for busy servers
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 10240 65535    ⚠️ ephemeral port exhaustion
net.ipv4.tcp_tw_reuse = 1              ⚠️ safe; tcp_tw_recycle was REMOVED — never use it
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr   ⚠️ notably better on lossy/long-fat links
fs.file-max / nofile limits            for high connection counts
```
**⚠️ Apply via `/etc/sysctl.d/*.conf` and `sysctl --system`**, not by editing
`/etc/sysctl.conf` — packaging and ordering are cleaner.

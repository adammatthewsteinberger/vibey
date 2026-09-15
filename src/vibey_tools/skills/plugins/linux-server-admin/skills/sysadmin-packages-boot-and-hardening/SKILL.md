---
name: sysadmin-packages-boot-and-hardening
description: "Use when provisioning or hardening a server: package managers and the distribution landscape and their support models, the boot path from firmware through bootloader to initramfs and unit activation, and security hardening in the order that actually reduces risk — SELinux and AppArmor, audit and detection, and the SSH configuration that matters."
---

# Linux Server Administration: Packages and Distributions, Boot, and Security Hardening

> **Part 3 of 5** of the *Linux Server Administration* reference (plugin `linux-server-admin`), covering §7–§9. Sibling skills: `sysadmin-filesystem-permissions-and-processes` (§0–§3), `sysadmin-systemd-storage-and-networking` (§4–§6), `sysadmin-observability-troubleshooting-and-operations` (§10–§14), `sysadmin-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §7. Packages and Distributions

| Family | Tools |
|---|---|
| **Debian/Ubuntu** | `apt`, `dpkg`, `apt-mark hold`, `/etc/apt/sources.list.d/`, `unattended-upgrades` |
| **RHEL family** | `dnf`, `rpm`, `dnf versionlock`, `dnf history undo N` ⚠️ **(genuinely useful)**, `dnf needs-restarting -r` |
| **SUSE** | `zypper` |
| **Arch** | `pacman` |
| **Universal** | `snap`, `flatpak`, `nix` |

```
dnf history · dnf history undo 42       ⚠️ transactional rollback of a package op
apt list --upgradable · apt-mark hold pkg
rpm -qf /path/to/file · dpkg -S /path   ⚠️ which package owns this file?
rpm -V pkg · debsums -c                 ⚠️ verify installed files against the package
needrestart / dnf needs-restarting -r   ⚠️ what needs restarting after an update
```
**⚠️ The `.rpmnew` / `.dpkg-dist` trap**: when you've modified a config that a package
update also changed, the package manager writes the new version alongside and **your
edited file stays**. **You get the old behaviour plus a file you never look at.** Search
for them after every batch of updates:
`find /etc -name '*.rpmnew' -o -name '*.rpmsave' -o -name '*.dpkg-*'`.

**⚠️ Distribution choice is mostly a lifecycle and ecosystem decision, not a technical
one.** RHEL family for long support and vendor certification; Debian for stability without
a subscription; Ubuntu LTS for a middle path with commercial options. **§17 → `sysadmin-reference` for dates.**

---

## §8. Boot

```
Firmware (UEFI/BIOS) → bootloader (GRUB2 / systemd-boot) → kernel + initramfs
  → initramfs mounts real root, pivots → systemd PID 1 → default.target
```
**⚠️ Where boot actually breaks, in order of frequency:**
1. **fstab entry for a missing device** → emergency shell. ⚠️ **`nofail` prevents this.**
2. **initramfs missing a driver** after a kernel or storage change →
   `dracut -f` (RHEL) / `update-initramfs -u` (Debian).
3. **GRUB config not regenerated** → `grub2-mkconfig -o /boot/grub2/grub.cfg` or
   `update-grub`.
4. **Full `/boot`** — ⚠️ **old kernels accumulate; the update fails partway.**

**Recovery**: append `systemd.unit=rescue.target` or `emergency.target` or `init=/bin/bash`
to the kernel line in GRUB. **From a live/rescue image: mount, `chroot`, fix.**
⚠️ **For chroot you need `/proc`, `/sys`, `/dev` bind-mounted or nothing works.**

---

## §9. Security Hardening

### 9.1 The order that actually reduces risk
1. **⚠️ Patch.** Unpatched known CVEs beat every exotic control. Automate it.
2. **Minimize attack surface** — ⚠️ **`ss -tulpn` and turn off what's listening that
   shouldn't be.**
3. **SSH hardening** (§9.4).
4. **Least privilege** — service accounts, capabilities (§2.2 → `sysadmin-filesystem-permissions-and-processes`), systemd sandboxing (§4.3 → `sysadmin-systemd-storage-and-networking`).
5. **Firewall** default-deny inbound (§6.3 → `sysadmin-systemd-storage-and-networking`).
6. **MAC** — SELinux or AppArmor (§9.2).
7. **Audit and monitor** (§9.3).
8. **Backups you have actually restored from** (§14 → `sysadmin-observability-troubleshooting-and-operations`).

### 9.2 SELinux and AppArmor
**⚠️ Do not disable SELinux. Fix the label.** It is the single most-disabled security
control and the fix is usually two commands.
```
getenforce · setenforce 0|1        ⚠️ 0 = permissive, TEMPORARY diagnosis only
ausearch -m avc -ts recent         what was denied
sealert -a /var/log/audit/audit.log   human-readable explanation + suggested fix
semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"
restorecon -Rv /srv/web            ⚠️ apply the labels
semanage port -a -t http_port_t -p tcp 8080   ⚠️ non-standard port needs this
getsebool -a · setsebool -P httpd_can_network_connect on
```
**⚠️ The diagnostic pattern**: set permissive, reproduce, read the AVC denials, fix labels
or booleans, set enforcing, verify. **Permissive still logs — that's the point.**

**AppArmor** (Debian/Ubuntu, path-based): `aa-status`, `aa-complain`, `aa-enforce`,
profiles in `/etc/apparmor.d/`.

### 9.3 Audit and detection
`auditd` with rules in `/etc/audit/rules.d/`; `aureport`, `ausearch`.
**File integrity**: AIDE, Tripwire. **Rootkit checks**: rkhunter, chkrootkit.
**Runtime**: **Falco** (eBPF-based, §10.4 → `sysadmin-observability-troubleshooting-and-operations`). **`fail2ban`** for brute-force.
**⚠️ Detection you never look at is theatre.** Ship to a central place, alert on
something, and test that the alert fires.

### 9.4 SSH — the config that matters
```
PermitRootLogin no                    ⚠️ or prohibit-password at minimum
PasswordAuthentication no             ⚠️ keys only — this is the single biggest win
KbdInteractiveAuthentication no        (⚠️ or password auth sneaks back in via PAM)
PubkeyAuthentication yes
AllowUsers alice bob   /  AllowGroups ssh-users
MaxAuthTries 3 · LoginGraceTime 30 · MaxSessions 10
ClientAliveInterval 300 · ClientAliveCountMax 2
X11Forwarding no · AllowAgentForwarding no · PermitTunnel no
```
**⚠️ Always `sshd -t` before reloading, and keep your existing session open while you test
a new one from another terminal.** A bad sshd config plus a closed session equals a
console trip.

**Keys**: `ed25519` (⚠️ **the default choice — small, fast, no parameter footguns**) or
RSA ≥3072. **`ssh-keygen -t ed25519 -C "comment"`.** ⚠️ **Use an agent and
`AddKeysToAgent`; consider certificates (`ssh-keygen -s`) over `authorized_keys` sprawl at
fleet scale — a CA with short-lived certs removes the key-revocation problem entirely.**

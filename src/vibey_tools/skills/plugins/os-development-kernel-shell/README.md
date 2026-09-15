# OS Development — Linux Kernel and Shell Plugin

A deep technical reference for operating system development on Linux: kernel architecture (processes, scheduling, memory, VFS, block, networking, interrupts, locking), writing kernel code in C and Rust, module and driver development, eBPF and sched_ext, syscalls and the userspace ABI, boot and init, containers and cgroups, the kernel development process, debugging and tracing, security and hardening — plus the shell layer, from POSIX sh through bash, zsh, fish, and nushell, with the semantics, traps, and defensive-scripting patterns that keep a script from destroying someone's data.

One reference, split into 5 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (verified August 2026) flags what goes stale first.

## Skills

- **linux-kernel-architecture-and-code** — Kernel Architecture, Writing Kernel Code, and Kernel Concurrency (§0–§3): Routing; Kernel Architecture; Writing Kernel Code; Concurrency in the Kernel.
- **linux-syscalls-ebpf-boot-and-init** — Syscalls and the ABI, eBPF and sched_ext, Boot, Init, cgroups, and Containers (§4–§7): Syscalls and the Userspace ABI; eBPF and sched_ext; Boot; Init, cgroups, and Containers.
- **linux-shell-scripting-and-userland** — Shell Semantics, Choosing a Shell, Defensive Scripting, and the Userland (§8–§11): Shell Semantics — the part that causes the bugs; Choosing a Shell; Defensive Shell Scripting; The Userland.
- **linux-kernel-debugging-process-and-hardening** — Debugging and Observability, the Kernel Development Process, and Hardening (§12–§14): Debugging and Observability; The Kernel Development Process; Security and Hardening.
- **linux-kernel-shell-reference** — Anti-Patterns, Contested Questions, Currency, and Canon (§15–§20): Anti-Patterns; Contested Questions; Currency Snapshot; The Canon; Quick Reference; Sources and Method.

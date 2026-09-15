---
name: linux-kernel-architecture-and-code
description: "Use when reading or writing Linux kernel code. Covers the shape of the kernel, processes and threads, scheduling (EEVDF, RT, deadline), memory (virtual memory, the page cache, allocators), VFS and the block layer, interrupts and deferred work; kernel C vs the C you know, the rules that get patches rejected, a minimal module line by line, the driver model and devicetree, userspace-facing interfaces (sysfs, ioctl, netlink), Rust in the kernel; and kernel concurrency — the locking primitives, RCU, memory barriers, and the deadlock rules. Includes the router for the whole os-development-kernel-shell reference."
---

# Linux Kernel & Shell: Kernel Architecture, Writing Kernel Code, and Kernel Concurrency

> **Part 1 of 5** of the *OS Development — Linux Kernel and Shell* reference (plugin `os-development-kernel-shell`), covering §0–§3. Sibling skills: `linux-syscalls-ebpf-boot-and-init` (§4–§7), `linux-shell-scripting-and-userland` (§8–§11), `linux-kernel-debugging-process-and-hardening` (§12–§14), `linux-kernel-shell-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

### 0.1 What kind of OS work is this?

| Task | Where it lives | Language | Risk if wrong |
|---|---|---|---|
| Observe the system | eBPF, ftrace, perf | BPF C / bpftrace | Low — verifier catches most of it |
| Change scheduling policy | **sched_ext** BPF scheduler | BPF C / Rust | Low — kernel reverts to fair class on error |
| Drive new hardware | Kernel module / driver | C or **Rust** | High — oops, corruption |
| Add a syscall or change ABI | Core kernel | C | **Permanent.** You can never take it back |
| New filesystem | fs/ | C | Data loss |
| Userspace init/service | systemd unit, D-Bus | Config / any | Medium |
| Automate a system task | Shell / Python | bash, POSIX sh | **Very high** — `rm -rf "$UNSET/"` |
| Build a distro / image | Yocto, Buildroot, mkosi | Recipes | Medium |
| Harden a system | sysctl, LSM, seccomp, lockdown | Config | Medium |

**[DURABLE] Before writing kernel code, ask whether you can do it in userspace or in
BPF instead.** The kernel community asks this first and so should you. A driver that
could be a `uio`/`vfio` userspace driver, a filesystem that could be FUSE, a monitor that
could be eBPF — all are better engineering *and* faster to ship, because they don't
require review by a maintainer who has been burned a thousand times.

### 0.2 The question router

| Asked about... | Go to |
|---|---|
| What is the kernel actually doing? Processes, scheduling, memory, VFS | §1 |
| Writing kernel code — modules, drivers, C idioms, Rust | §2 |
| Locking, RCU, memory barriers, per-CPU, preemption | §3 |
| Syscalls, the ABI, "don't break userspace", vDSO | §4 → `linux-syscalls-ebpf-boot-and-init` |
| eBPF, sched_ext, tracing programs | §5 → `linux-syscalls-ebpf-boot-and-init` |
| Boot: firmware → bootloader → initramfs → init | §6 → `linux-syscalls-ebpf-boot-and-init` |
| systemd, units, cgroups, namespaces, containers | §7 → `linux-syscalls-ebpf-boot-and-init` |
| Shell semantics — word splitting, quoting, expansion | §8 → `linux-shell-scripting-and-userland` |
| Bash vs zsh vs fish vs nushell; which to use | §9 → `linux-shell-scripting-and-userland` |
| Writing shell that doesn't destroy things | §10 → `linux-shell-scripting-and-userland` |
| The userland: coreutils, text processing, process tools | §11 → `linux-shell-scripting-and-userland` |
| Debugging: ftrace, perf, KASAN, crash, printk | §12 → `linux-kernel-debugging-process-and-hardening` |
| Kernel dev process: patches, maintainers, stable, CVEs | §13 → `linux-kernel-debugging-process-and-hardening` |
| Security: LSM, seccomp, lockdown, hardening, attack surface | §14 → `linux-kernel-debugging-process-and-hardening` |
| "Don't do this" | §15 → `linux-kernel-shell-reference` |
| "Which is better, X or Y?" | §16 → `linux-kernel-shell-reference` (contested) |
| "Is this still current?" | §17 → `linux-kernel-shell-reference` |
| Books, docs, people | §18 → `linux-kernel-shell-reference` |

---

## §1. Kernel Architecture

### 1.1 The shape of it

```
┌───────────────────────────────────────────────────────────────┐
│ USERSPACE   applications · libc (glibc/musl) · systemd         │
└────────────────────────────┬──────────────────────────────────┘
                    syscalls │ vDSO │ /proc /sys /dev │ netlink │ BPF
┌────────────────────────────┴──────────────────────────────────┐
│ SYSTEM CALL INTERFACE                                          │
├──────────┬──────────┬──────────┬──────────┬───────────────────┤
│ Process  │ Memory   │ VFS      │ Network  │ Device drivers    │
│ sched,   │ mm, page │ fs, page │ netdev,  │ (60%+ of the      │
│ signals, │ alloc,   │ cache,   │ TCP/IP,  │  source tree)     │
│ futex,   │ slab,    │ block    │ netfilter│                   │
│ cgroups  │ swap     │ layer    │ XDP      │                   │
├──────────┴──────────┴──────────┴──────────┴───────────────────┤
│ CORE: locking · RCU · workqueues · timers · IRQ · DMA · BPF    │
├───────────────────────────────────────────────────────────────┤
│ ARCH: x86 / arm64 / riscv / loongarch / s390 / powerpc         │
└───────────────────────────────────────────────────────────────┘
```

**[DURABLE] Linux is a monolithic kernel with loadable modules.** Everything runs in one
address space at ring 0. There is no IPC boundary between the scheduler and your driver.
That is the source of both its performance and its blast radius: a NULL dereference in a
USB driver takes down the machine.

**The source tree, by orientation:**
| Directory | Contents |
|---|---|
| `kernel/` | Core: scheduler (`kernel/sched/`), signals, time, futex, cgroups, BPF (`kernel/bpf/`) |
| `mm/` | Memory management: page allocator, slab, VMA, page cache, swap, OOM |
| `fs/` | VFS + every filesystem (`ext4/`, `xfs/`, `btrfs/`, `overlayfs/`, `proc/`) |
| `drivers/` | **The majority of the tree.** By subsystem |
| `net/` | Protocol stacks, netfilter, sockets, XDP |
| `arch/` | Per-architecture: entry code, page tables, atomics, boot |
| `include/linux/` | Internal headers — the kernel's real API surface |
| `include/uapi/` | **The userspace ABI.** Change with extreme care (§4 → `linux-syscalls-ebpf-boot-and-init`) |
| `lib/`, `crypto/`, `security/`, `block/`, `ipc/`, `init/` | As named |
| `Documentation/` | **Read this.** It is unusually good and constantly out-of-date in exactly the places you'd expect |
| `tools/` | perf, bpftool, selftests, sched_ext examples |
| `rust/` | Rust core abstractions and the `kernel` crate (§2.6) |

### 1.2 Processes and threads

**[DURABLE] Linux has no separate "thread" concept in the kernel.** There is
`struct task_struct`, and threads are tasks that share resources. `clone()` with flags
decides *what* is shared:

| Flag | Shares |
|---|---|
| `CLONE_VM` | Address space → this is what makes it "a thread" |
| `CLONE_FS` | cwd, umask, root |
| `CLONE_FILES` | File descriptor table |
| `CLONE_SIGHAND` | Signal handlers |
| `CLONE_THREAD` | Thread group (same TGID → same "PID" to userspace) |
| `CLONE_NEWNS/NEWPID/NEWNET/…` | **Namespaces** — this is how containers are built (§7.3 → `linux-syscalls-ebpf-boot-and-init`) |

`fork()` = `clone()` with almost nothing shared. `pthread_create()` = `clone()` with
VM|FS|FILES|SIGHAND|THREAD. **Containers are the same primitive with namespace flags.**
There is no "container" object in the kernel — a container is a process with unusual
namespace, cgroup, and LSM settings.

**Process states** (`/proc/PID/stat`): R (running/runnable), S (interruptible sleep),
**D (uninterruptible sleep — waiting on I/O; cannot be killed, and a pile of D-state
processes means storage or a network filesystem is stuck)**, T (stopped), Z (zombie —
exited but not reaped; the parent's fault, not the child's), X (dead).

### 1.3 Scheduling

**Scheduling classes, in priority order** [VERSIONED — this list has grown]:
```
stop_sched_class     — CPU hotplug/migration. Preempts everything.
dl_sched_class       — SCHED_DEADLINE (EDF + constant bandwidth server)
rt_sched_class       — SCHED_FIFO, SCHED_RR (priorities 1–99)
fair_sched_class     — SCHED_NORMAL/BATCH/IDLE. EEVDF since 6.6 (replaced CFS)
ext_sched_class      — SCHED_EXT (sched_ext, BPF schedulers) — since 6.12
idle_sched_class     — the idle task
```

**EEVDF** (Earliest Eligible Virtual Deadline First) replaced CFS as the fair-class
algorithm in 6.6. The key concepts: each task accrues **virtual runtime** scaled by
weight (from `nice`); a task is **eligible** when its `vruntime` is at or behind the
weighted average; among eligible tasks the one with the earliest **virtual deadline**
runs. `sched_latency`-style tuning knobs from CFS largely don't apply; the per-task
`slice` (settable via `sched_setattr`) is the modern lever.

**[DURABLE] Real-time on Linux, precisely:**
- `SCHED_FIFO`/`SCHED_RR` tasks preempt all fair tasks and run until they block or yield.
  A runaway `SCHED_FIFO` task at priority 99 with a busy loop **hangs that CPU**;
  `sched_rt_runtime_us` (default 950000 of 1000000 µs) is the throttle that saves you.
- `SCHED_DEADLINE` takes (runtime, deadline, period) and does admission control — the
  kernel *refuses* to admit a task set it can't schedule. It's the only class with a
  real guarantee.
- **PREEMPT_RT was merged into mainline in Linux 6.12** (Sept 2024) for x86, arm64, and
  RISC-V, ending a ~20-year out-of-tree effort. This makes most spinlocks sleeping
  rt_mutexes and most IRQ handlers threaded. **It does not make Linux hard real-time** —
  it takes worst-case latency from milliseconds to tens of microseconds, which is a
  different claim.
- Achieving that in practice needs the whole stack: `isolcpus`/`nohz_full`/`rcu_nocbs`,
  IRQ affinity moved off isolated cores, `mlockall()`, no page faults in the hot path,
  C-states and frequency scaling pinned, and **`cyclictest` under representative load as
  proof**. A max-latency number without a load description is meaningless.

### 1.4 Memory

**Virtual memory layout** (x86-64, 4-level paging, 48-bit): userspace `0x0000...` up to
128 TiB, a non-canonical hole, then kernel space in the top half — direct map of all
physical memory, vmalloc area, kernel text. Since 5.x there is optional 5-level paging
(57-bit) for very large machines.

**Allocators, and when to use which** [DURABLE]:
| API | Backing | Size | Contiguity | Context |
|---|---|---|---|---|
| `kmalloc(size, gfp)` | slab | ≤ a few MB (order-limited) | **Physically contiguous** | Anywhere (gfp-dependent) |
| `kzalloc` / `kcalloc` | slab | " | " | Zeroed. Prefer these. |
| `vmalloc(size)` | pages + PTEs | large | Virtually only | **Sleeps.** Not for DMA |
| `alloc_pages(gfp, order)` | buddy | 2^order pages | Physically contiguous | Page granularity |
| `kmem_cache_alloc` | dedicated slab cache | fixed | contiguous | Hot objects of one type |
| `dma_alloc_coherent` | DMA API | | DMA-capable | **The only correct way to get DMA memory** |
| `devm_kzalloc` | slab, device-managed | | contiguous | **Auto-freed on driver detach — use it** |

**GFP flags are the most important thing to get right:**
- `GFP_KERNEL` — may sleep. **Cannot be used in atomic context** (interrupt handler,
  spinlock held, RCU read-side critical section).
- `GFP_ATOMIC` — will not sleep, may fail, dips into emergency reserves. Use in
  interrupt context.
- `GFP_NOWAIT` — no sleep, no reserves.
- `GFP_NOIO` / `GFP_NOFS` — may sleep but must not recurse into I/O or the filesystem.
  Required in block/fs writeback paths or you deadlock against yourself.
- `__GFP_ZERO`, `__GFP_NOWARN`, `__GFP_NOFAIL` (almost never justified).

> **⚠️ GOTCHA — sleeping in atomic context.** `might_sleep()` and
> `CONFIG_DEBUG_ATOMIC_SLEEP` exist because this is the single most common kernel bug
> class. `GFP_KERNEL` under a spinlock produces "BUG: sleeping function called from
> invalid context" — *if* you have the debug options on. If you don't, you get a rare,
> load-dependent deadlock in production instead. **Always develop with the debug configs
> enabled (§12.1 → `linux-kernel-debugging-process-and-hardening`).**

**The page cache** unifies file I/O and mmap: `read()` populates it, `mmap()` maps it,
writeback flushes dirty pages per `vm.dirty_ratio`/`dirty_background_ratio`. Understanding
this explains most Linux I/O behaviour, including why `free` "shows no free memory"
(cache is reclaimable and that's the point) and why `fsync()` is the only durability
primitive that means anything.

**The OOM killer** picks by `oom_score` (roughly, memory footprint adjusted by
`oom_score_adj`). Under cgroup v2, memory pressure is contained per-cgroup with
`memory.max` / `memory.high`, and **PSI** (`/proc/pressure/{cpu,memory,io}`) is the
modern signal for "this machine is thrashing" — far better than load average.

### 1.5 VFS and the block layer

```
syscall (read/write/openat)
  → VFS: struct file → struct dentry → struct inode → struct super_block
    → filesystem (ext4, xfs, btrfs, overlayfs, nfs, fuse…)
      → page cache
        → block layer: bio → request queue → I/O scheduler (mq-deadline, bfq, none)
          → blk-mq (multiqueue) → driver (nvme, virtio-blk, scsi)
```

**[DURABLE] The VFS's four objects** — superblock (a mounted fs), inode (a file's
metadata), dentry (a name→inode cache entry; the dcache is why path lookup is fast), and
file (an open file description, with the offset). Understanding that **dentries cache
names and inodes cache files** explains hard links, rename semantics, and why
`/proc/PID/fd` shows what it shows.

**Durability, correctly [DURABLE and constantly gotten wrong]:**
```
write()            → page cache. NOT durable. Survives process crash, not power loss.
fsync(fd)          → file data + metadata for that file to stable storage.
fdatasync(fd)      → data + only metadata needed to read it back. Cheaper.
fsync(dirfd)       → REQUIRED after create/rename/unlink to persist the DIRECTORY ENTRY.
O_SYNC / O_DSYNC   → implicit sync on each write. Slow.
O_DIRECT           → bypass page cache. Alignment requirements. Not a durability guarantee.
```
> **⚠️ GOTCHA — the atomic-rename recipe.** The only portable way to replace a file
> without risking a truncated result across a power loss:
> `open(tmp) → write() → fsync(tmp) → close → rename(tmp, target) → fsync(parent dir)`.
> Skipping the **parent directory fsync** is the step everyone omits, and it means the
> rename may not be durable even though the data is.
> Also: **`fsync()` can fail, and on Linux historically a failed `fsync()` could clear
> the error flag** — the "fsyncgate" problem that changed PostgreSQL's design. On error,
> the correct response is to treat the data as lost, not to retry.

**Filesystem selection** [VERSIONED]: **ext4** (default, boring, extremely well tested),
**XFS** (large files, high parallelism, online repair since ~6.18), **Btrfs** (CoW,
snapshots, checksums, subvolumes; RAID5/6 still not recommended), **ZFS** (out-of-tree,
CDDL/GPL licence incompatibility means it will never merge), **overlayfs** (the container
layering filesystem), **F2FS** (flash), **tmpfs**, **FUSE** (userspace).
**bcachefs** — see §17 → `linux-kernel-shell-reference`; it is no longer in the kernel tree.

### 1.6 Interrupts and deferred work

**[DURABLE] The two-half rule.** Hardware IRQ handlers run with interrupts disabled on
that line, cannot sleep, and must be as short as possible: acknowledge, grab the data,
schedule the rest.

| Mechanism | Context | Can sleep | Use for |
|---|---|---|---|
| Hard IRQ handler | interrupt | **No** | Ack hardware, wake the bottom half |
| **Threaded IRQ** (`request_threaded_irq`) | process | **Yes** | The modern default — the "bottom half" is a kernel thread |
| Softirq | interrupt (deferred) | No | Core subsystems only (net, block, timers). Don't add new ones |
| Tasklet | interrupt (deferred) | No | **Deprecated.** Use threaded IRQ or workqueue |
| **Workqueue** (`queue_work`) | process (kworker) | **Yes** | General deferred work. The right default |
| Kthread | process | Yes | Long-running per-device work |

**[VERSIONED] Write new drivers with `request_threaded_irq()`.** It gives you a sleeping
context for free and behaves correctly under PREEMPT_RT, where softirqs and tasklets have
different semantics.

---

## §2. Writing Kernel Code

### 2.1 The kernel is not C as you know it

**[DURABLE] What you do not have:**
- **No libc.** No `printf`, `malloc`, `strcpy` in the userspace sense. The kernel has its
  own: `printk`/`pr_*`, `kmalloc`, `strscpy`, `kstrtoint`.
- **No floating point** (without `kernel_fpu_begin/end`, and you almost certainly
  shouldn't). The FPU state isn't saved across kernel entry.
- **A tiny, fixed stack** — typically **16 KB** on x86-64 (`THREAD_SIZE`), shared with
  interrupt frames on some configs. **No large stack arrays, no deep recursion, no
  variable-length arrays.** `CONFIG_FRAME_WARN` yells at ~1–2 KB per frame.
- **No exceptions and no unwinding.** Errors are `int` return codes: `0` on success,
  **negative errno** (`-ENOMEM`, `-EINVAL`, `-EIO`) on failure. `ERR_PTR()`/`IS_ERR()`/
  `PTR_ERR()` encode errors in pointer returns.
- **No memory protection.** A bad pointer corrupts unrelated subsystems. The symptom
  appears far from the cause. This is why KASAN exists (§12.3 → `linux-kernel-debugging-process-and-hardening`).
- **Preemption and concurrency everywhere.** Your function can be entered on every CPU
  simultaneously, and preempted mid-way. Assume it.

**Kernel C dialect:** GNU C (not ISO), currently gnu11-ish with strong movement toward
newer standards; `__attribute__`s, statement expressions, `typeof`, and inline asm are
normal. `-fno-strict-aliasing` and `-fno-delete-null-pointer-checks` are on, which is why
some UB that would bite userspace doesn't bite here — do not rely on that.

**The idioms you will read constantly:**
```c
/* Error handling with goto — the canonical single-exit cleanup ladder.
   MISRA-style "no goto" rules do not apply here; this IS the kernel style. */
static int foo_probe(struct platform_device *pdev)
{
        struct foo *f;
        int ret;

        f = devm_kzalloc(&pdev->dev, sizeof(*f), GFP_KERNEL);
        if (!f)
                return -ENOMEM;                    /* devm_ = auto-freed. Prefer it. */

        f->clk = devm_clk_get(&pdev->dev, NULL);
        if (IS_ERR(f->clk))
                return dev_err_probe(&pdev->dev, PTR_ERR(f->clk), "no clock\n");
                /* dev_err_probe handles -EPROBE_DEFER quietly. Use it. */

        ret = clk_prepare_enable(f->clk);
        if (ret)
                return ret;

        ret = foo_hw_init(f);
        if (ret)
                goto err_clk;                      /* unwind in reverse order */

        platform_set_drvdata(pdev, f);
        return 0;

err_clk:
        clk_disable_unprepare(f->clk);
        return ret;
}

/* container_of — how the kernel does "inheritance" without inheritance.
   Given a pointer to an embedded member, recover the enclosing struct. */
struct my_dev { int id; struct device dev; };
static struct my_dev *to_my_dev(struct device *d)
{ return container_of(d, struct my_dev, dev); }

/* Intrusive linked lists — the node lives IN your struct, no allocation. */
struct my_item { struct list_head list; int value; };
LIST_HEAD(items);
list_add_tail(&item->list, &items);
list_for_each_entry(item, &items, list) { ... }
list_for_each_entry_safe(item, tmp, &items, list) { list_del(&item->list); kfree(item); }
```

### 2.2 The rules that get patches rejected

**[DURABLE, and enforced socially as much as technically]:**
1. **Follow `Documentation/process/coding-style.rst`.** Tabs of 8. 80 columns is a
   soft limit (100 tolerated). Braces K&R-ish. `checkpatch.pl --strict` before sending.
2. **One logical change per patch.** A series that mixes a cleanup with a fix will be
   asked to be split.
3. **`Signed-off-by:` is a legal statement** (the Developer Certificate of Origin), not
   a formality.
4. **Never break userspace.** §4 → `linux-syscalls-ebpf-boot-and-init`. This is the one rule Linus enforces personally and
   loudly.
5. **No new `/proc` files** for arbitrary data; use sysfs (one value per file) or debugfs
   (unstable, debug-only) as appropriate. sysfs has an ABI stability expectation.
6. **Document your locking.** A comment saying which lock protects which field is
   expected. `lockdep` (§12.2 → `linux-kernel-debugging-process-and-hardening`) will verify it.
7. **`__user` annotations and `copy_from_user`/`copy_to_user`** for every userspace
   pointer. Sparse (`make C=1`) checks this. Dereferencing a `__user` pointer directly
   is both a bug and a security hole.
8. **Check every return value.** `__must_check` exists.

### 2.3 A minimal module, and why each line is there

```c
// SPDX-License-Identifier: GPL-2.0        /* Required. Machine-checkable. */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

static int __init hello_init(void)         /* __init: freed after boot */
{
        pr_info("hello: loaded\n");        /* pr_* honours the module prefix */
        return 0;                          /* nonzero = module load fails */
}

static void __exit hello_exit(void)        /* __exit: dropped if built-in */
{
        pr_info("hello: unloaded\n");
}

module_init(hello_init);
module_exit(hello_exit);

MODULE_LICENSE("GPL");    /* Non-GPL taints the kernel and loses EXPORT_SYMBOL_GPL */
MODULE_AUTHOR("...");
MODULE_DESCRIPTION("...");
```
Build out-of-tree against the running kernel's headers:
```makefile
obj-m += hello.o
all:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
```

> **⚠️ GOTCHA — there is no stable in-kernel ABI, deliberately.** A module built for
> 6.18.40 will not load on 6.18.41 if the relevant symbols' CRCs changed. This is policy,
> not oversight: the kernel reserves the right to change internal interfaces, and the
> cost of that policy is borne by out-of-tree modules. The consequences: DKMS rebuilds on
> every kernel update, `MODULE_VERSION`/`modversions` mismatches, and the reason vendors
> push hard to get drivers upstream. **Getting your driver merged is the only durable
> maintenance strategy.**

### 2.4 Driver model and devicetree

Modern drivers plug into the **driver model**: a `struct device` bound to a `struct
device_driver` by a **bus** (platform, PCI, USB, I2C, SPI). The bus matches by
compatible string (devicetree), ACPI ID, or vendor/device ID, then calls `probe()`.

```c
static const struct of_device_id foo_of_match[] = {
        { .compatible = "vendor,foo-v2" },
        { }
};
MODULE_DEVICE_TABLE(of, foo_of_match);   /* enables autoloading via modalias */

static struct platform_driver foo_driver = {
        .probe  = foo_probe,
        .remove = foo_remove,
        .driver = {
                .name           = "foo",
                .of_match_table = foo_of_match,
                .pm             = &foo_pm_ops,
        },
};
module_platform_driver(foo_driver);
```
**Devicetree** describes non-discoverable hardware (most ARM/RISC-V embedded); ACPI does
the same job on x86 servers. `-EPROBE_DEFER` is the mechanism for "my dependency isn't
ready yet, retry later" — return it, don't spin.

**Use the `devm_` (device-managed) API for everything you can.** Resources are released
automatically on probe failure and on detach, which eliminates the single largest source
of driver leak bugs.

### 2.5 Userspace-facing interfaces

| Interface | Stability | Use for |
|---|---|---|
| **syscall** | Forever (§4 → `linux-syscalls-ebpf-boot-and-init`) | Fundamental new capability. Very high bar |
| **ioctl** | Per-driver, versioned | Device-specific commands. **Design the struct with padding and a size/version field from day one** |
| **sysfs** (`/sys`) | ABI-stable, documented in `Documentation/ABI/` | One value per file, text |
| **debugfs** (`/sys/kernel/debug`) | **None** | Debugging only. Never rely on it in production tooling |
| **procfs** (`/proc`) | Legacy stable | Process info. Don't add new non-process files |
| **netlink** | Stable | Structured, async, multicast config (networking, but not only) |
| **char device** | Per-driver | Streaming data |
| **BPF** | Stable-ish | Programmable hooks (§5 → `linux-syscalls-ebpf-boot-and-init`) |

### 2.6 Rust in the kernel

**[VERSIONED — this changed materially in 2026.]** Rust support landed experimentally in
6.1; **Linux 7.0 (12 April 2026) removed the experimental designation, making Rust a
first-class kernel language.** The "Rust experiment" was formally concluded at the 2025
Kernel Maintainers Summit in Tokyo with an explicit coexistence policy: **Rust for new
code, C for existing subsystems, no forced migrations.** Kernel builds now require only
stable Rust releases (minimum anchored to the Debian stable toolchain, ~1.93 at the time
of the 7.0 release). Reported at Open Source Summit India in July 2026: some subsystems —
**graphics notably** — intend to accept only Rust for *new* drivers going forward.

**What exists:** the `kernel` crate with abstractions over PCI device enumeration,
interrupt handling, DMA mapping, platform device registration, `dev_printk` on all device
types, and generic I/O back-ends. Real drivers: Android's **ashmem** shipped in Rust on
kernel 6.12 (putting Rust kernel code on hundreds of millions of devices), NVIDIA's
**Nova** DRM driver for Turing-era hardware, Rust NVMe work, and PuzzleFS.

**What's actually hard about it** [the honest list]:
- **No `std`.** You get `core`, `alloc`, and the kernel's own `kernel` crate.
- **Fallible allocation everywhere.** `Box::new` can't panic in the kernel, so you use
  the kernel's fallible variants and handle `-ENOMEM` explicitly.
- **Toolchain management overhead** — a specific minimum Rust version, and some carefully
  used unstable features.
- **Two skill sets.** You need kernel programming *and* Rust; the intersection is small.
- **Documentation lags** the C side substantially.
- Abstractions for a subsystem may simply not exist yet, in which case you write them —
  which is a much bigger job than writing the driver.

**[CONTESTED] Rust in the kernel.** The disagreement is real, public, and has cost
maintainers. *For:* memory-safety bugs are the dominant kernel CVE class and Rust
eliminates them by construction; Google reports zero memory-safety bugs in production
from its Rust Android driver code where equivalent C drivers had CVEs. *Against (the
strongest version):* a second language doubles the maintenance surface for subsystem
maintainers who must now review both; refactoring a C interface now requires fixing Rust
bindings maintained by someone else; and the kernel's rule that C changes shouldn't be
blocked by Rust breakage is easier to state than to live with. One maintainer publicly
resigned over this. **Both the technical case and the social cost are real; the policy
question is settled, the friction is not.**

---

## §3. Concurrency in the Kernel

### 3.1 The primitives

| Primitive | Sleeps | Context | Use for |
|---|---|---|---|
| `spinlock_t` | No (busy-waits) | Any, incl. IRQ | Short critical sections. **Under PREEMPT_RT these become sleeping rt_mutexes** |
| `spin_lock_irqsave/irqrestore` | No | When an IRQ handler takes the same lock | The safe default when in doubt |
| `raw_spinlock_t` | No, ever | Truly atomic paths | Stays a real spinlock even on RT |
| `struct mutex` | **Yes** | Process context only | Longer sections; the default choice |
| `rw_semaphore` | Yes | Process | Many readers, rare writers |
| `seqlock_t` | No | Any | Read-mostly; readers retry, never block writers |
| **RCU** | Readers: no | Any | **Read-mostly data structures. The kernel's signature technique** |
| `atomic_t` / `atomic64_t` | No | Any | Counters, flags |
| `refcount_t` | No | Any | **Reference counts — use this, not atomic_t.** It detects overflow/UAF |
| `completion` | Yes | Process | "Wait until this finishes" |
| `wait_queue_head_t` | Yes | Process | Sleep until a condition |
| `percpu` variables | — | Any | Avoid sharing entirely — the fastest lock is no lock |

### 3.2 RCU — the thing that makes Linux scale

**[DURABLE] Read-Copy-Update:** readers are (almost) free — no locks, no atomics, no
cache-line bouncing. Writers make a *copy*, publish it atomically, and defer freeing the
old version until every pre-existing reader has finished.

```c
/* Reader — cheap. rcu_read_lock() is essentially a preempt-disable. */
rcu_read_lock();
p = rcu_dereference(gp);            /* ensures the load isn't reordered ahead */
if (p) do_something(p->field);      /* p is guaranteed valid until unlock */
rcu_read_unlock();

/* Writer */
new = kmalloc(sizeof(*new), GFP_KERNEL);
*new = *old;
new->field = value;
rcu_assign_pointer(gp, new);        /* publish: barrier + store */
synchronize_rcu();                  /* wait for a GRACE PERIOD (may sleep, may be slow) */
kfree(old);
/* or: call_rcu(&old->rcu, free_cb);  — async, doesn't block the writer */
```
**The grace period** is the whole idea: a period after which every CPU has passed through
a quiescent state, so no reader can still hold the old pointer.

> **⚠️ GOTCHA — RCU read-side is atomic context.** You cannot sleep between
> `rcu_read_lock()` and `rcu_read_unlock()`. No `GFP_KERNEL`, no mutex, no
> `copy_to_user`. (SRCU exists if you need to sleep; it has its own costs.)
> `CONFIG_PROVE_RCU` catches violations.

### 3.3 Memory barriers

**[DURABLE] The compiler and the CPU both reorder memory accesses.** The kernel's model
is documented in `Documentation/memory-barriers.txt` — long, dense, and the definitive
source.

| Barrier | Effect |
|---|---|
| `barrier()` | Compiler only |
| `smp_mb()` | Full barrier (SMP only; compiles away on UP) |
| `smp_rmb()` / `smp_wmb()` | Read / write barrier |
| `smp_store_release()` / `smp_load_acquire()` | **The preferred modern idiom.** Cheaper than full barriers and expresses intent |
| `mb()`, `rmb()`, `wmb()` | Including for MMIO/DMA |
| `READ_ONCE()` / `WRITE_ONCE()` | Prevent the compiler from tearing, fusing, or inventing accesses |

**[DURABLE] `volatile` is nearly always wrong in kernel code.** Use `READ_ONCE`/
`WRITE_ONCE` for single accesses and proper locking or barriers for ordering.
`Documentation/process/volatile-considered-harmful.rst` exists for a reason.

### 3.4 The deadlock rules

1. **Establish a global lock ordering and document it.** Nested locks must always be
   taken in the same order everywhere.
2. **Never sleep holding a spinlock.**
3. **If an IRQ handler takes lock L, every other acquirer of L must disable interrupts**
   (`spin_lock_irqsave`), or you deadlock against yourself.
4. **Prefer one lock over two.** Prefer per-CPU or RCU over one.
5. **Turn on lockdep** (`CONFIG_PROVE_LOCKING`). It builds a lock dependency graph at
   runtime and reports a potential deadlock the first time it sees an inconsistent
   ordering — *even if the deadlock doesn't happen*. It is one of the best debugging
   tools in any system, anywhere.

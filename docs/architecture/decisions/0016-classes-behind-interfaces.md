# 0016 — Code lives in classes, and every class has an interface beside it

**Status:** accepted · **Date:** 2026-09-15

**Canon:** sub-doctrine 9.b — *the declared seam*, filed under doctrine 9 — The vibe (ADR-0020). It is law from the operator's ratifying merge of the change that carries it.

## Context

This codebase already has one interface convention and it only covers one seam.
`application/interfaces/` declares thirteen Protocol modules — the ports the
composition root wires concrete adapters into — and `.importlinter`'s
`interfaces-declare-only` contract keeps them from importing the code that
consumes them. That is the boundary between the application layer and the world.

Everywhere else, substitution is ad hoc. Measured on `a81c825`:

| layer | classes | Protocols | module-level functions |
|---|---|---|---|
| `domain/` | 129 | 0 | 99 |
| `application/` | 83 | 40 | 48 |
| `infrastructure/` | 64 | 2 | 91 |
| `cli/` | 0 | 0 | 37 |
| `tui/` | 8 | 0 | 5 |

Two `interfaces/` directories existed at that commit: `application/interfaces` (13
files, twelve of them declaring the 40 Protocols counted above) and
`infrastructure/interfaces` (1). The "classes" column counts concrete classes, not
Protocols. So roughly three hundred module-level functions and two hundred and
eighty classes had no declared seam at all. A third package, `cli/interfaces`,
arrived with the SIGTERM latch (44c1c21a) and is the first to follow the mirrored
`_interface` naming below; the existing `application/interfaces` modules are grouped
by port family and converge like any other module.

A function with no seam is substituted by patching its import — `monkeypatch.setattr`
against the module that imported it, not the module that defined it. That works,
and it binds every test to the import graph rather than to the contract. Rename a
module, move a call site, and a test that was asserting behaviour starts asserting
nothing while still passing.

## Decision

Two rules, and the second is the reason for the first.

**1. Code lives in class objects.** A module-level function is the method of last
resort, permitted only where a class is genuinely not available — a module's
public `__all__` façade, a `__main__` entry point, a pure helper that a language
or library contract requires to be a bare function. "It is only a few lines" is
not a reason. Where a bare function is used, the reason is written at the
definition, not left to be inferred.

**2. Every class has an interface beside it, in a mirrored `interfaces/`
directory.** For `src/<pkg>/services/github_service.py` there is
`src/<pkg>/services/interfaces/github_service_interface.py`. The mapping is
mechanical: the directory gains an `interfaces/` child, the module gains an
`_interface` suffix, and the interface declares the contract the class
implements.

Interfaces declare; they never consume. `.importlinter` already states that rule
for `application.interfaces` and it extends unchanged to every new `interfaces/`
package: an interface module may import the standard library and other
interfaces, and nothing else from its own tree.

## Rationale

**Testability is the whole argument.** A class behind an interface is
substituted at its seam — the caller takes the interface, the test passes a
double, and nothing is patched. The test then depends on the contract, which is
the thing that is supposed to be stable, instead of on the import graph, which
is not. The 100% branch-coverage floor makes this concrete rather than
aspirational: a branch that can only be reached by patching a module attribute
is a branch whose test will break for reasons unrelated to its subject.

**It makes the seam a reviewable artifact.** An interface file is where a
contract change becomes visible in a diff. A bare function's contract changes
silently, in its signature, among its implementation.

**It generalises the pattern that already works here.** `application/interfaces`
plus a composition root is why the application layer can be tested without a
database, and why `bootstrap.py` is the only module that knows what a
`HandoffStore` really is (a `PostgresHandoffRepository`). The decision is to stop treating that as a special
case for one layer.

## Consequences

**This is the rule for new and changed code from this date.** Retrofitting the
measured 289 module-level functions and 288 unfaced classes is its own backlog,
prioritised per module family, and it is explicitly not a precondition for
anything else. A sweeping mechanical rewrite of a tree with a 100% branch floor
would be a very large diff whose tests all still pass — which is the shape of
change that hides a regression rather than catching one.

**`domain/` is where this rule costs the most, and it does not get an
exemption.** The layer is stdlib-only, pure, and full of frozen dataclasses and
free functions; `rotation.py::select()` and `noloss.py::verify()` are
deliberately not objects. Those keep their behaviour, and the rule applies to
their form: the function becomes a method on a class that carries no state, and
the interface declares it. Purity is preserved because purity was never about
the absence of a class.

**The workspace tenants inherit it as they are touched, not on arrival.**
`src/vibey_runners/*` and `src/vibey_tools/*` are absorbed subtrees with their
own histories; `vibey-gh` in particular is 33 modules of mostly stdlib functions —
284 module-level functions beside 59 classes, 54 of them configuration dataclasses. Rewriting them on import would destroy the property the
import exists to create — that each package still builds and passes its own
suite unchanged. They converge module by module.

**An interface with one implementation is still correct.** The objection that a
single-implementation interface is ceremony is answered by the test double: the
second implementation is the one the tests use, and it exists from the first day.

**New enforcement.** `.importlinter` gains a contract per `interfaces/` package
as those packages appear, matching `interfaces-declare-only`. A structural check
that every class module has a matching interface module belongs with the
agent-surface parity test — a repo-introspecting static test, not a lint plugin.

---
name: blockchain-security-testing-and-ops
description: "Use when testing, auditing, securing, deploying, or operating on-chain systems. Covers the Foundry/Hardhat toolchain, fuzzing, invariant testing and formal verification, what to actually test, what actually loses money (access control, business logic, stolen keys) and the vulnerability canon (reentrancy, oracle manipulation, precision and rounding), security beyond the code (audits, bug bounties, incident response), deployment and verification, key management and multisigs, node and validator operations, and indexing, events, and frontend integration (viem/wagmi)."
---

# Blockchain Development: Testing, Security, Deployment, and Operations

> **Part 3 of 4** of the *Cryptocurrency and Blockchain Development* reference (plugin `cryptocurrency-development`), covering §9–§10 and §13. Sibling skills: `blockchain-protocol-layer` (§0–§3 and §11–§12), `blockchain-smart-contract-development` (§4–§8), `blockchain-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §16 → `blockchain-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — cryptography, distributed systems, or a security lesson the industry
>   has paid for repeatedly. Does not expire.
> - **[VERSIONED]** — protocol state, client versions, tooling, upgrade schedules. Moving
>   fast; verify before relying on it.
> - **[CONTESTED]** — genuine technical or design disagreement.
>
> **⚠️ GOTCHA** boxes mark the mistakes that lose money irreversibly. This domain has an
> unusually direct mapping from bug to financial loss, so those boxes carry more weight
> here than in an ordinary engineering reference.
>
> **Scope note:** this is an engineering document. It covers how these systems are built
> and how they fail. **It is not investment advice, and does not evaluate any asset as an
> investment.**
>
> **The three framings that organize everything below:**
> 1. **Deployed code is adversarial code running in public with money attached.** Every
>    function is callable by anyone, in any order, at any time, composed with contracts
>    that don't exist yet, by attackers who read your source and have unlimited attempts.
>    This is a fundamentally harsher environment than ordinary software.
> 2. **You cannot patch it.** Immutability is the point and also the problem. Upgradeability
>    is a design decision with its own large attack surface (§6 → `blockchain-smart-contract-development`), and "we'll fix it in the
>    next release" is not available to you.
> 3. **The expensive failures are boring.** Not exotic cryptography — **access control,
>    business logic, and stolen keys.** §10's data is unambiguous on this, and it should
>    reorder your security priorities.

---

## §9. Testing

### 9.1 The toolchain

**[VERSIONED] The Foundry/Hardhat choice is no longer binary, and the 2026 answer differs
from the 2022 answer.**

**Foundry** — Rust-based, **tests written in Solidity**, extremely fast, with built-in
fuzzing, invariant testing, mainnet forking, and cheatcodes (`vm.prank`, `vm.deal`,
`vm.expectRevert`, `vm.warp`). **The default for protocol and security-sensitive work.**

**Hardhat 3** — a major rewrite (new EDR engine, rebuilt config) that **added native
Solidity tests**, multichain/OP Stack simulation, and gas statistics. **This closed the two
historic gaps**: reported benchmarks put Hardhat 3 **within ~2× of Foundry on equivalent
test suites, versus the 10–20× penalty of Hardhat 2**, and Solidity-native testing removed
Foundry's exclusivity there.

**⚠️ The practical 2026 position: they coexist.** Foundry's `foundry.toml` is parsed by
Hardhat and artifacts can be shared, so many teams use **Foundry for fast unit/fuzz/
invariant testing of core logic and Hardhat for TypeScript integration tests, deployment
scripts, and L2 simulation**. **Pin a shared solc version across both** to avoid
compiler-version drift. The genuinely wrong move is choosing Hardhat in 2026 because a 2022
tutorial said so, then trying to retrofit Foundry-level test speed into a deeply
Hardhat-coupled codebase.

### 9.2 What to actually test

**[DURABLE] Unit tests are the floor, not the goal.** The techniques that find real bugs:

- **Fuzzing** — random inputs against properties. `forge test` does this natively; **turn it
  on for every function taking a numeric argument.**
- **Invariant / stateful fuzzing** — the highest-value technique available to most teams.
  Define properties that must hold across *any sequence* of calls ("total supply equals the
  sum of balances," "the vault is never insolvent," "no user can withdraw more than they
  deposited"), then let the fuzzer attack them. **Echidna** and **Medusa** are the
  specialist tools.
- **Fork testing** — run against real mainnet state and real dependencies. Catches
  integration assumptions that mocks hide.
- **Formal verification** — **Certora Prover**, **Halmos**, **Kontrol**, the SMTChecker.
  Mathematically proves properties hold under all inputs. **[VERSIONED] Increasingly a
  standard offering from security firms rather than an exotic add-on**, and it's the gold
  standard for high-value protocols.
- **Static analysis** — **Slither** (run it; it's fast and catches real things),
  **Mythril**, **Aderyn**.
- **Differential testing** against a reference implementation.
- **Coverage** — necessary, wildly insufficient. 100% line coverage tells you nothing about
  whether you tested the *adversarial* path.

---

## §10. Security

### 10.1 What actually loses money — start here

**[VERSIONED, and it should reorder your priorities.]** The empirical picture from 2025–2026
incident data is unambiguous and does not match where most developer attention goes.

**By loss category** (OWASP Smart Contract Top 10 for 2026, built from 2025 incident data
across 149 documented incidents totalling ~$1.42B):
```
Access control vulnerabilities   $953.2M   ← the overwhelming majority
Logic errors                      $63.8M
Reentrancy                        $35.7M
Flash loan exploits               $33.8M
```
**⚠️ Read that again. Access control is roughly fifteen times the loss of logic errors and
twenty-seven times reentrancy.** The most devastating attacks don't exploit exotic
cryptography — **they exploit mundane permission mistakes.** Hacken's 2025 data agrees:
access-control exploits drove ~59% of total losses, smart-contract vulnerabilities ~8%.

**And the bigger shift [VERSIONED]:** **smart contract exploit losses fell ~89%
year-over-year in Q1 2026** per DefiLlama — audits and architecture are working — **and it
didn't reduce total losses, because attackers moved to the humans.** Q1 2026 saw ~$450M lost
across 145 incidents, of which **phishing and social engineering accounted for ~$306M,
nearly two-thirds**. A single January social-engineering attack drained **$282M without
touching a line of code.** Six audited protocols were breached in that quarter; **one had
passed 18 prior audits.**

**⚠️ The operational consequence: your security budget is probably misallocated.** Code
audits address code vulnerabilities. They would not have prevented the largest 2026
incidents. **Key management, operational security, insider risk, and social-engineering
resistance now deserve first-class attention alongside the audit** — and note that
**Chainalysis attributes roughly 76% of 2026 crypto hack losses to state-backed actors
linked to Lazarus Group**, whose approach includes six-month social-engineering campaigns
and embedding operatives as IT workers. That is a different threat model than "did we
check-effects-interactions correctly."

### 10.2 The vulnerability canon

**[DURABLE] Know these cold. Most exploits are known classes hitting code that skipped
review, not zero-days.**

| Class | Mechanism | Defense |
|---|---|---|
| **Broken access control** | Missing/incorrect modifier; unprotected initializer or upgrade | §6.2 → `blockchain-smart-contract-development`. **Audit every privileged path** |
| **Reentrancy** | External call before state update; also **cross-function** and **read-only** (view function returns stale mid-transaction state) | **Checks-Effects-Interactions**; `nonReentrant`; transient storage |
| **Oracle manipulation** | Spot price from a manipulable source | §8.2 → `blockchain-smart-contract-development` |
| **Integer issues** | Overflow on pre-0.8 or in `unchecked`; **precision loss from division-before-multiplication**; rounding in the protocol's favour | 0.8+; order operations carefully; round deliberately |
| **Unchecked return values** | `call`/`send`/non-standard ERC-20 silently failing | Check returns; `SafeERC20` |
| **DoS** | Unbounded loops; a reverting recipient blocking a queue; gas griefing | Bound loops; **pull over push** |
| **Front-running / MEV** | Ordering | Slippage limits, deadlines, commit-reveal (§8.4 → `blockchain-smart-contract-development`) |
| **Signature issues** | Replay across chains/contracts, missing nonce, **`ecrecover` malleability**, signatures for the zero address | EIP-712 with full domain; nonces; OZ `ECDSA` |
| **Weak randomness** | `block.timestamp`, `blockhash`, `block.prevrandao` | **On-chain randomness is not private.** Use a VRF |
| **Delegatecall to untrusted code** | Attacker controls your storage | Never delegatecall to user input |
| **Uninitialized proxies** | §6.1 → `blockchain-smart-contract-development` | `_disableInitializers()` |
| **First-depositor / donation** | Share-price manipulation in vaults | Virtual shares; seed the vault |
| **Price/liquidity assumptions** | Assuming deep liquidity, or a pool that can't be drained | Model the adversarial case |

### 10.3 Beyond the code

**⚠️ Verify your contracts on the block explorer.** Chainalysis documented five protocols
in six months where the **exploited contract was the protocol's own and was unverified**,
totalling ~$36.7M — and noted that in an era of easy decompilation, unverified code buys you
nothing while destroying user trust and third-party review.

**Bug bounties** (Immunefi is the venue) are cheap relative to an exploit. **Monitoring and
incident response** — Forta, OpenZeppelin Defender, custom watchers — plus a **rehearsed
pause procedure**. **Timelocks** give users an exit window. And **[VERSIONED] the rise of
AI-assisted exploit development is likely accelerating**, per Chainalysis — the attacker's
cost of finding a bug in public bytecode is falling.

**Audit reality check**: costs range from roughly $3,000 for a simple contract to $100,000+
for complex multi-contract systems. **⚠️ An audit is a snapshot of specific code at a
specific commit by fallible humans under time pressure. It is not a guarantee**, as the
protocol with 18 prior audits demonstrated. Get multiple audits for high value, fix
findings *and* their root causes, and re-audit after changes.

---

## §13. Deployment and Operations

### 13.1 Deployment

**Checklist**: audited and findings resolved · deployed to a testnet and exercised ·
**exact compiler version pinned** · optimizer settings recorded · **deterministic build
reproducible** · constructor arguments verified · **source verified on the explorer** (§10.3)
· ownership transferred to a multisig/timelock, **not an EOA** · initializers called and
locked · pause mechanism tested · monitoring live · **incident runbook written before
launch**.

**CREATE2** gives deterministic addresses across chains — useful, and note that a
counterfactual address can receive funds before the contract exists.

### 13.2 Key management

**[DURABLE] This is now a first-order security concern rather than an afterthought (§10.1).**
Hardware wallets for anything meaningful. **Multisig (Safe) for protocol control** — and
**verify what you're signing**, since blind signing is how multisig holders get drained.
Timelocks. Separate deploy keys from admin keys from operational keys. **Never put a
private key or mnemonic in a repo, an env file that gets committed, or a CI log** — key
compromise produced the *largest single losses* in 2026's incident data.

### 13.3 Node and validator ops

Client updates on fork deadlines (§3.1 → `blockchain-protocol-layer`) — **fork weeks are when self-managed infrastructure
hurts most**. Run a minority client (§1.3 → `blockchain-protocol-layer`). Monitor sync status, peer count, attestation
effectiveness, and disk headroom. Test on testnets before mainnet forks. **Slashing
protection databases must never be lost or duplicated across machines** — running the same
validator key in two places is the classic self-inflicted slashing.

### 13.4 Indexing and frontends

**[DURABLE] Events are your API to the off-chain world**, and under-emitting is a design
error you'll regret. **Indexers**: The Graph, Ponder, Subsquid, or a custom
`eth_getLogs` + reorg-handling pipeline. **⚠️ Handle reorgs** — data you indexed can be
un-happened, and an indexer that assumes finality too early will serve wrong data.

**Frontend**: viem/wagmi (the current standard), RainbowKit or ConnectKit for wallet
connection, WalletConnect for mobile. **⚠️ Show users what they're signing** in human terms;
opaque signature prompts are the substrate of the phishing losses in §10.1.

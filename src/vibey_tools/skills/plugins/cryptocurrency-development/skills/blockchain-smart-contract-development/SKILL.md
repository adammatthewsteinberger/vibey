---
name: blockchain-smart-contract-development
description: "Use when writing or reviewing smart contracts. Covers the EVM execution model, gas and storage, EVM-compatible vs EVM-equivalent chains, Solidity and the alternatives (Vyper, Huff, Yul), contract architecture (upgradeability and proxies, access control, design principles), the token and application standards (ERC-20/721/1155/4626, account abstraction and ERC-4337), and DeFi primitives — AMMs, lending, oracles, flash loans, and MEV."
---

# Blockchain Development: EVM, Solidity, Contract Architecture, Standards, and DeFi

> **Part 2 of 4** of the *Cryptocurrency and Blockchain Development* reference (plugin `cryptocurrency-development`), covering §4–§8. Sibling skills: `blockchain-protocol-layer` (§0–§3 and §11–§12), `blockchain-security-testing-and-ops` (§9–§10 and §13), `blockchain-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    is a design decision with its own large attack surface (§6), and "we'll fix it in the
>    next release" is not available to you.
> 3. **The expensive failures are boring.** Not exotic cryptography — **access control,
>    business logic, and stolen keys.** §10 → `blockchain-security-testing-and-ops`'s data is unambiguous on this, and it should
>    reorder your security priorities.

---

## §4. The EVM

### 4.1 The execution model

**[DURABLE]** A **stack machine** (1024-deep, 256-bit words) with four data locations, and
understanding the distinction between them is the single most load-bearing piece of EVM
knowledge:

| Location | Persistence | Cost | Notes |
|---|---|---|---|
| **Stack** | Transient | Cheapest | 1024 slots, 256-bit words |
| **Memory** | Per-call | Cheap, **expands quadratically** | Byte-addressed scratch space |
| **Storage** | **Permanent, on-chain** | **Very expensive** | 256-bit → 256-bit map per contract |
| **Calldata** | Read-only input | Cheap to read | Cheaper than memory for large read-only args |
| **Transient storage** (EIP-1153) | Cleared at end of tx | Cheap | `TSTORE`/`TLOAD` — reentrancy guards, callbacks |

**[DURABLE] Storage dominates gas cost.** A cold `SLOAD` is ~2100 gas, a zero→nonzero
`SSTORE` is ~20,000, and a nonzero→nonzero write ~2900 (with refunds for clearing).
**Almost all gas optimization is really storage-access optimization**, and everything else
is noise by comparison.

**Call types**: `CALL` (new context, `msg.sender` = caller), **`DELEGATECALL`** (⚠️
**executes target code in the caller's storage context** — the basis of proxies (§6.1)
and of some of the worst bugs in the field's history), `STATICCALL` (read-only, reverts on
state change), and `CREATE`/`CREATE2` (the latter gives deterministic addresses from a
salt, enabling counterfactual deployment).

**Reverts** unwind all state changes in the frame and refund remaining gas. **[DURABLE]
The atomicity of a transaction is your most powerful safety property** — if any part
reverts, none of it happened. Design around it.

### 4.2 Gas

```
tx cost = 21,000 base
        + calldata (4 gas/zero byte, 16/non-zero)
        + execution opcodes
        + storage (dominant)
  fee   = gas_used × (base_fee + priority_fee)   [EIP-1559; base fee is BURNED]
```
**⚠️ Gas is a security parameter, not just a cost.** Unbounded loops over user-controlled
arrays are a **denial-of-service vulnerability** — if the array grows past the block gas
limit, the function becomes permanently uncallable, potentially locking funds forever.

**The 63/64 rule** (EIP-150): a call forwards at most 63/64 of remaining gas, so the caller
always retains enough to handle the return. **⚠️ This makes "gas griefing" possible** — a
callee can deliberately consume its allocation to make the caller fail.

### 4.3 EVM-compatible vs. EVM-equivalent

**[DURABLE] The distinction matters when porting.** "EVM-compatible" chains may differ in
opcode behaviour, gas costs, precompiles, block time assumptions, and `block.timestamp`
semantics. **"EVM-equivalent"** claims byte-for-byte identical execution. **⚠️ Never assume
a contract audited on mainnet is safe on another EVM chain without re-review** — different
gas schedules alone can turn safe code into a DoS.

---

## §5. Solidity and the Contract Languages

### 5.1 Solidity

**[VERSIONED] The 0.8.x line is current** — **0.8.36 (July 2026)** was the latest stable at
the time of writing, with 0.8.37 in nightly development. Releases are frequent and often
carry security fixes; **0.8.36 alone included two medium-severity security fixes.**

**[DURABLE] Pin an exact compiler version in production.** Use `pragma solidity 0.8.30;`
rather than `^0.8.0`. Floating pragmas mean your deployed bytecode depends on whoever
compiled it, which breaks reproducible builds and verification.

**What 0.8 changed and why it matters**: **arithmetic overflow and underflow revert by
default** since 0.8.0. This eliminated an entire vulnerability class — and it's why
**contracts still running on 0.6.x and 0.7.x are a live risk**. One 2026 exploit hit a
contract on **Solidity 0.6.10, which lacks automatic overflow protection**, after nearly
five years deployed. `unchecked { }` opts out where you've proven safety and want the gas.

**The essentials**:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

contract Example {
    // visibility: external | public | internal | private  — always explicit
    // state mutability: pure | view | payable | (default)
    // storage vs memory vs calldata — declare deliberately

    error InsufficientBalance(uint256 available, uint256 required); // custom errors:
                                                                    // cheaper than strings
    event Transfer(address indexed from, address indexed to, uint256 value);
        // `indexed` → topics, filterable by log queries; max 3 indexed params

    modifier onlyOwner() { if (msg.sender != owner) revert Unauthorized(); _; }

    receive() external payable {}   // plain ETH transfers
    fallback() external payable {}  // unmatched calldata
}
```
**⚠️ `msg.sender` vs `tx.origin`**: **never use `tx.origin` for authorization.** It's the
original EOA, so any contract the user calls can relay a call to you and pass the check.
This is a textbook phishing vector.

**`viaIR`** (the IR-based codegen pipeline) produces better optimization and is increasingly
the default in serious projects; enable it deliberately and re-test, since it changes
generated code. **Yul** is the intermediate language, and **inline assembly** drops to it —
use sparingly, and know that **assembly bypasses Solidity's safety checks entirely**.

### 5.2 The alternatives

**Vyper** — deliberately restricted, Python-like, no inheritance, no inline assembly,
bounded loops. **[CONTESTED]** Its restrictions are a real security argument; against it,
a smaller ecosystem and its own compiler-bug history (a Vyper reentrancy-guard compiler bug
caused a major 2023 exploit — **the compiler is part of your trust surface**).
**Huff / Yul** — near-assembly, for extreme gas optimization. Very high risk.
**Fe**, **Sway** (FuelVM), **Cairo** (Starknet), **Move** (Aptos/Sui — resource-oriented,
with a genuinely different and interesting ownership model), **Rust** (Solana, CosmWasm,
NEAR).

---

## §6. Contract Architecture

### 6.1 Upgradeability

**[CONTESTED, and it's the most consequential architectural decision you'll make.]**
*For upgradeability*: bugs are otherwise unfixable, requirements change, and migrations are
brutal for users. *Against*: it reintroduces trust, adds a large attack surface, and
**upgrade keys are themselves a top-tier target.**

**The patterns:**
```
Transparent Proxy    proxy DELEGATECALLs to impl; admin calls handled at proxy
UUPS (EIP-1822)      upgrade logic lives in the IMPLEMENTATION — cheaper,
                     ⚠️ but you can brick it by deploying an impl without upgrade logic
Beacon               many proxies read one beacon → upgrade all at once
Diamond (EIP-2535)   multi-facet routing; powerful, complex, contested
Immutable            no upgrade path. The safest and least forgiving option
```
> **⚠️ GOTCHA — the proxy failure modes, all of which have caused real losses:**
> 1. **Storage collisions.** The implementation's storage layout must be append-only across
>    upgrades. Reordering or inserting a variable corrupts state. Use **namespaced storage
>    (ERC-7201)** or storage gaps.
> 2. **Uninitialized implementation contracts.** The logic contract must have its
>    initializer disabled (`_disableInitializers()`), or someone else initializes it and,
>    with UUPS, can `selfdestruct`/brick it.
> 3. **Constructors don't run** in proxy context. Use `initialize()` with an
>    initializer guard.
> 4. **`immutable` and constructor-set state** live in the implementation's code, not the
>    proxy's storage — a frequent source of subtle wrongness.
> 5. **The upgrade key is the whole security model.** A timelock plus a multisig is the
>    minimum for anything holding real value.

### 6.2 Access control

**[DURABLE] This is the highest-value section in the document, because access control is
the single largest category of on-chain loss (§10.1 → `blockchain-security-testing-and-ops`).**

Patterns: `Ownable` (simple, single point of failure), `Ownable2Step` (**use this instead** —
transfer requires acceptance, preventing a typo'd address from permanently orphaning the
contract), `AccessControl` (role-based), timelocks (mandatory delay on privileged actions,
giving users time to exit), and multisig (Safe is the standard) or full DAO governance.

**The checklist for every privileged function**: is it actually restricted? Is the modifier
present on *every* path including the initializer and the upgrade function? Can it be
called before initialization? Is the role transferable, and safely? Is there a timelock on
anything that can drain or brick the system?

### 6.3 Design principles

**[DURABLE]** **Checks-Effects-Interactions** — validate, then update your state, *then*
make external calls. This ordering alone prevents most reentrancy. **Pull over push** for
payments — let users withdraw rather than pushing funds, so one reverting recipient can't
block everyone. **Fail loudly** — revert with custom errors rather than returning false.
**Minimize privileged surface.** **Emit events for everything** an off-chain system needs
(§13.4 → `blockchain-security-testing-and-ops`). **Bound every loop.** **Handle the ERC-20 misbehaviours** in §7.1.

---

## §7. Standards

### 7.1 Tokens

| Standard | What |
|---|---|
| **ERC-20** | Fungible tokens. ⚠️ See below |
| **ERC-721** | NFTs. `safeTransferFrom` invokes a receiver hook — **a reentrancy vector** |
| **ERC-1155** | Multi-token, batch operations |
| **ERC-4626** | Tokenized vaults. ⚠️ **Inflation/donation attacks on the first depositor** are the classic bug — mitigate with virtual shares or a dead-shares seed |
| **ERC-2612** | `permit` — gasless approvals via signature |
| **ERC-777** | ⚠️ Hooks caused real reentrancy exploits. **Largely deprecated in practice** |

> **⚠️ GOTCHA — ERC-20 is a standard that many tokens don't follow, and assuming compliance
> is how integrations break:**
> - **Non-standard return values** — USDT and others don't return a bool. **Use
>   OpenZeppelin's `SafeERC20`.**
> - **Fee-on-transfer tokens** — the amount received ≠ the amount sent. **Measure balance
>   before and after**, don't trust the argument.
> - **Rebasing tokens** — balances change without transfers.
> - **Non-18 decimals** — USDC has 6. Hardcoding 18 is a recurring, expensive bug.
> - **Blocklists** — USDC/USDT can freeze addresses, so a transfer can revert forever.
> - **Approval race** — some tokens require setting the allowance to 0 before changing it.
> - **Malicious tokens** — if you let anyone list a token, you've let them run arbitrary
>   code inside your callstack.

### 7.2 The rest

**ERC-165** (interface detection), **EIP-712** (typed structured signing — what makes
signature prompts human-readable; ⚠️ **always include a domain separator with `chainId` and
the verifying contract, or your signature is replayable across chains and contracts**),
**ERC-1271** (contract signature validation — necessary for smart accounts),
**ERC-7201** (namespaced storage layout, §6.1).

### 7.3 Account abstraction

**[VERSIONED] The most consequential UX change in years, and it landed in two pieces.**
**ERC-4337** implements smart accounts entirely outside the protocol — UserOperations,
a Bundler, an EntryPoint, and Paymasters (which enable sponsored gas and paying fees in
ERC-20). **EIP-7702** (shipped in **Pectra, May 2025**) went further by letting a regular
EOA temporarily execute as a smart contract, so **existing wallets** gain batching, session
keys, sponsored gas, and social recovery **without migrating to a new address**.

**⚠️ EIP-7702 is a live security consideration, not just a feature.** An EOA delegating to
malicious code is a new and effective drainer pattern, and wallet and contract code that
assumes "`msg.sender` with no code is a plain EOA" is now making an unsafe assumption.

---

## §8. DeFi Primitives and MEV

### 8.1 The building blocks
**AMMs** (constant product `x·y=k`; concentrated liquidity; the **impermanent loss** that
LPs bear), **lending** (over-collateralization, health factors, liquidation incentives),
**stablecoins** (fiat-backed, over-collateralized crypto-backed, and algorithmic — ⚠️ the
last category has an extensive failure history), **derivatives**, and **liquid staking**.

**[DURABLE] Composability is the superpower and the risk.** Contracts calling contracts
calling contracts means your protocol's safety depends on dependencies you don't control,
and a bug three layers down can drain you.

### 8.2 Oracles

**[DURABLE] Oracle manipulation is a top-tier exploit class, and the fix is well known.**
```
⚠️ NEVER:   price = reserve1 / reserve0      // spot price from a DEX pool
                                              // — a flash loan moves it in one tx
✓  INSTEAD: Chainlink / Pyth / RedStone push or pull feeds
            TWAPs over a meaningful window
            multiple independent sources with deviation checks
```
And check the feed's own health: staleness (`updatedAt`), the L2 sequencer uptime feed,
and sane min/max bounds. **⚠️ A stale oracle reading treated as current is itself an
exploit** — several protocols have lost funds this way without any manipulation at all.

### 8.3 Flash loans

Uncollateralized loans that must be repaid in the same transaction. **[DURABLE] Flash loans
are not the vulnerability — they are the capital amplifier that makes an existing
vulnerability profitable.** They turn "an attacker with $100M could do this" into "anyone
can do this, right now, for a fee." **Assume every attacker has unlimited capital for one
transaction**, and your threat model becomes correct.

### 8.4 MEV

**[DURABLE]** Maximal Extractable Value — profit from ordering, inserting, or censoring
transactions. **Front-running**, **back-running**, **sandwich attacks** (the one that
directly harms ordinary users), **liquidations** and **arbitrage** (arguably beneficial).

**Mitigations for builders**: slippage limits and deadlines on every swap (**a swap with no
slippage bound is free money for a sandwicher**), commit-reveal schemes, batch auctions,
private mempools/order flow, and designing so ordering doesn't matter.

**The infrastructure**: proposer-builder separation currently runs through **out-of-protocol
relays** (MEV-Boost), which is a real centralization dependency — **which is precisely what
Glamsterdam's ePBS (§3.2 → `blockchain-protocol-layer`) is intended to bring in-protocol.**

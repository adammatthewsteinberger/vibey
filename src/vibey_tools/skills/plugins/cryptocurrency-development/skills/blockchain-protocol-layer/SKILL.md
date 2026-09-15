---
name: blockchain-protocol-layer
description: "Use when working on or reasoning about blockchain protocol development rather than smart contracts: what a blockchain actually is, Ethereum's post-Merge architecture (execution and consensus layers, finality, slashing), client diversity as systemic risk, node types and working with nodes, how protocol changes happen (the EIP process, recent and upcoming hard forks, the changed fee environment), the rollup model and building an L2 or app-chain, and cross-chain bridges and their failure modes. Includes the router for the whole cryptocurrency-development reference."
---

# Blockchain Development: Protocol Layer, Clients, Upgrades, L2s, and Cross-Chain

> **Part 1 of 4** of the *Cryptocurrency and Blockchain Development* reference (plugin `cryptocurrency-development`), covering §0–§3 and §11–§12. Sibling skills: `blockchain-smart-contract-development` (§4–§8), `blockchain-security-testing-and-ops` (§9–§10 and §13), `blockchain-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    business logic, and stolen keys.** §10 → `blockchain-security-testing-and-ops`'s data is unambiguous on this, and it should
>    reorder your security priorities.

---

## §0. Routing

### 0.1 Two very different jobs

**[DURABLE] "Crypto development" means two largely disjoint skill sets**, and conflating
them is the most common orientation error:

| | **Protocol development** | **Application development** |
|---|---|---|
| You build | Clients, consensus, VMs, L2 stacks, cryptography | Smart contracts and the systems around them |
| Languages | Go, Rust, C#, Java, Zig, Nim | Solidity, Vyper, Huff, Yul |
| Failure mode | Chain splits, finality failures, mass slashing | Drained contracts |
| Review culture | Multi-client testing, devnets, spec conformance | Audits, fuzzing, formal verification |
| Sections | §1, §2, §3, §11, §12 | §4–§10 → `blockchain-smart-contract-development`, `blockchain-security-testing-and-ops`, §13 → `blockchain-security-testing-and-ops` |

### 0.2 The question router

| Asked about... | Go to |
|---|---|
| Consensus, finality, the protocol layer | §1 |
| Ethereum clients and node operation | §2 |
| The upgrade process, EIPs, hard forks | §3 |
| The EVM execution model, gas, storage | §4 → `blockchain-smart-contract-development` |
| Solidity and the contract languages | §5 → `blockchain-smart-contract-development` |
| Contract architecture: proxies, upgrades, access control | §6 → `blockchain-smart-contract-development` |
| Standards: ERC-20/721/1155/4626, account abstraction | §7 → `blockchain-smart-contract-development` |
| DeFi primitives, oracles, MEV | §8 → `blockchain-smart-contract-development` |
| Testing: Foundry, Hardhat, fuzzing, formal verification | §9 → `blockchain-security-testing-and-ops` |
| Security: the vulnerability canon and what actually loses money | §10 → `blockchain-security-testing-and-ops` |
| L2s, rollups, and building a chain | §11 |
| Cross-chain and bridges | §12 |
| Deployment, keys, ops, indexing, frontends | §13 → `blockchain-security-testing-and-ops` |
| Interpretability of on-chain data, analytics | §13.4 → `blockchain-security-testing-and-ops` |
| "Don't do this" | §14 → `blockchain-reference` |
| "Which approach is better?" | §15 → `blockchain-reference` (contested) |
| "Is this still current?" | §16 → `blockchain-reference` |
| Docs, books, people | §17 → `blockchain-reference` |

---

## §1. The Protocol Layer

### 1.1 What a blockchain actually is

**[DURABLE]** A replicated state machine with **Sybil-resistant leader election** and a
**fork-choice rule**, producing eventual (or explicit) agreement on an ordered log.
Everything else is engineering detail.

```
mempool → block proposer selected → block built → propagated
  → validated by every node independently → fork choice → finality
```

**Consensus families:**
- **Proof of Work** — Sybil resistance by burned energy. Probabilistic finality (confirmations).
  Simple, robust, expensive. Bitcoin.
- **Proof of Stake** — Sybil resistance by bonded capital, with **slashing** for provable
  misbehaviour. Ethereum uses **Gasper** (LMD-GHOST fork choice + Casper FFG finality),
  giving **explicit finality** after two epochs (~13 minutes).
- **BFT-style** (Tendermint/CometBFT, HotStuff derivatives) — instant finality, smaller
  validator sets, liveness fails if >1/3 are offline.
- **DAG / leaderless** and other designs — real, less battle-tested.

**[DURABLE] The trade-off that never goes away**: decentralization, security, and
scalability pull against each other, and every design picks a point. **Be suspicious of any
claim to have escaped it** — usually the escape is a validator set small enough to be a
distributed database with extra steps.

### 1.2 Ethereum's post-Merge architecture

```
┌─────────────────────────┐        ┌──────────────────────────┐
│ CONSENSUS CLIENT        │ Engine │ EXECUTION CLIENT         │
│ (beacon chain, PoS)     │◄──API─►│ (EVM, state, mempool)    │
│ Lighthouse, Prysm, Teku,│        │ Geth, Nethermind, Reth,  │
│ Nimbus, Lodestar,       │        │ Besu, Erigon, ethrex     │
│ Grandine                │        │                          │
└─────────────────────────┘        └──────────────────────────┘
```
**[DURABLE] You must run both.** This split, formalized at The Merge (September 2022), is
the single most important structural fact about running Ethereum infrastructure, and it
surprises people who last looked before 2022.

**Validator economics**: 32 ETH per validator (**EIP-7251 raised the effective max balance
to 2048 ETH**, allowing consolidation), duties are attesting and occasionally proposing,
and **slashing** punishes provable equivocation while **inactivity leaks** punish being
offline during non-finality.

### 1.3 Client diversity — a genuine systemic risk

**[DURABLE] If one client runs a supermajority of validators, a bug in it can finalize an
invalid chain or cause mass slashing.** The thresholds that matter: **>1/3 breaks
finality; >2/3 can finalize a bad chain.** This is not theoretical — **Reth suffered a
severe network-wide outage on 2 September 2025** processing a specific block, taking down
most Reth nodes on mainnet; operators running a multi-client setup stayed up.

**[VERSIONED]** Execution-layer diversity has genuinely improved. Geth's share has fallen
from a historic ~84% to roughly **36–41%**, with **Nethermind ~23–32%**, **Reth ~14–15%**,
**Besu ~7–12%**, and **Erigon ~2–5%** depending on the measurement source. ⚠️ **The
sources disagree substantially** because they measure different populations (peer-visible
nodes vs. self-reported validators vs. staking-community surveys) — one 2026 staking survey
found **Nethermind ~45%, Geth ~33%, Besu ~15%** within that community. **The consensus
layer is the bigger worry**, with Lighthouse and Prysm both large.

**⚠️ If you run validators, run a minority client, and consider running more than one.**
This is the rare case where the socially responsible choice is also the operationally
safer one.

---

## §2. Nodes and Clients

### 2.1 Node types

| Type | Stores | Use |
|---|---|---|
| **Full node** | Current state + recent history; verifies everything | The default. What you should run |
| **Archive node** | All historical state at every block | Analytics, indexers, `eth_call` at old blocks. **Very large** |
| **Light client** | Headers + proofs | Mobile, embedded; the Verge roadmap's target |
| **Validator** | Full node + consensus client + signing keys | Staking |

**[VERSIONED] Reth is notably fast to sync** — substantially faster than Geth's baseline on
equivalent NVMe hardware. **NVMe SSD is non-negotiable** for any client; spinning disks and
most SATA SSDs cannot keep up with state access patterns.

### 2.2 Working with nodes

**JSON-RPC** is the universal interface: `eth_call` (simulate, no state change),
`eth_estimateGas`, `eth_sendRawTransaction`, `eth_getLogs` (⚠️ heavily rate-limited by
providers and the usual source of "why is my indexer slow"), `eth_getStorageAt`,
`debug_traceTransaction` (⚠️ archive/debug-enabled nodes only, and the most useful
debugging tool you have).

**Libraries**: **viem** (TypeScript — the modern default, better typing and DX than its
predecessor), **ethers.js** (still widely used), **web3.js** (legacy), **web3.py**,
**Alloy** (Rust — the Foundry/Reth ecosystem's stack), **Nethereum** (.NET), **web3j** (Java).

**⚠️ Running your own node vs. using a provider is a real architectural decision**, not a
purity question. Providers (Alchemy, Infura, QuickNode, Chainstack) are operationally
simpler; your own node removes a trust and censorship dependency and removes rate limits.
**Anything that must not be censorable should not depend on one provider.**

---

## §3. Protocol Upgrades and the EIP Process

### 3.1 How changes happen

```
idea → EIP draft → ACD calls (All Core Devs, Execution + Consensus)
  → devnets → public testnets (Sepolia, Holesky/Hoodi) → MAINNET FORK
```
**EIP tracks**: **Core** (consensus-breaking), **Networking**, **Interface**, and **ERC**
(application-layer standards — §7 → `blockchain-smart-contract-development`). **[DURABLE] ERCs are the ones application developers
care about; Core EIPs are the ones that break your node if you don't upgrade.**

**[DURABLE] Hard forks are coordinated flag days.** Every execution client (Geth,
Nethermind, Besu, Erigon, Reth) and every consensus client (Lighthouse, Prysm, Teku,
Nimbus, Lodestar, Grandine) ships a **mandatory release**, and **testnets always fork
first** — that gap is your window to find problems while they're cheap.

**⚠️ A network upgrade never requires users to "migrate" or "upgrade" their tokens.**
Balances, addresses, and keys are unaffected. **Anyone telling holders to upgrade their ETH
for a fork is running a scam** — and this recurs at every single fork.

### 3.2 The recent and upcoming forks

**[VERSIONED]** Ethereum has settled into a roughly **twice-yearly** cadence:

| Fork | Date | Headline |
|---|---|---|
| **The Merge** | Sept 2022 | PoW → PoS; ~99.95% energy reduction |
| **Shapella** | Apr 2023 | Staking withdrawals |
| **Dencun** | Mar 2024 | **EIP-4844 proto-danksharding** — blobs; cut L2 data costs ~90% |
| **Pectra** | May 2025 | **EIP-7702** (EOAs can act like smart accounts, §7.3 → `blockchain-smart-contract-development`); **EIP-7251** validator consolidation |
| **Fusaka** | **3 Dec 2025** | **PeerDAS** — validators sample blob data instead of downloading all of it; gas limit to ~60M |
| **Glamsterdam** | **targeted 2026** | **EIP-7732 (ePBS)** and **EIP-7928 (Block-Level Access Lists)**; **EIP-7904** gas repricing |
| **Hegotá** | 2027 | **FOCIL** headlining; Verkle discussed |

**⚠️ Glamsterdam's date is genuinely unsettled and the sources conflict** — official
Ethereum roadmap material has listed **Q4 2026**, other coverage has said H1 2026 or "second
half of 2026," and developers consistently stress it depends on testnet validation.
**Treat any specific date as provisional and check Forkcast or ethereum.org.**

**Why Glamsterdam matters to builders**: **Block-Level Access Lists** declare what state a
block touches *before* execution, enabling **parallel transaction execution**; **ePBS**
brings proposer-builder separation into the protocol (currently it depends on out-of-protocol
relays, a real centralization dependency — §8.4 → `blockchain-smart-contract-development`) and lays groundwork for inclusion lists;
and **EIP-7904 reprices gas** to realign costs with actual computational resources, since
many current gas prices were set years ago and no longer reflect modern hardware.

### 3.3 The fee environment has changed

**[VERSIONED, and it invalidates a very common mental model.]** If your assumptions about
Ethereum were formed in 2021–2023, they're out of date. **As of May 2026, standard gas has
run around 0.15 gwei with daily averages near 0.5 gwei** — a basic ETH transfer costing
under a cent, with typical days in the low single-digit cents. **"Ethereum mainnet is too
expensive for most apps" is now a stale default assumption.** Do the gas math for your
actual workload rather than relying on folklore.

---

## §11. Layer 2 and Building a Chain

### 11.1 The rollup model

**[DURABLE]** Execute off-chain, post data and proofs to L1, inherit L1 security for data
availability and settlement.

| Type | Validity | Withdrawal | Notes |
|---|---|---|---|
| **Optimistic** | Assumed valid; **fraud proofs** during a challenge window | **~7 days** (or fast via a liquidity provider) | OP Stack, Arbitrum. Simpler; the delay is the cost |
| **ZK / validity** | **Validity proof** verified on L1 | Minutes to hours | zkSync, Starknet, Scroll, Linea, Polygon zkEVM. Proving cost and complexity are the trade |
| **Validium / volition** | Validity proof, **data off-chain** | Fast | Cheaper; **weaker data-availability guarantees** |

**[DURABLE] The security question for any L2 is always the same three things**: who can
censor you, who can steal from you, and can you exit without permission? **L2Beat's stage
classification** is the honest scoring of exactly that, and it's the right first stop before
trusting any chain's marketing.

**⚠️ The centralized sequencer is the current reality.** Most rollups rely on a single
sequencer to order and execute transactions — a censorship risk and single point of failure.
**Forced-inclusion via L1 is the escape hatch**, and you should verify it exists and works.
**Decentralized sequencer designs are under active development but remain largely
unshipped.**

**Blobs (EIP-4844) are how L2 data gets cheap**, and **PeerDAS (Fusaka)** is what lets blob
capacity grow — validators sample columns rather than downloading every blob in full.

### 11.2 Building a chain

**[DURABLE] Ask first whether you need one.** A new chain means bootstrapping validators or
sequencers, liquidity, bridges, tooling, indexers, wallets, and users — and fragmenting
liquidity is usually a larger cost than whatever it buys.

If you do: **rollup-as-a-service stacks** (OP Stack, Arbitrum Orbit, ZK Stack, Polygon CDK,
Starknet's stack) are how most L2s are built now. **Cosmos SDK / CometBFT** for a sovereign
app-chain. **Polkadot parachains.** Fully custom is a multi-year effort.

**[VERSIONED] The client layer is adapting to this**: Nethermind implements each supported
L2 as a plugin with an OP Stack rollup node built directly into the client (replacing a
separate `op-node`), and **ethrex** is a Rust client whose same codebase runs as both an L1
execution client and a multi-prover ZK-rollup. **ZK-proving is being built into production
execution clients**, which is a meaningful shift in what a "client" is.

---

## §12. Cross-Chain

**[DURABLE] Bridges are the most-exploited category in the field's history, and the reason
is structural**: they hold concentrated value and must verify claims about a chain they
can't natively see.

**The models**: **lock-and-mint** (⚠️ the lockbox is a honeypot), **burn-and-mint**,
**liquidity networks**, **light-client / native verification** (the most secure, most
expensive), and **optimistic bridges**.

**The trust question to ask about any bridge**: *who attests that the source-chain event
happened?* A multisig? An external validator set? A light client? **A bridge secured by a
5-of-9 multisig has the security of a 5-of-9 multisig, regardless of what the marketing
says.**

**⚠️ Cross-chain message verification is where bridges break in practice.** A 2026 example:
an attacker crafted **fake Axelar messages that passed validation** and tricked a receiver
contract into releasing funds without a matching deposit — **missing access control in the
message receiver**, ~$3M across chains. The pattern (trusting an inbound message without
verifying the sender and the source chain) recurs constantly.

**Messaging protocols**: LayerZero, CCIP, Axelar, Wormhole, Hyperlane — each with a
different trust model you should be able to state in one sentence before integrating.

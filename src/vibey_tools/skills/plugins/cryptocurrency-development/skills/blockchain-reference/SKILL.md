---
name: blockchain-reference
description: "Use when reviewing blockchain or smart-contract work against known anti-patterns, weighing contested questions (upgradeable vs immutable, Solidity vs Vyper, Foundry vs Hardhat, optimistic vs ZK rollups, monolithic vs modular, whether an L2 is Ethereum, whether decentralization survives the incentives), checking whether protocol, client, or tooling state is still current (snapshot verified August 2026), finding the primary documentation, security references, books, and communities, or needing the quick-reference numbers, pre-deployment checklist, and triage. Companion to the other cryptocurrency-development skills."
---

# Blockchain Development: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 4 of 4** of the *Cryptocurrency and Blockchain Development* reference (plugin `cryptocurrency-development`), covering §14–§19. Sibling skills: `blockchain-protocol-layer` (§0–§3 and §11–§12), `blockchain-smart-contract-development` (§4–§8), `blockchain-security-testing-and-ops` (§9–§10 and §13). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §16 below for the currency snapshot and what goes stale first.

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

## §14. Anti-Patterns

| Anti-pattern | Why | Instead |
|---|---|---|
| Assuming your function is only called your way | Every function is public to the world, in any order | Design adversarially (§0 → `blockchain-protocol-layer` framing 1) |
| Focusing security effort on reentrancy | It's ~$35.7M vs access control's ~$953.2M | **Audit every privileged path** (§10.1 → `blockchain-security-testing-and-ops`) |
| Treating an audit as a guarantee | One breached protocol had passed 18 | Audits + fuzzing + invariants + monitoring (§9 → `blockchain-security-testing-and-ops`, §10.3 → `blockchain-security-testing-and-ops`) |
| Security budget entirely on code | Phishing/social engineering was ~2/3 of Q1 2026 losses | Key management and opsec as first-class (§10.1 → `blockchain-security-testing-and-ops`) |
| Floating pragma in production | Non-reproducible bytecode | Pin the exact solc version (§5.1 → `blockchain-smart-contract-development`) |
| Leaving contracts on Solidity <0.8 | No automatic overflow protection | Migrate; a 2026 exploit hit 0.6.10 code (§5.1 → `blockchain-smart-contract-development`) |
| `tx.origin` for authorization | Trivially phishable | `msg.sender` (§5.1 → `blockchain-smart-contract-development`) |
| External call before state update | Reentrancy | **Checks-Effects-Interactions** (§6.3 → `blockchain-smart-contract-development`) |
| Spot price from a DEX pool as an oracle | One flash loan moves it | Chainlink/TWAP/multi-source (§8.2 → `blockchain-smart-contract-development`) |
| Not checking oracle staleness | A stale price is itself an exploit | Check `updatedAt`, sequencer uptime (§8.2 → `blockchain-smart-contract-development`) |
| Assuming ERC-20 compliance | Non-standard returns, fees, rebases, 6 decimals, blocklists | `SafeERC20`; measure balance deltas (§7.1 → `blockchain-smart-contract-development`) |
| Hardcoding 18 decimals | USDC has 6 | Read `decimals()` |
| Unbounded loop over user-controlled array | **Permanent DoS**; funds can lock forever | Bound it; pull over push (§4.2 → `blockchain-smart-contract-development`, §6.3 → `blockchain-smart-contract-development`) |
| Pushing payments to users | One reverting recipient blocks everyone | Pull pattern (§6.3 → `blockchain-smart-contract-development`) |
| Swap with no slippage bound or deadline | Free money for a sandwicher | Always set both (§8.4 → `blockchain-smart-contract-development`) |
| On-chain randomness from block data | Miners/proposers and everyone else can see it | VRF (§10.2 → `blockchain-security-testing-and-ops`) |
| Reordering storage variables in an upgrade | **Storage collision corrupts state** | Append-only; ERC-7201 (§6.1 → `blockchain-smart-contract-development`) |
| Leaving an implementation contract uninitialized | Someone else initializes; UUPS can be bricked | `_disableInitializers()` (§6.1 → `blockchain-smart-contract-development`) |
| Constructor logic in an upgradeable contract | Constructors don't run in proxy context | `initialize()` with a guard (§6.1 → `blockchain-smart-contract-development`) |
| Single-step ownership transfer | A typo'd address orphans the contract forever | `Ownable2Step` (§6.2 → `blockchain-smart-contract-development`) |
| Owner as an EOA on a live protocol | One key, one compromise, total loss | Multisig + timelock (§6.2 → `blockchain-smart-contract-development`, §13.2 → `blockchain-security-testing-and-ops`) |
| Leaving contracts unverified | ~$36.7M lost across five such protocols; decompilation is easy anyway | Verify on the explorer (§10.3 → `blockchain-security-testing-and-ops`) |
| Deploying to another EVM chain without re-review | Different gas costs and opcodes | Re-audit per chain (§4.3 → `blockchain-smart-contract-development`) |
| Trusting an inbound cross-chain message | Fake messages passing validation is a live 2026 pattern | Verify sender **and** source chain (§12 → `blockchain-protocol-layer`) |
| Believing "decentralized" without checking | Most rollups have one sequencer; many bridges are a multisig | L2Beat stages; state the trust model (§11.1 → `blockchain-protocol-layer`, §12 → `blockchain-protocol-layer`) |
| Assuming 2021-era gas prices | Mainnet ran ~0.15 gwei in May 2026 | Do the gas math (§3.3 → `blockchain-protocol-layer`) |
| Blind-signing multisig transactions | How multisig holders get drained | Verify calldata (§13.2 → `blockchain-security-testing-and-ops`) |
| Running one validator key on two machines | Self-inflicted slashing | Slashing protection discipline (§13.3 → `blockchain-security-testing-and-ops`) |
| Running the supermajority client | Systemic risk, and Reth's 2025 outage shows the personal one | Minority client (§1.3 → `blockchain-protocol-layer`) |
| Under-emitting events | Your off-chain systems can't see state | Emit for everything indexed (§13.4 → `blockchain-security-testing-and-ops`) |
| Indexer that ignores reorgs | Serves data that got un-happened | Handle reorgs (§13.4 → `blockchain-security-testing-and-ops`) |

---

## §15. Contested Questions

**15.1 Upgradeable vs. immutable.** §6.1 → `blockchain-smart-contract-development`. The genuinely hard one. The middle position most
serious protocols land on: **upgradeable behind a timelock and a multisig, with a credible
path to eventual immutability**, so users can exit before any change takes effect.

**15.2 Solidity vs. Vyper.** §5.2 → `blockchain-smart-contract-development`. Vyper's restrictions are a real security argument;
against it, ecosystem size and its own compiler-bug history. **The deeper point either way:
the compiler is part of your trust surface.**

**15.3 Foundry vs. Hardhat.** §9.1 → `blockchain-security-testing-and-ops` — and this genuinely changed. The speed and
Solidity-testing arguments that decided it in 2022 are much weaker now that Hardhat 3 is
within ~2× and has native Solidity tests. **The 2026 answer is often "both, for different
phases."**

**15.4 Optimistic vs. ZK rollups.** Optimistic: simpler, mature, cheap to prove, 7-day
withdrawals. ZK: fast finality, higher proving cost and complexity, less mature tooling.
**The gap has narrowed considerably**; the honest answer depends on your withdrawal-latency
requirement and your tolerance for a younger stack.

**15.5 Monolithic vs. modular blockchains.** Modular (separate execution, settlement,
consensus, DA) versus doing it all in one chain. *Modular*: specialization and scaling.
*Monolithic*: composability, simpler security reasoning, no fragmented liquidity. Ethereum
has bet decisively on modular via rollups; several competitors have not.

**15.6 Is an L2 "Ethereum"?** A real ecosystem argument about whether rollup-centric scaling
delivers Ethereum's security guarantees to users in practice, given centralized sequencers,
upgrade keys, and bridge risk. **L2Beat's stage framework exists precisely because the
answer is "it depends on the specific L2."**

**15.7 Does decentralization survive the incentives?** Staking concentration, MEV relay
centralization, RPC-provider concentration, and client supermajorities are all real
measured pressures against the stated design goals. **The protocol roadmap (ePBS, FOCIL,
PeerDAS, statelessness) is substantially a response to this**, which is itself an
acknowledgment that the concern is legitimate.

---

## §16. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **Fusaka** | **Activated 3 December 2025.** **PeerDAS** — validators sample blob data by column across 128 subnets rather than downloading every blob; gas limit raised to ~60M | Low |
| **Glamsterdam** | ⚠️ **Date genuinely unsettled** — ethereum.org's roadmap has listed **Q4 2026**; other coverage says H1 2026 or "second half of 2026"; a June 2026 report described it at the all-EIP devnet stage, "the final phase before public testnet." Headline EIPs: **EIP-7732 (ePBS)**, **EIP-7928 (Block-Level Access Lists)**, **EIP-7904 (gas repricing)**. Goals: parallel execution, in-protocol block building, higher L1 capacity. **Check Forkcast for status** | **High** |
| **Hegotá** | Named December 2025; targeted **2027**. **FOCIL** (Fork-Choice enforced Inclusion Lists) selected as the headline feature; **Verkle Trees** under discussion | **High** |
| **Pectra** | May 2025. **EIP-7702** (EOAs execute as smart contracts) and **EIP-7251** (validator max effective balance to 2048 ETH) | Low |
| **Gas environment** | ⚠️ **As of 5 May 2026, standard gas around 0.15 gwei, daily averages near 0.5 gwei through April** — basic transfers under a cent. **The 2021–2023 fee regime is not a safe default assumption** | Medium |
| **Solidity** | **0.8.36 (9 July 2026)** latest stable — included **two medium-severity security fixes**; 0.8.37 in nightly. Experimental **SSA-form code generator** (introduced 0.8.35) gaining stack-to-memory improvements | Medium |
| **Execution client share** | ⚠️ **Sources disagree by measurement method.** Ethernodes (peer-visible): **Geth ~41%, Nethermind ~32%, Reth ~15%, Besu ~7%, Erigon ~2%**. Chainstack: Geth 36%, Nethermind 23%, Reth 13.9%, Besu 11.9%, Erigon 4.5%. A 2026 EthStaker survey of its community: **Nethermind ~45%, Geth ~33%, Besu ~15%**. Geth is down from a historic ~84% | Medium |
| **Client incidents** | **2 September 2025: a critical issue took down most Reth nodes on mainnet** at block 23272427. Multi-client operators stayed up. **The case for diversity is empirical, not theoretical** | Low |
| **ZK in clients** | **Nethermind** building ZK proving into the production execution client (execution witness capture, stateless replay, minimal EVM binary complete); **ethrex** (LambdaClass, Rust) runs the same codebase as an L1 client *and* a multi-prover ZK rollup | Medium |
| **Hardhat 3** | Major rewrite: new **EDR** engine, **native Solidity tests**, multichain/OP Stack simulation, gas statistics, rebuilt config. Benchmarks put it **within ~2× of Foundry vs. Hardhat 2's 10–20× penalty**. Cross-tool interop: `foundry.toml` parsed by Hardhat, shared artifacts | Medium |
| **Loss categories (OWASP SC Top 10 2026, from 2025 data)** | **149 incidents, ~$1.42B total. Access control $953.2M · logic errors $63.8M · reentrancy $35.7M · flash loans $33.8M.** ⚠️ Access control leads by more than an order of magnitude | Medium |
| **The 2026 shift** | ⚠️ **Smart contract exploit losses fell ~89% YoY in Q1 2026 (DefiLlama) — and total losses stayed high.** ~$450M across 145 incidents in Q1, of which **phishing and social engineering were ~$306M (≈2/3)**. One January social-engineering attack drained **$282M with no code exploited**. Six audited protocols breached that quarter; **one had 18 prior audits** | **High** |
| **Threat actors** | **Chainalysis attributes ~76% of 2026 crypto hack losses to state-backed actors linked to Lazarus Group**; DPRK cumulative attributed theft exceeds $6B since 2017. Methods include multi-month social engineering and embedding operatives as IT workers | Medium |
| **Unverified contracts** | Chainalysis found **five protocols in six months where the exploited contract was the protocol's own and unverified**, ~$36.7M combined. Also notes **AI-assisted exploit development is likely accelerating** | Medium |
| **Audit costs** | ~**$3,000** for a simple contract to **$100,000+** for complex multi-contract systems. **Formal verification** (Certora Prover, Halmos) increasingly a standard offering rather than a premium add-on | Medium |

**Goes stale fastest:** Glamsterdam's date and scope; client share numbers; exploit
statistics; Solidity patch versions. **Essentially never stale:** §4 → `blockchain-smart-contract-development` (EVM model), §6.3 → `blockchain-smart-contract-development`
(design principles), §7.1 → `blockchain-smart-contract-development` (ERC-20 misbehaviours), §8.2 → `blockchain-smart-contract-development`–8.3 (oracles and flash loans),
§10.2 → `blockchain-security-testing-and-ops` (the vulnerability canon), §14 (anti-patterns).

---

## §17. The Canon

### 17.1 Primary documentation — read these directly
- **ethereum.org/developers** and the **Ethereum Yellow Paper** (formal EVM spec) and
  **execution-specs** / **consensus-specs** repos — the actual protocol.
- **EIPs.ethereum.org** — every standard, in its authoritative form. **Read the ERC you're
  implementing rather than a blog post about it.**
- **Solidity documentation** (`docs.soliditylang.org`) — including the security
  considerations page and the release blog for the security fixes in each version.
- **Foundry Book** (`getfoundry.sh`) and **Hardhat 3 docs** (`hardhat.org`).
- **OpenZeppelin Contracts** — read the source; it's the reference implementation of most
  standards and the comments are educational.
- **evm.codes** — an interactive opcode reference with gas costs. Indispensable.
- **L2Beat** — the honest L2 risk and stage assessment (§11.1 → `blockchain-protocol-layer`).
- **Forkcast** and the **Ethereum Foundation blog / Protocol Announcements** for upgrade
  status.

### 17.2 Security-specific
**OWASP Smart Contract Top 10** (§10.1 → `blockchain-security-testing-and-ops`'s source), **Smart Contract Weakness Classification
(SWC)**, **Trail of Bits' `building-secure-contracts`** (the best free security curriculum),
**Consensys Smart Contract Best Practices**, **Damn Vulnerable DeFi** and **Ethernaut**
(wargames — **do these; they teach the attacker's perspective faster than any reading**),
**Secureum** and **Cyfrin Updraft**, **rekt.news** (post-mortems — an education in what
actually goes wrong), **Immunefi**, and **DefiLlama's hacks database**.

### 17.3 Books and long-form
| Author | Work |
|---|---|
| **Andreas Antonopoulos & Gavin Wood** | ***Mastering Ethereum*** (free on GitHub) — dated on the roadmap, excellent on fundamentals |
| **Andreas Antonopoulos** | *Mastering Bitcoin* — the clearest explanation of the underlying mechanics |
| **Narayanan et al.** | *Bitcoin and Cryptocurrency Technologies* (Princeton, free) — the academic treatment |
| **Vitalik Buterin** | `vitalik.eth.limo` — the roadmap essays are the primary source on protocol direction |
| **Paradigm, a16z crypto, Flashbots research** | The research blogs where MEV and protocol design get worked out in public |

### 17.4 People and communities
**Ethereum Magicians** (`ethereum-magicians.org` — where EIPs get argued),
**Ethereum Research** (`ethresear.ch`), the **ACD call notes and recordings**,
**Flashbots** (MEV), **samczsun** (the best public incident write-ups in the field),
**Trail of Bits**, **OpenZeppelin**, **Certora**, **Dan Guido**, **Georgios Konstantopoulos**
(Paradigm — Reth, Foundry), **transmissions11**, and **Solidity's own forum and Twitter**
for compiler changes.

---

## §18. Quick Reference

### 18.1 Numbers
- **21,000 gas** base transaction; **4/16 gas** per zero/non-zero calldata byte.
- **Cold SLOAD ~2,100 · zero→nonzero SSTORE ~20,000 · nonzero→nonzero ~2,900.**
- **63/64 rule** on forwarded gas (EIP-150).
- Stack depth **1024**; word size **256 bits**.
- Ethereum finality: **2 epochs ≈ 13 minutes**.
- Validator: **32 ETH**; max effective balance **2048 ETH** post-EIP-7251.
- Optimistic rollup withdrawal: **~7 days**.
- Client-diversity thresholds: **>1/3 breaks finality, >2/3 can finalize a bad chain.**
- Access control ≈ **$953M** of 2025's ~$1.42B in losses.

### 18.2 Pre-deployment checklist
- [ ] Exact solc version pinned; optimizer settings recorded; build reproducible
- [ ] Every privileged function has the right modifier, on **every** path
- [ ] Initializers protected; implementation contracts have `_disableInitializers()`
- [ ] Storage layout append-only (or ERC-7201) if upgradeable
- [ ] Checks-Effects-Interactions everywhere; reentrancy guards where needed
- [ ] All external calls' return values checked; `SafeERC20` for tokens
- [ ] Oracles: no spot prices, staleness checked, sequencer uptime checked on L2
- [ ] Every loop bounded; pull-over-push for payments
- [ ] Slippage bounds and deadlines on anything swapping
- [ ] Fuzz + **invariant** tests written and passing; Slither clean or triaged
- [ ] Fork tests against real mainnet state and dependencies
- [ ] Audited; findings fixed **and root-caused**; re-audited after changes
- [ ] Ownership on a multisig + timelock, never an EOA
- [ ] Source verified on the explorer
- [ ] Monitoring, pause procedure, and incident runbook live **before** launch
- [ ] Bug bounty posted

### 18.3 Triage
| Symptom | First look |
|---|---|
| Transaction reverts, no reason | `debug_traceTransaction` on an archive node; check custom errors |
| "Out of gas" on a working function | Unbounded loop over a grown array (§4.2 → `blockchain-smart-contract-development`) |
| Works on mainnet, fails on another EVM chain | Different gas schedule/opcodes (§4.3 → `blockchain-smart-contract-development`) |
| Integration breaks on one specific token | Non-standard ERC-20 (§7.1 → `blockchain-smart-contract-development`) |
| Upgrade corrupted state | Storage layout collision (§6.1 → `blockchain-smart-contract-development`) |
| Users report losing funds without a contract bug | Phishing / signature approval — check what they signed (§10.1 → `blockchain-security-testing-and-ops`, §13.4 → `blockchain-security-testing-and-ops`) |
| Indexer data is wrong | Reorg handling (§13.4 → `blockchain-security-testing-and-ops`) |
| Validator missing attestations at a fork | Client not updated for the fork (§3.1 → `blockchain-protocol-layer`) |
| Price feed returns something absurd | Staleness, or manipulation of a spot source (§8.2 → `blockchain-smart-contract-development`) |

---

## §19. Sources and Method

**Method.** Narrative (not systematic) review. The durable material — §1.1 → `blockchain-protocol-layer`, §4 → `blockchain-smart-contract-development` (EVM model),
§6.3 → `blockchain-smart-contract-development` (design principles), §7.1 → `blockchain-smart-contract-development`, §8.2 → `blockchain-smart-contract-development`–8.3, §10.2 → `blockchain-security-testing-and-ops` (the vulnerability canon), §12 → `blockchain-protocol-layer`, §14 — rests
on protocol specifications, the standard security references in §17, and vulnerability
classes documented consistently across years of post-mortems. Every **time-sensitive**
claim (upgrade schedules, client shares, compiler versions, tooling benchmarks, exploit
statistics) was verified against a primary or near-primary source in **August 2026** and is
flagged in §16 with a decay-risk rating. Where sources conflict — notably the Glamsterdam
date and the client-share numbers — **I have reported the conflict rather than picking one**.

**Search log** (August 2026): Ethereum roadmap, Fusaka, and Glamsterdam status · Solidity
versions and the Foundry/Hardhat toolchain · smart contract exploit statistics and audit
landscape · execution client diversity and the L2/rollup client layer.

**Primary and near-primary sources consulted (selected):**
- **ethereum.org** — the roadmap, Fusaka and Glamsterdam pages, client diversity docs,
  nodes-and-clients, and the "Building on Ethereum in 2026" post (gas environment)
- **Solidity** — the official releases blog (0.8.36, July 2026) and Etherscan's compiler
  version list for nightly state
- **OWASP Smart Contract Top 10 (2026)** — the loss-category breakdown, built from 2025
  incident data via SolidityScan's Web3HackHub
- **Chainalysis** — the unverified-contracts analysis and threat-actor attribution;
  **Hacken** quarterly security reporting; **DefiLlama** hacks database for the YoY change
- **Ethernodes**, **Chainstack**, **clientdiversity.org**, and **EthStaker's 2026 staking
  landscape analysis** for client share (all four disagree; all four are cited)
- **Stakely**'s post-mortem of the September 2025 Reth incident
- **Nomic Foundation / Hardhat 3** documentation and independent Foundry-vs-Hardhat
  benchmark write-ups; **Foundry**'s configuration reference
- **The Block**, **CoinDesk**, **Decrypt**, **Everstake**, and **Chainstack** on upgrade
  naming, scope, and infrastructure implications

**Confidence statement.** **High confidence** in §1 → `blockchain-protocol-layer`, §4–§8 → `blockchain-smart-contract-development`, §10.2 → `blockchain-security-testing-and-ops`, §12 → `blockchain-protocol-layer`, §13 → `blockchain-security-testing-and-ops`, §14 and §18 —
these rest on protocol specifications, official documentation, and vulnerability classes
documented across many years of incidents. **High confidence** in the Solidity version
details and in Fusaka's activation date, both from official sources. **Moderate confidence,
and explicitly conflicted, on the Glamsterdam timeline** (§3.2 → `blockchain-protocol-layer`, §16): official Ethereum
material and secondary coverage give different dates ranging from H1 2026 to Q4 2026,
developers consistently caveat that it depends on testnet validation, and I have presented
that spread rather than a single date. **Moderate confidence on client-share figures**
(§1.3 → `blockchain-protocol-layer`, §16): four sources give materially different numbers because they measure different
populations, and I have reported all four rather than averaging them. **Moderate confidence
on the exploit statistics** (§10.1 → `blockchain-security-testing-and-ops`): these come from security firms and analytics platforms
with differing methodologies and incentives, aggregate loss figures for a given period vary
substantially between trackers, and attribution to specific threat actors is inherently
uncertain — **the ordering of loss categories is well-corroborated across sources and is
the part I would rely on; the precise dollar figures are not.** Tooling benchmark claims in
§9.1 → `blockchain-security-testing-and-ops` come from third-party comparisons rather than a standing neutral benchmark, and
Foundry maintains its own benchmark page while Hardhat does not, which is itself a source
of asymmetry. **Nothing in this document is investment advice**, and no claim here should
be read as an assessment of any asset's value.

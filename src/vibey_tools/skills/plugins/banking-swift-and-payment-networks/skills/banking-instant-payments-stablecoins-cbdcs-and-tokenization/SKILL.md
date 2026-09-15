---
name: banking-instant-payments-stablecoins-cbdcs-and-tokenization
description: "Use for the modern rails and the digital-money debate: instant payment systems including FedNow, UPI, Pix and SEPA Instant and why domestic instant payments spread faster than cross-border ones, stablecoins and their reserve, redemption and run-risk questions, retail and wholesale CBDCs and the actual state of deployment, and tokenized deposits and wholesale settlement experiments."
---

# Banking and Payments: Instant Payment Systems, Stablecoins, CBDCs, and Tokenized Deposits and Wholesale Settlement

> **Part 4 of 6** of the *Banking, SWIFT and Payment Networks* reference (plugin `banking-swift-and-payment-networks`), covering §17–§20. Sibling skills: `banking-payments-banks-reserves-and-settlement` (§0–§5), `banking-correspondent-swift-iso20022-and-governance` (§6–§11), `banking-ripple-xrp-ledger-and-honest-assessment` (§12–§16), `banking-compliance-security-and-remittance-costs` (§21–§23), `banking-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The plumbing is stable and slow-moving. Two areas moved. See §24 → `banking-reference` for the ISO 20022 migration, and what is actually settling on blockchain rails.

> **⚠️ NOT FINANCIAL ADVICE. Nothing here is a recommendation to buy, sell or hold any
> asset, and §12–§16 → `banking-ripple-xrp-ledger-and-honest-assessment` in particular describe a domain saturated with promotional material
> from parties holding positions.** ⚠️ **This file is about infrastructure — how payments
> work — not about what anything is worth.**
>
> **Complements a cryptography reference (message authentication, settlement finality
> guarantees) and an investment reference (which covers markets rather than plumbing).**
>
> **⚠️ GOTCHA** boxes mark where the popular description of a system is simply wrong — and
> this domain has an unusual number of them.
>
> **The three ideas that organize this document:**
> 1. **⚠️ MESSAGING IS NOT MONEY MOVEMENT** (§7 → `banking-correspondent-swift-iso20022-and-governance`). **SWIFT does not transfer funds. It
>    carries instructions. Almost every confused claim about SWIFT — including "SWIFT is
>    slow" and "crypto will replace SWIFT" — collapses once this is clear.**
> 2. **⚠️ SETTLEMENT IS THE HARD PART, NOT TRANSMISSION** (§5 → `banking-payments-banks-reserves-and-settlement`, §6 → `banking-correspondent-swift-iso20022-and-governance`). **Getting a message
>    across the world is trivial and has been for decades. Extinguishing an obligation with
>    finality, across legal jurisdictions, with credit and liquidity risk managed, is what
>    the infrastructure is actually for.**
> 3. **⚠️ THE CORRESPONDENT MODEL IS THE THING BEING DISRUPTED** (§6 → `banking-correspondent-swift-iso20022-and-governance`, §24.2 → `banking-reference`). **Not SWIFT,
>    not banks — the chain of nostro/vostro relationships with pre-funded accounts is where
>    the cost, delay and opacity live, and every serious alternative attacks that.**

---

## §17. Instant Payment Systems

**⚠️ The genuinely transformative development in payments, and it is domestic rather than
crypto.**
⚠️ **UK Faster Payments (2008) was early; ⚠️ India's UPI is the scale case, having
transformed retail payments and reaching extraordinary transaction volumes; ⚠️ Brazil's Pix,
launched by the central bank in 2020, achieved adoption speed that surprised almost
everyone; ⚠️ SEPA Instant in Europe, now subject to a regulation requiring euro banks to
offer it; ⚠️ and FedNow in the US, launched 2023 and adopting more slowly.**
**⚠️ The common features**: ⚠️ **24/7/365, near-instant, irrevocable, and cheap or free at
the point of use.**
> **⚠️ GOTCHA — irrevocability plus instant speed creates a new fraud problem.** ⚠️ **AUTHORIZED
> PUSH PAYMENT fraud — tricking someone into sending money themselves — has grown sharply
> where instant rails are widespread, and it defeats traditional fraud controls because the
> payment is genuinely authorized.** **⚠️ The UK's mandatory reimbursement regime is one
> policy response, and the incentive debate around it is live.**

**⚠️ Cross-border interlinking** of instant systems (Project Nexus, and bilateral links like
Singapore-Thailand) ⚠️ **is arguably the most credible path to fast cheap cross-border
payments, and it is unglamorous.**

---

## §18. ⚠️ Stablecoins

```
⚠️ WHAT THEY ARE  ⚠️ tokens intended to hold a fixed value,
   usually one dollar
⚠️ ⚠️ THE TYPES, in descending order of how well they have worked
   ⚠️ FIAT-BACKED  ⚠️ reserves in cash and short Treasuries.
      ⚠️ THE ONLY MODEL THAT HAS WORKED AT SCALE. The questions
      are reserve QUALITY, attestation versus audit, and
      redemption rights
   ⚠️ CRYPTO-COLLATERALIZED  overcollateralized, capital-heavy
   ⚠️ ⚠️ ALGORITHMIC  ⚠️ repeatedly failed. ⚠️ Terra/UST's
      collapse in 2022 destroyed tens of billions and is the
      reference case
⚠️ ⚠️ WHAT THEY ACTUALLY ARE, in §2's terms  ⚠️ a claim on an
   issuer — ⚠️ closer to a money market fund or e-money than to
   a bank deposit, and WITHOUT deposit insurance
⚠️ ⚠️ THE DEPEG RISK IS REAL AND HAS MATERIALIZED  ⚠️ USDC broke
   its peg in March 2023 when reserves were held at a bank that
   failed — ⚠️ demonstrating that the reserve is only as safe as
   where it sits
⚠️ WHY INSTITUTIONS ACTUALLY LIKE THEM  ⚠️ 24/7 settlement,
   programmability, no pre-funding across correspondents (§6),
   and ⚠️ NO PRICE VOLATILITY — which is the decisive advantage
   over a volatile bridge asset (§16, §24.2)
⚠️ REGULATION  ⚠️ MiCA in the EU and the US GENIUS Act framework
   have moved this from unregulated to regulated, which is what
   made institutional adoption possible
⚠️ ⚠️ THE SYSTEMIC QUESTIONS  ⚠️ reserve runs · the effect of
   large holdings on Treasury markets · monetary sovereignty in
   dollarizing economies · and whether this is narrow banking
   reinvented without the regulation that came with it
```

---

## §19. CBDCs

**⚠️ Central bank digital currency** — ⚠️ **central bank money in digital form, and the
retail/wholesale distinction is the most important one.**
**⚠️ WHOLESALE CBDC** is the less controversial and arguably more useful: ⚠️ **tokenized
central bank reserves for interbank and securities settlement, which is an incremental
improvement to existing plumbing.**
**⚠️ RETAIL CBDC** raises genuinely hard questions: ⚠️ **DISINTERMEDIATION (⚠️ if the public
can hold central bank money directly, what happens to bank deposits and hence to lending,
§2 → `banking-payments-banks-reserves-and-settlement`?), privacy and surveillance, offline capability, and programmability — ⚠️ which is
simultaneously the most-touted feature and the most objected-to.**
**⚠️ The state of play varies enormously**: ⚠️ **China's e-CNY is the largest pilot; the ECB
has a digital euro project; ⚠️ several countries have launched and seen low uptake; and the
US has moved against a retail CBDC.**
**⚠️ The honest question** is what problem a retail CBDC solves that instant payments (§17)
and regulated e-money do not — ⚠️ **and the answers offered are usually about resilience,
sovereignty and inclusion rather than about user experience.**

---

## §20. Tokenized Deposits and Wholesale Settlement

**⚠️ Tokenized deposits** are commercial bank money on a distributed ledger — ⚠️ **and the
distinction from stablecoins matters: a tokenized deposit remains a bank liability inside
the regulated perimeter with deposit insurance, while a stablecoin is a claim on an
issuer** (§18).
**⚠️ Live examples** include ⚠️ **JPMorgan's Kinexys (formerly Onyx) and JPM Coin for
intra-institution settlement.**
**⚠️ The BIS "unified ledger" concept** and Project Agorá propose ⚠️ **central bank money,
commercial bank money and tokenized assets on shared programmable infrastructure —
essentially arguing that the value is in ATOMIC SETTLEMENT and composability, not in
disintermediation.**
**⚠️ DVP and PVP on-chain** (§5 → `banking-payments-banks-reserves-and-settlement`) — ⚠️ **atomic settlement genuinely eliminates Herstatt-type
risk, which is the strongest technical argument in this whole area.**
**⚠️ The unglamorous conclusion much of the industry has reached**: ⚠️ **the useful part of
the technology is atomic, programmable settlement — not disintermediating banks.**

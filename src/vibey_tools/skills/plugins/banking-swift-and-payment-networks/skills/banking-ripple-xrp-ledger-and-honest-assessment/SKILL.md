---
name: banking-ripple-xrp-ledger-and-honest-assessment
description: "Use when the question involves Ripple or XRP, where conflation is the norm: the three distinct things — the company, the asset and the ledger — kept apart, XRP Ledger mechanics including the consensus protocol and the built-in decentralized exchange, Ripple's actual products and how many of them use XRP, the legal status after the SEC litigation, and an honest assessment of what has and has not been adopted."
---

# Banking and Payments: Ripple Versus XRP Versus the XRP Ledger, XRP Ledger Mechanics, Ripple's Products, Legal Status, and an Honest Assessment

> **Part 3 of 6** of the *Banking, SWIFT and Payment Networks* reference (plugin `banking-swift-and-payment-networks`), covering §12–§16. Sibling skills: `banking-payments-banks-reserves-and-settlement` (§0–§5), `banking-correspondent-swift-iso20022-and-governance` (§6–§11), `banking-instant-payments-stablecoins-cbdcs-and-tokenization` (§17–§20), `banking-compliance-security-and-remittance-costs` (§21–§23), `banking-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The plumbing is stable and slow-moving. Two areas moved. See §24 → `banking-reference` for the ISO 20022 migration, and what is actually settling on blockchain rails.

> **⚠️ NOT FINANCIAL ADVICE. Nothing here is a recommendation to buy, sell or hold any
> asset, and §12–§16 in particular describe a domain saturated with promotional material
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

## §12. ⚠️ Ripple versus XRP versus the XRP Ledger

> **⚠️ Three different things, constantly conflated — including deliberately. Getting this
> straight is most of what it takes to read this area critically.**
```
⚠️ ⚠️ RIPPLE  ⚠️ a PRIVATE COMPANY (Ripple Labs). Sells payment
   software and services to institutions. ⚠️ Holds a large XRP
   position
⚠️ ⚠️ XRP  ⚠️ a CRYPTOCURRENCY. All 100 billion units were
   created at launch — ⚠️ NO MINING, no issuance schedule.
   ⚠️ A large share was allocated to Ripple the company, much of
   it placed in escrow with scheduled releases
⚠️ ⚠️ THE XRP LEDGER (XRPL)  ⚠️ an open-source, permissionless
   blockchain, launched 2012. ⚠️ Ripple is a major contributor
   but does not own it
⚠️ ⚠️ WHY THE DISTINCTION IS LOAD-BEARING
   ⚠️ A bank can use Ripple's SOFTWARE without touching XRP
   ⚠️ A payment can settle on the XRPL using a STABLECOIN
      without XRP doing anything but paying a trivial fee
   ⚠️ ⚠️ THEREFORE "BANK ADOPTS RIPPLE" TELLS YOU ALMOST NOTHING
      ABOUT XRP USE — ⚠️ and headlines routinely elide this
      (§16, §24.2)
⚠️ ⚠️ THE QUESTION TO ASK OF ANY ADOPTION CLAIM: ⚠️ is the token
   in the transaction path, or is this a company using a
   database?
```

---

## §13. XRP Ledger Mechanics

**⚠️ Consensus, not proof of work**: ⚠️ **the XRPL uses a federated agreement protocol in
which each node has a Unique Node List of validators it trusts.** ⚠️ **Fast and
energy-cheap; ⚠️ the trade is that trust is in the validator set rather than in
economically-costly work, and UNL overlap is required for safety.**
**⚠️ Performance**: ⚠️ **settlement in a few seconds, fees of a fraction of a cent, and
throughput well above Bitcoin or Ethereum L1.**
**⚠️ Native features**: ⚠️ **a built-in decentralized exchange and path-finding, trust lines
for issued assets, and destination tags — the ledger was designed for payments rather than
for general computation.**
**⚠️ Fees are BURNED rather than paid to validators**, ⚠️ **and a small XRP reserve is
required per account, which is the anti-spam mechanism.**
> **⚠️ GOTCHA — validator decentralization is the standing critique.** ⚠️ **Ripple publishes
> a default UNL, and while anyone may run a validator and choose their own list, the
> practical concentration of trust is a legitimate question that supporters and critics
> answer differently.**

**⚠️ And note §5 → `banking-payments-banks-reserves-and-settlement`'s point**: ⚠️ **fast confirmation is not the same as legal settlement
finality, and for regulated institutions the legal question is the binding one.**

---

## §14. Ripple's Products

**⚠️ RippleNet / Ripple Payments** — ⚠️ **the institutional payments platform. ⚠️ Membership
does NOT imply XRP usage** (§12).
**⚠️ ODL (On-Demand Liquidity)**, formerly xRapid — ⚠️ **the actual XRP use case, and the
argument is precise: instead of pre-funding a nostro account (§6 → `banking-correspondent-swift-iso20022-and-governance`), convert source currency
to XRP, transmit, and convert to destination currency, holding the bridge asset for
seconds.** ⚠️ **If it works, it frees the trapped capital that is correspondent banking's
biggest cost.**
**⚠️ RLUSD** — ⚠️ **Ripple's dollar stablecoin, launched 2024, issued on the XRPL and
Ethereum.** ⚠️ **Note the strategic significance: it is an alternative settlement asset that
does NOT require XRP** (§24.2 → `banking-reference`).
**⚠️ Custody, and a national trust bank charter** — ⚠️ **the OCC conditionally approved
Ripple National Trust Bank in December 2025 per reporting, which would hold RLUSD reserves
and offer institutional custody.** ⚠️ **A national trust bank cannot take deposits or
lend.**
**⚠️ The direction of travel is toward being a regulated financial infrastructure company**
rather than a crypto company.

---

## §15. Legal Status

**⚠️ The SEC sued Ripple in December 2020** alleging XRP sales were unregistered securities
offerings.
**⚠️ The July 2023 ruling was split** — ⚠️ **and the split is the interesting part:
institutional sales to sophisticated buyers were held to be investment contracts, while
PROGRAMMATIC sales on exchanges were not, on the reasoning that blind bid-ask buyers had no
expectation derived from Ripple's efforts specifically.**
**⚠️ The reasoning was criticized from multiple directions** and ⚠️ **is not binding
precedent beyond the case.**
**⚠️ The litigation concluded** with penalties and the appeals resolved, ⚠️ **and the broader
US regulatory posture toward digital assets has shifted since.**
**⚠️ Elsewhere**: ⚠️ **MiCA in the EU, and various national regimes, treat these questions
differently — ⚠️ and "regulatory clarity" claims should always be read as jurisdiction-
specific.**
**⚠️ This is a factual summary, not legal advice, and the area moves.**

---

## §16. ⚠️ An Honest Assessment

> **⚠️ Read this before reading anything promotional, from either direction.**
```
⚠️ ⚠️ WHAT IS GENUINELY TRUE
   ⚠️ The XRPL works. Seconds, trivial fees, years of uptime
   ⚠️ ⚠️ THE PRE-FUNDING PROBLEM IS REAL (§6) and the ODL
      argument against it is intellectually sound
   ⚠️ Ripple is a real company with real institutional customers
      and real revenue
⚠️ ⚠️ WHAT IS ROUTINELY OVERSTATED
   ⚠️ ⚠️ "REPLACING SWIFT" — ⚠️ a category error (§7). SWIFT is
      messaging; Ripple is settlement. ⚠️ The thing being
      displaced is CORRESPONDENT BANKING (§6)
   ⚠️ ⚠️ PARTNER COUNTS as evidence of XRP demand (§12)
   ⚠️ Pilots and MOUs presented as production deployments
⚠️ ⚠️ THE STRUCTURAL CRITIQUES THAT DESERVE WEIGHT
   ⚠️ 1. ⚠️ VOLATILITY. ⚠️ A bridge asset held for seconds still
      needs deep two-sided liquidity in BOTH corridors, and the
      exchange spread and slippage are the real cost — ⚠️ which
      is precisely why institutions have moved toward
      stablecoins (§24.2)
   ⚠️ 2. ⚠️ THE COMPANY AND THE TOKEN CAN DIVERGE. ⚠️ Ripple can
      succeed commercially while XRP demand stays flat, because
      its products increasingly do not require XRP (§14, §24.2)
   ⚠️ 3. ⚠️ CONCENTRATION of supply and the escrow overhang
   ⚠️ 4. Validator centralization (§13)
   ⚠️ 5. ⚠️ THE INCUMBENTS RESPONDED — gpi (§9), instant payment
      systems (§17), and SWIFT's own ledger work (§24.2)
⚠️ ⚠️ AND THE INFORMATION-QUALITY WARNING  ⚠️ this topic has an
   unusually large volume of coverage produced by people holding
   the asset. ⚠️ Treat unsourced volume and adoption figures
   sceptically, and check whether a claim is about RIPPLE, XRP,
   or the XRPL every single time
```

---

# PART IV — THE WIDER LANDSCAPE

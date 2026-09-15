---
name: banking-compliance-security-and-remittance-costs
description: "Use for the constraint layer that shapes what payment systems can do: compliance including KYC, AML, sanctions screening and the de-risking that cuts off whole corridors, security covering the SWIFT-related heists, endpoint compromise and the CSP controls that followed, and the real costs and economics of remittances and where the fees actually go."
---

# Banking and Payments: Compliance, Security, and Costs and Remittances

> **Part 5 of 6** of the *Banking, SWIFT and Payment Networks* reference (plugin `banking-swift-and-payment-networks`), covering §21–§23. Sibling skills: `banking-payments-banks-reserves-and-settlement` (§0–§5), `banking-correspondent-swift-iso20022-and-governance` (§6–§11), `banking-ripple-xrp-ledger-and-honest-assessment` (§12–§16), `banking-instant-payments-stablecoins-cbdcs-and-tokenization` (§17–§20), `banking-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §21. ⚠️ Compliance

```
⚠️ THE REGIME  ⚠️ KYC and CDD at onboarding · ⚠️ SANCTIONS
   SCREENING against OFAC, EU, UN and national lists ·
   transaction monitoring · SAR/STR filing · the FATF
   recommendations as the international standard ·
   ⚠️ the TRAVEL RULE requiring originator and beneficiary
   information to accompany transfers (⚠️ and extended to
   virtual assets, which is a live implementation problem)
⚠️ ⚠️ THE FALSE POSITIVE PROBLEM IS THE OPERATIONAL REALITY.
   ⚠️ Name-matching against sanctions lists generates
   overwhelmingly false alerts, each requiring human review.
   ⚠️ THIS IS A LARGE SHARE OF WHY CROSS-BORDER PAYMENTS ARE
   SLOW AND EXPENSIVE — ⚠️ and it is exactly what ISO 20022's
   structured party data is meant to improve (§8, §24.1)
⚠️ ⚠️ DE-RISKING (§6) IS THE PERVERSE OUTCOME  ⚠️ when the
   expected penalty for a compliance failure exceeds the profit
   from a whole market, the rational bank exits the market.
   ⚠️ The aggregate result is financial exclusion that no
   regulator intended
⚠️ THE TENSION WORTH NAMING  ⚠️ every improvement in payment
   speed reduces the window for intervention, and every
   improvement in privacy reduces screening effectiveness.
   ⚠️ These are genuine trade-offs, not solvable by better
   engineering
```

---

## §22. ⚠️ Security

**⚠️ THE BANGLADESH BANK HEIST (2016)** is the case study worth knowing in detail.
⚠️ **Attackers compromised the bank's own systems, then issued FRAUDULENT BUT PERFECTLY
VALID SWIFT messages instructing transfers from its account at the New York Fed —
attempting roughly a billion dollars and succeeding with about $81 million, much of it
routed through Philippine casinos.**
> **⚠️ GOTCHA — SWIFT was not breached, and this is the point.** ⚠️ **The attack exploited
> the endpoint, and the network faithfully carried authenticated instructions from a
> compromised member.** **⚠️ A trusted-network model is only as strong as its weakest
> participant — the same structural lesson as the peripherals reference's BadUSB and the
> firmware reference's supply chain.**

**⚠️ The response** was SWIFT's Customer Security Programme, ⚠️ **mandating baseline controls
with attestation and peer review — an interesting governance model where the network
enforces security standards on its members.**
**⚠️ Other threat classes**: ⚠️ **business email compromise (⚠️ the highest-loss fraud
category by value in many jurisdictions, and entirely social), card fraud and the shift to
CNP, ATM jackpotting, insider fraud, and authorized push payment fraud** (§17 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`).

---

## §23. ⚠️ Costs and Remittances

**⚠️ The remittance problem is a genuine humanitarian issue**, ⚠️ **not merely a technical
one.**
**⚠️ Global remittance flows to low- and middle-income countries run to hundreds of billions
of dollars annually and exceed foreign direct investment for many countries.**
**⚠️ The average cost has remained stubbornly high** — ⚠️ **the UN Sustainable Development
Goal target is under 3%, and the global average has persistently sat above it, with some
corridors far worse.**
**⚠️ Where the cost actually is**: ⚠️ **FX spread (⚠️ frequently larger than the disclosed
fee), correspondent chain fees (§6 → `banking-correspondent-swift-iso20022-and-governance`), cash-out network costs, compliance (§21), and
last-mile distribution in cash economies.**
**⚠️ Why technology has helped less than promised**: ⚠️ **the expensive parts are the
regulated on-ramp and the physical off-ramp, not the transmission.** ⚠️ **A settlement
system that is free does not solve getting cash into a village.**
**⚠️ What has actually reduced costs**: ⚠️ **mobile money (⚠️ M-Pesa and successors), domestic
instant systems (§17 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`), fintech competition on FX spread, and regulatory transparency
requirements.**

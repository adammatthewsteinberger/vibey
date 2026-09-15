---
name: banking-payments-banks-reserves-and-settlement
description: "Use for the foundations that most payment confusion traces back to: what a payment actually is as a transfer of claims, what a bank is and how deposits are created rather than lent out, central banks and reserve accounts as the ultimate settlement layer, the payment system taxonomy of RTGS, deferred net settlement, card and instant rails, and clearing, netting and Herstatt settlement risk. Includes the router for the whole banking and payments reference."
---

# Banking and Payments: What a Payment Actually Is, What a Bank Is, Central Banks and Reserves, the Payment System Taxonomy, and Clearing, Netting and Settlement Risk

> **Part 1 of 6** of the *Banking, SWIFT and Payment Networks* reference (plugin `banking-swift-and-payment-networks`), covering §0–§5. Sibling skills: `banking-correspondent-swift-iso20022-and-governance` (§6–§11), `banking-ripple-xrp-ledger-and-honest-assessment` (§12–§16), `banking-instant-payments-stablecoins-cbdcs-and-tokenization` (§17–§20), `banking-compliance-security-and-remittance-costs` (§21–§23), `banking-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ SETTLEMENT IS THE HARD PART, NOT TRANSMISSION** (§5, §6 → `banking-correspondent-swift-iso20022-and-governance`). **Getting a message
>    across the world is trivial and has been for decades. Extinguishing an obligation with
>    finality, across legal jurisdictions, with credit and liquidity risk managed, is what
>    the infrastructure is actually for.**
> 3. **⚠️ THE CORRESPONDENT MODEL IS THE THING BEING DISRUPTED** (§6 → `banking-correspondent-swift-iso20022-and-governance`, §24.2 → `banking-reference`). **Not SWIFT,
>    not banks — the chain of nostro/vostro relationships with pre-funded accounts is where
>    the cost, delay and opacity live, and every serious alternative attacks that.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| What a payment is | §1 |
| **⚠️ What a bank is** | **§2** |
| Central banks and reserves | §3 |
| Payment system types | §4 |
| **⚠️ Clearing and settlement** | **§5** |
| **⚠️ Correspondent banking** | **§6 → `banking-correspondent-swift-iso20022-and-governance`** |
| **⚠️ What SWIFT is** | **§7 → `banking-correspondent-swift-iso20022-and-governance`** |
| **⚠️ Message formats** | **§8 → `banking-correspondent-swift-iso20022-and-governance`** |
| gpi and tracking | §9 → `banking-correspondent-swift-iso20022-and-governance` |
| **⚠️ Governance and sanctions** | **§10 → `banking-correspondent-swift-iso20022-and-governance`** |
| Alternatives to SWIFT | §11 → `banking-correspondent-swift-iso20022-and-governance` |
| **⚠️ Ripple vs XRP vs XRPL** | **§12 → `banking-ripple-xrp-ledger-and-honest-assessment`** |
| XRP Ledger mechanics | §13 → `banking-ripple-xrp-ledger-and-honest-assessment` |
| Ripple's products | §14 → `banking-ripple-xrp-ledger-and-honest-assessment` |
| Legal status | §15 → `banking-ripple-xrp-ledger-and-honest-assessment` |
| **⚠️ Honest assessment** | **§16 → `banking-ripple-xrp-ledger-and-honest-assessment`** |
| Instant payment systems | §17 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization` |
| **⚠️ Stablecoins** | **§18 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`** |
| CBDCs | §19 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization` |
| Tokenized settlement | §20 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization` |
| **⚠️ Compliance** | **§21 → `banking-compliance-security-and-remittance-costs`** |
| **⚠️ Security** | **§22 → `banking-compliance-security-and-remittance-costs`** |
| **⚠️ Costs and remittances** | **§23 → `banking-compliance-security-and-remittance-costs`** |
| **What's live** | **§24 → `banking-reference`** |
| Misconceptions, numbers | §25–§26 → `banking-reference` |
| Sources, quick ref, method | §27–§29 → `banking-reference` |

---

## §1. What a Payment Actually Is

```
⚠️ ⚠️ A PAYMENT IS THE DISCHARGE OF AN OBLIGATION, not the
   movement of an object. ⚠️ No thing travels. ⚠️ What happens is
   that ledger entries change and a legal obligation is
   extinguished
⚠️ THE FOUR THINGS THAT MUST HAPPEN
   ⚠️ 1. INSTRUCTION  ⚠️ someone says what should happen (§7)
   ⚠️ 2. CLEARING  reconciling and calculating what is owed
   ⚠️ 3. ⚠️ SETTLEMENT  ⚠️ the actual transfer of value between
      the parties' accounts at a common institution
   ⚠️ 4. ⚠️ FINALITY  ⚠️ the point after which it CANNOT be
      reversed. ⚠️ This is a LEGAL property, not a technical one,
      and it is the property that matters most
⚠️ ⚠️ SETTLEMENT REQUIRES A COMMON POINT. ⚠️ Two banks settle at
   the central bank; two people settle at their bank; two
   countries have no common central bank — ⚠️ WHICH IS THE
   ENTIRE PROBLEM OF CROSS-BORDER PAYMENTS (§6)
⚠️ THE RISKS BEING MANAGED  ⚠️ credit risk · liquidity risk ·
   ⚠️ SETTLEMENT RISK (⚠️ you paid, they didn't — see Herstatt,
   §5) · operational · legal · systemic
```

---

# PART I — BANKING FUNDAMENTALS

## §2. ⚠️ What a Bank Is

```
⚠️ THE BALANCE SHEET  ⚠️ ASSETS are loans and securities and
   reserves; ⚠️ LIABILITIES are DEPOSITS. ⚠️ Your deposit is the
   bank's debt to you — you are an unsecured creditor
⚠️ ⚠️ BANKS CREATE MONEY BY LENDING. ⚠️ The textbook
   "money multiplier" story — deposits come in, a fraction is
   lent out — is BACKWARDS as a description of how it works.
   ⚠️ A bank makes a loan by CREATING a matching deposit; both
   sides of the balance sheet expand simultaneously
   ⚠️ The Bank of England's 2014 bulletin says this explicitly,
   which is worth knowing because the textbook version persists
   ⚠️ THE CONSTRAINT is not reserves but CAPITAL, profitability,
   and regulation — not a fixed multiplier
⚠️ MATURITY TRANSFORMATION  ⚠️ borrow short (deposits, payable on
   demand), lend long. ⚠️ Profitable and INHERENTLY FRAGILE —
   which is what a bank run is
⚠️ REGULATION  ⚠️ Basel capital ratios · LCR and NSFR liquidity
   rules · deposit insurance (⚠️ which exists to stop runs by
   making them pointless) · resolution regimes
⚠️ ⚠️ TYPES OF MONEY, and the distinction matters
   ⚠️ CENTRAL BANK MONEY  reserves and cash. ⚠️ Risk-free
   ⚠️ COMMERCIAL BANK MONEY  ⚠️ your deposit. A claim on a bank
   ⚠️ E-money and stablecoins  ⚠️ a claim on someone else again
   (§18)
```

---

## §3. Central Banks and Reserves

**⚠️ Reserve accounts** are the settlement asset for the banking system — ⚠️ **banks hold
accounts at the central bank, and interbank settlement is a transfer between those
accounts.**
**⚠️ This is why the central bank is the apex of the payment system**: ⚠️ **it is the common
point (§1) at which everyone can settle without credit risk.**
**⚠️ Monetary policy operates through this plumbing**: ⚠️ **the policy rate, standing
facilities, open market operations, and — in a floor system — interest on reserves.**
**⚠️ Intraday liquidity** is the underappreciated part: ⚠️ **RTGS systems (§4) require banks
to have funds available moment by moment, and central banks provide intraday credit,
usually collateralized, to keep payments flowing.**
**⚠️ Lender of last resort** and the Bagehot formulation — ⚠️ **lend freely, against good
collateral, at a penalty rate — remains the reference framing for crisis intervention.**

---

## §4. The Payment System Taxonomy

```
⚠️ ⚠️ RTGS (Real-Time Gross Settlement)  ⚠️ each payment settled
   INDIVIDUALLY and IMMEDIATELY in central bank money.
   ⚠️ No settlement risk; ⚠️ HIGH LIQUIDITY DEMAND, because you
   need the full amount at the moment of payment
   ⚠️ Fedwire, TARGET2/T2, CHAPS
⚠️ ⚠️ DEFERRED NET SETTLEMENT  ⚠️ obligations accumulate and are
   NETTED, settling once or a few times a day.
   ⚠️ Hugely liquidity-efficient; ⚠️ carries settlement risk
   between netting cycles
   ⚠️ ACH, BACS, most retail systems
⚠️ ⚠️ HYBRID  ⚠️ most modern large-value systems, with liquidity-
   saving mechanisms that offset queued payments against each
   other while retaining gross finality. ⚠️ CHIPS is the classic
⚠️ INSTANT / FAST PAYMENT  ⚠️ 24/7, near-real-time, retail-scale,
   with finality in seconds (§17)
⚠️ CARD NETWORKS  ⚠️ a DIFFERENT ANIMAL — authorization is
   near-instant, ⚠️ but clearing and settlement happen later,
   which is why a "pending" charge can vanish
⚠️ SECURITIES SETTLEMENT  ⚠️ DVP (delivery versus payment) links
   the asset leg to the cash leg so neither can happen alone —
   the same idea as PVP for FX (§5)
```

---

## §5. ⚠️ Clearing, Netting and Settlement Risk

> **⚠️ §1's second organizing idea made concrete.**
```
⚠️ NETTING  ⚠️ bilateral and multilateral. ⚠️ The liquidity saving
   is enormous — netting can reduce the value that must actually
   settle by an order of magnitude
⚠️ CCPs (central counterparties)  ⚠️ novate contracts so the CCP
   becomes buyer to every seller and seller to every buyer.
   ⚠️ Concentrates risk deliberately in a heavily regulated,
   well-margined entity — ⚠️ and makes the CCP systemically
   critical by construction
⚠️ ⚠️ HERSTATT RISK  ⚠️ THE canonical settlement risk. ⚠️ In 1974
   Bankhaus Herstatt was closed mid-day after receiving Deutsche
   Mark payments but before making the corresponding dollar
   payments. ⚠️ Counterparties had paid and got nothing
   ⚠️ THE FIX  ⚠️ PVP (payment versus payment) — CLS Bank settles
   both legs of an FX trade simultaneously or neither happens
⚠️ ⚠️ FINALITY IS LEGAL, NOT TECHNICAL. ⚠️ A payment is final
   when the law says it is irrevocable — statute and system
   rules, not confirmation screens. ⚠️ This is exactly what
   "probabilistic finality" in blockchain systems does NOT
   provide, and it is a genuine and underdiscussed gap (§13)
```

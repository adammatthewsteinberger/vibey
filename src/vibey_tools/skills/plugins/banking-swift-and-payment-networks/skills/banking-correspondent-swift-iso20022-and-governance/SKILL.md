---
name: banking-correspondent-swift-iso20022-and-governance
description: "Use for cross-border payments and the messaging layer: correspondent banking and the nostro-vostro structure that makes international payments slow and expensive, what SWIFT actually is — a messaging cooperative, not a payment system — the MT to ISO 20022 migration and what richer data enables, gpi and end-to-end tracking, governance, sanctions and the geopolitics of network access, and the alternative and parallel systems including CIPS and SPFS."
---

# Banking and Payments: Correspondent Banking, What SWIFT Actually Is, Message Formats from MT to ISO 20022, gpi and Tracking, Governance and Sanctions, and Alternatives

> **Part 2 of 6** of the *Banking, SWIFT and Payment Networks* reference (plugin `banking-swift-and-payment-networks`), covering §6–§11. Sibling skills: `banking-payments-banks-reserves-and-settlement` (§0–§5), `banking-ripple-xrp-ledger-and-honest-assessment` (§12–§16), `banking-instant-payments-stablecoins-cbdcs-and-tokenization` (§17–§20), `banking-compliance-security-and-remittance-costs` (§21–§23), `banking-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ MESSAGING IS NOT MONEY MOVEMENT** (§7). **SWIFT does not transfer funds. It
>    carries instructions. Almost every confused claim about SWIFT — including "SWIFT is
>    slow" and "crypto will replace SWIFT" — collapses once this is clear.**
> 2. **⚠️ SETTLEMENT IS THE HARD PART, NOT TRANSMISSION** (§5 → `banking-payments-banks-reserves-and-settlement`, §6). **Getting a message
>    across the world is trivial and has been for decades. Extinguishing an obligation with
>    finality, across legal jurisdictions, with credit and liquidity risk managed, is what
>    the infrastructure is actually for.**
> 3. **⚠️ THE CORRESPONDENT MODEL IS THE THING BEING DISRUPTED** (§6, §24.2 → `banking-reference`). **Not SWIFT,
>    not banks — the chain of nostro/vostro relationships with pre-funded accounts is where
>    the cost, delay and opacity live, and every serious alternative attacks that.**

---

## §6. ⚠️ Correspondent Banking

> **⚠️ §1 → `banking-payments-banks-reserves-and-settlement`'s third organizing idea. This is the system everything is trying to replace, and
> understanding WHY it is bad is more useful than any pitch about what replaces it.**
```
⚠️ ⚠️ THE PROBLEM IT SOLVES  ⚠️ two banks in different countries
   have no common settlement point (§1). ⚠️ So Bank A holds an
   account WITH Bank B, in Bank B's currency
⚠️ ⚠️ NOSTRO AND VOSTRO  ⚠️ "our account with you" and "your
   account with us" — ⚠️ the SAME account seen from two sides
⚠️ ⚠️ WHY IT IS EXPENSIVE AND SLOW
   ⚠️ 1. PRE-FUNDING  ⚠️ capital sits idle in nostro accounts
      around the world just to be available. ⚠️ THIS IS THE
      SINGLE BIGGEST COST, and it is the thing ODL-style
      proposals target (§14)
   ⚠️ 2. ⚠️ CHAINS  ⚠️ if A and B have no direct relationship,
      the payment hops through intermediaries — each adding
      fees, time, and a point where information is lost
   ⚠️ 3. ⚠️ CUT-OFF TIMES AND TIME ZONES  ⚠️ a payment can wait
      overnight for a market to open. ⚠️ Much "slowness" is this
   ⚠️ 4. Compliance screening at every hop (§21)
   ⚠️ 5. FX conversion and spread
⚠️ ⚠️ DE-RISKING  ⚠️ since roughly 2011 the number of active
   correspondent relationships has FALLEN, as banks exit
   jurisdictions where compliance cost exceeds revenue.
   ⚠️ The effect falls hardest on small and poor economies —
   a genuine financial-inclusion harm caused by regulation
   working as designed at the level of the individual bank
```

---

# PART II — SWIFT

## §7. ⚠️ What SWIFT Actually Is

> **⚠️ §1 → `banking-payments-banks-reserves-and-settlement`'s first organizing idea, and the correction that unlocks the whole topic.**
```
⚠️ ⚠️ SWIFT IS A MESSAGING NETWORK. IT DOES NOT MOVE MONEY,
   HOLD MONEY, OR SETTLE ANYTHING. ⚠️ It carries standardized,
   authenticated instructions between financial institutions.
   ⚠️ The money moves through the accounts described in §6
⚠️ WHAT IT IS  ⚠️ a Belgian COOPERATIVE owned by its member
   institutions · ⚠️ eleven-thousand-plus institutions in more
   than two hundred countries · a secure network, a message
   standard, and a set of shared rules
⚠️ ⚠️ THEREFORE, WHEN PEOPLE SAY "SWIFT IS SLOW"  ⚠️ they are
   almost always describing correspondent banking (§6),
   compliance screening (§21), or cut-off times. ⚠️ The MESSAGE
   arrives in seconds. ⚠️ Blaming the messaging layer for
   settlement-layer problems is the single most common error in
   this area
⚠️ BIC / SWIFT CODE  ⚠️ the institution identifier — 8 or 11
   characters, and NOT an account number
⚠️ THE SERVICES  ⚠️ FIN (the classic message service) ·
   ⚠️ FINplus (ISO 20022, §8) · InterAct, FileAct · ⚠️ gpi (§9) ·
   sanctions and KYC utilities
⚠️ ⚠️ SWIFT'S REAL MOAT is not technology — it is NETWORK EFFECT
   plus STANDARDIZATION plus TRUST plus regulatory acceptance.
   ⚠️ Building a faster network is easy; getting eleven thousand
   institutions to adopt it is not
```

---

## §8. ⚠️ Message Formats: MT to ISO 20022

```
⚠️ ⚠️ MT (the legacy format)  ⚠️ numbered message types with
   positional, tag-based fields. ⚠️ Compact, decades old, and
   SEVERELY LIMITED — short free-text fields, no structure for
   addresses or parties, and character-set restrictions
   ⚠️ MT103  customer credit transfer — ⚠️ the workhorse
   ⚠️ MT202  bank-to-bank transfer · MT202COV (cover payment)
   ⚠️ MT940/942  statements · MT101 payment initiation
⚠️ ⚠️ ISO 20022 / MX  ⚠️ XML, richly structured, extensible,
   with a shared data DICTIONARY across business domains
   ⚠️ pacs.008  customer credit transfer (replaces MT103)
   ⚠️ pacs.009  financial institution transfer (replaces MT202)
   ⚠️ pain.001  payment initiation · camt.*  cash management
   ⚠️ THE NAMING  business area . message . variant . version
⚠️ ⚠️ WHY IT ACTUALLY MATTERS — and it is not "XML is nicer"
   ⚠️ STRUCTURED PARTY AND ADDRESS DATA transforms sanctions
      screening and AML (§21) — ⚠️ unstructured free-text names
      are why false-positive rates are so high
   ⚠️ Richer remittance information enables automatic
      reconciliation, which is a real corporate cost saving
   ⚠️ End-to-end data survives the hops of §6 instead of being
      truncated
⚠️ ⚠️ THE TRUNCATION PROBLEM was the core argument for migration:
   ⚠️ data lost at one hop cannot be recovered downstream, so
   the whole chain must speak the richer format for anyone to
   benefit (§24.1)
```

---

## §9. gpi and Tracking

**⚠️ SWIFT gpi (global payments innovation)** was the pre-blockchain response to the
complaints in §6: ⚠️ **an end-to-end tracking reference (UETR) carried through the chain, so
a payment can be traced; commitments on same-day availability and fee transparency; and a
tracker database.**
**⚠️ It genuinely improved things** — ⚠️ **the widely quoted figures on gpi payments
reaching beneficiaries within hours or minutes are Swift's own, and the honest reading is
that transparency improved substantially while the underlying correspondent structure
(§6) did not change.**
**⚠️ Pre-validation** checks account details before sending, ⚠️ **reducing the failed-payment
repair costs that are a large hidden expense.**
**⚠️ The strategic point**: ⚠️ **gpi was SWIFT demonstrating it could respond to the
blockchain challenge within the existing model — and it substantially blunted the "SWIFT
can't do this" argument.**

---

## §10. ⚠️ Governance, Sanctions and Geopolitics

**⚠️ SWIFT is a cooperative under Belgian law, overseen by the G-10 central banks with the
National Bank of Belgium as lead overseer** — ⚠️ **it is not an arm of any government, and
it insists on neutrality.**
> **⚠️ GOTCHA — but neutrality has limits, and "SWIFT sanctions" is a misnomer.** ⚠️ **SWIFT
> does not decide sanctions. It complies with the law of jurisdictions it operates in —
> most consequentially EU law.** **⚠️ Disconnection of Iranian banks in 2012 and 2018 and of
> certain Russian banks from 2022 followed EU regulation, not a SWIFT policy decision.**

**⚠️ Why disconnection is powerful**: ⚠️ **not because the messages are irreplaceable — telex
and email exist — but because losing the standard, the counterparty reach and the
compliance infrastructure makes doing business enormously more expensive and slower.**
**⚠️ The strategic consequence**: ⚠️ **exclusion has driven investment in alternatives (§11)
and is frequently cited in arguments for reducing dollar and Western infrastructure
dependence.** ⚠️ **Whether this durably fragments the system is genuinely contested and
worth holding lightly.**

---

## §11. Alternatives and Parallel Systems

**⚠️ CIPS (China)** — ⚠️ **often described as a SWIFT alternative, which conflates two
things: CIPS is primarily a CLEARING AND SETTLEMENT system for renminbi (closer to CHIPS
than to SWIFT), and it has historically used SWIFT messaging for much of its traffic.**
⚠️ **It is growing and it is not a like-for-like replacement.**
**⚠️ SPFS (Russia)** — ⚠️ **a domestic messaging system, functional within Russia and with
limited international participation.**
**⚠️ INSTEX** — ⚠️ **the European vehicle for Iran trade; a useful case study in how hard
this is, having handled very little before being wound down.**
**⚠️ Regional systems**: ⚠️ **BUNA, PAPSS in Africa, and bilateral local-currency
arrangements.**
**⚠️ The honest assessment**: ⚠️ **building a message network is easy; achieving the network
effect, legal acceptance and counterparty reach of §7 is what nobody has done — and the
alternatives so far serve specific political needs rather than competing generally.**

---

# PART III — RIPPLE AND THE XRP LEDGER

---
name: banking-reference
description: "Use when correcting a payments misconception, looking up a settlement time, volume, fee or migration-deadline figure, finding the sources, or needing a quick-reference picker — plus the current state of the ISO 20022 migration and what is actually settling on blockchain rails. Companion to the other banking and payments skills."
---

# Banking and Payments: What's Live, Misconceptions, Numbers and Dates, and Sources

> **Part 6 of 6** of the *Banking, SWIFT and Payment Networks* reference (plugin `banking-swift-and-payment-networks`), covering §24–§29. Sibling skills: `banking-payments-banks-reserves-and-settlement` (§0–§5), `banking-correspondent-swift-iso20022-and-governance` (§6–§11), `banking-ripple-xrp-ledger-and-honest-assessment` (§12–§16), `banking-instant-payments-stablecoins-cbdcs-and-tokenization` (§17–§20), `banking-compliance-security-and-remittance-costs` (§21–§23). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The plumbing is stable and slow-moving. Two areas moved. See §24 for the ISO 20022 migration, and what is actually settling on blockchain rails.

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
> 3. **⚠️ THE CORRESPONDENT MODEL IS THE THING BEING DISRUPTED** (§6 → `banking-correspondent-swift-iso20022-and-governance`, §24.2). **Not SWIFT,
>    not banks — the chain of nostro/vostro relationships with pre-funded accounts is where
>    the cost, delay and opacity live, and every serious alternative attacks that.**

---

## §24. What's Live — checked August 2026

### 24.1 ⚠️ ISO 20022: the migration succeeded, and it isn't over
**⚠️ §8 → `banking-correspondent-swift-iso20022-and-governance`'s transition passing its hardest deadline — with a live one three months out.**

- **⚠️ COEXISTENCE ENDED 22 NOVEMBER 2025.** ⚠️ **Swift permanently retired legacy MT
  payment instruction messages from cross-border flows, making ISO 20022 the sole standard
  for CBPR+.**
- **⚠️ THE ADOPTION FIGURE IS STRIKING.** ⚠️ **Swift reports a 97% adoption rate after the
  cutover weekend, describing it as a very successful end of coexistence.** ⚠️ **Fedwire
  went ISO-native in July 2025, and reporting puts over 70 countries and nearly 200 market
  infrastructure initiatives on the standard.**
- **⚠️ THE NEXT HARD DEADLINE IS 14 NOVEMBER 2026, and it is the harder one.**
  ⚠️ **Fully unstructured postal addresses stop being accepted in CBPR+ payments — only
  fully structured or hybrid (town name and country code in dedicated fields) will pass.**
  ⚠️ **The interbank MT101 relay is also decommissioned in favour of pain.001 version 9.**
- **⚠️ WHY THE ADDRESS RULE IS DISPROPORTIONATELY DIFFICULT**: ⚠️ **it is not a messaging
  change but a DATA GOVERNANCE change reaching into KYC records and customer master data
  (§21 → `banking-compliance-security-and-remittance-costs`) — you cannot emit a structured address you never collected.**
- ⚠️ **The roadmap continues to 2027–28 for statements, direct debits, charges and
  investigations, with camt.110 and camt.111 replacing the MT19x/29x exception messages.**

> **⚠️ GOTCHA — "97% adoption" and "fully migrated" are different claims, and the gap is the
> story.** ⚠️ **Swift's own guidance addresses institutions still relying on CONTINGENCY
> PROCESSING or IN-FLOW TRANSLATION, urging them to plan full adoption in 2026 — and one
> analysis observes that the translation safety net arguably shaped behaviour, with many
> institutions leaning on conversion layers rather than re-architecting around native ISO
> 20022.**
> ⚠️ **Contingency conversion is also being charged for as of January 2026, which is the
> economic nudge.** **⚠️ So a bank can be "compliant" while capturing none of §8 → `banking-correspondent-swift-iso20022-and-governance`'s actual
> benefits, because the rich data is being manufactured at the boundary rather than carried
> end to end.**

**⚠️ The strategic reading** is that November 2025 was the syntax milestone and the value
comes later — ⚠️ **structured data enforcement, investigations modernization, and instant
payment interoperability.** ⚠️ **One vendor analysis claims 44% of banks will miss the next
deadline, which is a marketing figure from a firm selling migration services and should be
read as such — but the underlying point that address data is harder than message format is
correct.**
**⚠️ Sourcing note: the dates, the 97% figure and the roadmap come from Swift's own
documentation and from J.P. Morgan's client guidance, which agree.**

### 24.2 ⚠️ What is actually settling on blockchain rails — and it is mostly not XRP
**⚠️ §12 → `banking-ripple-xrp-ledger-and-honest-assessment`'s distinction becoming the central fact of the story, and §16 → `banking-ripple-xrp-ledger-and-honest-assessment`'s second structural
critique playing out.**

- **⚠️ THE PATTERN IN THE REPORTING IS CONSISTENT: institutions choose STABLECOINS over
  volatile bridge assets.** ⚠️ **Reporting states that Ripple's major 2026 institutional
  deals settled in RLUSD rather than XRP, attributing it to price volatility blocking
  compliance approval on large trades.**
- **⚠️ THE ILLUSTRATIVE CASE.** ⚠️ **A May 2026 pilot reportedly involving JPMorgan,
  Mastercard, Ondo and Ripple cleared a cross-border tokenized US Treasury trade on the XRP
  Ledger in under five seconds — ⚠️ but the settlement ran through RLUSD, with XRP covering
  only network fees of a fraction of a cent.**
  ⚠️ **That single example is §12 → `banking-ripple-xrp-ledger-and-honest-assessment`'s distinction in one transaction: the LEDGER was used,
  the TOKEN essentially was not.**
- **⚠️ THE NUMBERS, all reported and all from crypto-sector sources**: ⚠️ **RLUSD reportedly
  around $1.5–1.8 billion market cap and roughly 89% of the XRP Ledger's stablecoin market;
  ⚠️ approximately 40% of RippleNet institutions actively using XRP for ODL; ⚠️ and a
  record 19 million weekly XRPL transactions in March 2026 alongside a reported 80% decline
  in the share using XRP specifically for cross-border payments.**
- **⚠️ WHERE XRP STILL HAS A CASE, and it is a real one**: ⚠️ **thin corridors where
  stablecoin liquidity is shallow and large transfers would suffer slippage — SBI Remit's
  Japan-to-Southeast-Asia flows are the cited example.** ⚠️ **This is a narrower claim than
  the general one and it is more defensible.**

> **⚠️ GOTCHA — the company and the token can succeed independently, and §16 → `banking-ripple-xrp-ledger-and-honest-assessment` flagged this as
> the structural risk.** ⚠️ **A Forbes analysis puts the diagnostic cleanly: banks can use
> Ripple's platform without ever using XRP, settling in fiat or in RLUSD, and Ripple earns
> revenue either way.** ⚠️ **It offers a checkable indicator — total transaction FEES on the
> XRP Ledger remaining minimal relative to XRP's market capitalization, which it reads as
> the network not being used at the scale the valuation implies.**
> **⚠️ That is a falsifiable test rather than a narrative, which is why it is worth
> carrying.**

**⚠️ Meanwhile the incumbent moved** (§16 → `banking-ripple-xrp-ledger-and-honest-assessment`'s fifth critique): ⚠️ **reporting indicates SWIFT
is building its own blockchain-based shared ledger, targeting a live MVP in 2026 with 40+
banks.** ⚠️ **If the network-effect argument in §7 → `banking-correspondent-swift-iso20022-and-governance` holds, an incumbent-led shared ledger is
a serious competitive development.**
**⚠️ Sourcing warning, and it is the strongest in this file.** ⚠️ **Almost every source for
this subsection is crypto-sector media, some of it explicitly price-focused, and several
figures trace to single unverified reports.** ⚠️ **I have marked everything as reported.**
⚠️ **The DIRECTIONAL finding — institutions settling in stablecoins rather than volatile
bridge assets — appears consistently across sources with differing editorial positions,
including ones sympathetic to XRP, which is why I hold that part more firmly than any
specific number.**

---

## §25. Misconceptions

| Misconception | Correction |
|---|---|
| SWIFT transfers money | ⚠️ **It carries messages. Money moves via §6 → `banking-correspondent-swift-iso20022-and-governance` accounts** (§7 → `banking-correspondent-swift-iso20022-and-governance`) |
| SWIFT is slow | ⚠️ **The message is seconds. Correspondent banking is slow** (§6 → `banking-correspondent-swift-iso20022-and-governance`, §7 → `banking-correspondent-swift-iso20022-and-governance`) |
| Crypto will replace SWIFT | ⚠️ **Category error — messaging vs settlement** (§7 → `banking-correspondent-swift-iso20022-and-governance`, §16 → `banking-ripple-xrp-ledger-and-honest-assessment`) |
| SWIFT imposes sanctions | ⚠️ **It complies with EU law. It doesn't decide** (§10 → `banking-correspondent-swift-iso20022-and-governance`) |
| CIPS is China's SWIFT | ⚠️ **It's primarily clearing and settlement, closer to CHIPS** (§11 → `banking-correspondent-swift-iso20022-and-governance`) |
| Banks lend out deposits | ⚠️ **Lending CREATES deposits. Both sides expand** (§2 → `banking-payments-banks-reserves-and-settlement`) |
| Your deposit is your money at the bank | ⚠️ **It's the bank's debt to you** (§2 → `banking-payments-banks-reserves-and-settlement`) |
| A payment moves something | ⚠️ **It discharges an obligation. Ledgers change** (§1 → `banking-payments-banks-reserves-and-settlement`) |
| Confirmation means final | ⚠️ **Finality is a LEGAL property** (§5 → `banking-payments-banks-reserves-and-settlement`, §13 → `banking-ripple-xrp-ledger-and-honest-assessment`) |
| Cross-border is slow because of technology | ⚠️ **Pre-funding, chains, cut-offs, screening** (§6 → `banking-correspondent-swift-iso20022-and-governance`, §21 → `banking-compliance-security-and-remittance-costs`) |
| Faster payments are strictly better | ⚠️ **Irrevocable + instant enables APP fraud** (§17 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`) |
| Ripple, XRP and the XRPL are one thing | ⚠️ **Three different things. Always check which** (§12 → `banking-ripple-xrp-ledger-and-honest-assessment`) |
| "Bank adopts Ripple" means XRP demand | ⚠️ **It usually doesn't** (§12 → `banking-ripple-xrp-ledger-and-honest-assessment`, §24.2) |
| Ripple is replacing SWIFT | ⚠️ **It targets correspondent banking** (§6 → `banking-correspondent-swift-iso20022-and-governance`, §16 → `banking-ripple-xrp-ledger-and-honest-assessment`) |
| The XRPL is mined | ⚠️ **Federated consensus. All 100bn created at launch** (§12 → `banking-ripple-xrp-ledger-and-honest-assessment`, §13 → `banking-ripple-xrp-ledger-and-honest-assessment`) |
| Stablecoins are like bank deposits | ⚠️ **A claim on an issuer. No deposit insurance** (§18 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`) |
| Fiat-backed stablecoins can't depeg | ⚠️ **USDC did in March 2023 when its reserve bank failed** (§18 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`) |
| Algorithmic stablecoins are a variant | ⚠️ **They have repeatedly failed. Terra is the case** (§18 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`) |
| CBDCs are basically stablecoins | ⚠️ **Central bank money. Disintermediation is the hard question** (§19 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`) |
| Tokenized deposits are stablecoins | ⚠️ **Bank liability, inside the regulated perimeter** (§20 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`) |
| Blockchain's value is disintermediation | ⚠️ **Industry converged on atomic settlement instead** (§20 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`) |
| SWIFT was hacked in the Bangladesh heist | ⚠️ **The endpoint was. Messages were valid** (§22 → `banking-compliance-security-and-remittance-costs`) |
| Remittance cost is a transmission problem | ⚠️ **It's the on-ramp, off-ramp and FX spread** (§23 → `banking-compliance-security-and-remittance-costs`) |
| ISO 20022 is just newer XML | ⚠️ **Structured party data transforms screening** (§8 → `banking-correspondent-swift-iso20022-and-governance`, §21 → `banking-compliance-security-and-remittance-costs`) |
| 97% adoption means migration is done | ⚠️ **Contingency and translation layers count** (§24.1) |
| Institutions settle in XRP | ⚠️ **Reporting says mostly RLUSD** (§24.2) |

---

## §26. Numbers and Dates

```
⚠️ ⚠️ ISO 20022 coexistence ENDED  ⚠️ 22 November 2025
⚠️ Adoption after cutover  ⚠️ 97% (Swift's own figure)
⚠️ Fedwire ISO-native  ⚠️ 14 July 2025
⚠️ ⚠️ NEXT HARD DEADLINE  ⚠️ 14 November 2026 — unstructured
   postal addresses rejected; MT101 relay → pain.001 v9
⚠️ Contingency conversion charged from  ⚠️ January 2026
⚠️ Remaining roadmap  ⚠️ 2027-2028 (statements, DD, E&I)
⚠️ Coverage  ⚠️ 70+ countries, ~200 MI initiatives (reported)
⚠️ SWIFT network  ⚠️ 11,000+ institutions, 200+ countries
⚠️ Key MT→MX  ⚠️ MT103→pacs.008 · MT202→pacs.009 · MT101→pain.001
⚠️ Herstatt  ⚠️ 1974 — the settlement risk case
⚠️ Bangladesh Bank heist  ⚠️ 2016, ~$81m succeeded of ~$1bn tried
⚠️ XRP supply  ⚠️ 100bn, all created at launch, no mining
⚠️ XRPL settlement  ⚠️ ~3-5 seconds, fees a fraction of a cent
⚠️ SEC v. Ripple  ⚠️ filed Dec 2020 · split ruling July 2023
⚠️ ⚠️ RLUSD (reported)  ⚠️ ~$1.5-1.8bn cap · ~89% of XRPL stablecoins
⚠️ ⚠️ RippleNet institutions using XRP for ODL  ⚠️ ~40% (reported)
⚠️ SDG remittance cost target  ⚠️ under 3% · global average higher
```

---

## §27. Sources

| Source | Why |
|---|---|
| **BIS CPMI publications** | ⚠️ **The authority on payment systems. Free** |
| **Swift standards and ISO 20022 documentation** | ⚠️ **§8 → `banking-correspondent-swift-iso20022-and-governance`, §24.1 — primary, and free** |
| **Bank of England, "Money creation in the modern economy" (2014)** | ⚠️ **§2 → `banking-payments-banks-reserves-and-settlement`. Short, free, and corrects the textbook** |
| **CPMI "Red Book" country payment system descriptions** | ⚠️ **§4 → `banking-payments-banks-reserves-and-settlement` by jurisdiction** |
| **FATF Recommendations** | ⚠️ **§21 → `banking-compliance-security-and-remittance-costs`, primary** |
| **World Bank Remittance Prices Worldwide** | ⚠️ **§23 → `banking-compliance-security-and-remittance-costs` — actual measured corridor costs** |
| **XRP Ledger documentation (xrpl.org)** | ⚠️ **§13 → `banking-ripple-xrp-ledger-and-honest-assessment` — technical, and note who maintains it** |
| **SEC v. Ripple filings and rulings** | ⚠️ **§15 → `banking-ripple-xrp-ledger-and-honest-assessment` — read the primary documents, not summaries** |
| **BIS Annual Economic Report chapters on the monetary system** | ⚠️ **§19–§20 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`, sceptical and rigorous** |
| **Financial Stability Board reports on stablecoins** | ⚠️ **§18 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`** |
| **Swift Customer Security Programme** | ⚠️ **§22 → `banking-compliance-security-and-remittance-costs`** |

---

## §28. Quick Reference

### 28.1 Picker
| Question | Where |
|---|---|
| Why did my international payment take days? | ⚠️ **Correspondent hops, cut-offs, screening — not SWIFT** (§6 → `banking-correspondent-swift-iso20022-and-governance`) |
| What does SWIFT actually do? | ⚠️ **Messaging. Not settlement** (§7 → `banking-correspondent-swift-iso20022-and-governance`) |
| Is this payment final? | ⚠️ **A legal question, not a screen** (§5 → `banking-payments-banks-reserves-and-settlement`) |
| Why is remittance so expensive? | ⚠️ **On-ramp, off-ramp, FX spread** (§23 → `banking-compliance-security-and-remittance-costs`) |
| Does "bank partners with Ripple" mean XRP? | ⚠️ **Usually no. Check the transaction path** (§12 → `banking-ripple-xrp-ledger-and-honest-assessment`, §24.2) |
| Stablecoin or tokenized deposit? | ⚠️ **Issuer claim vs bank liability** (§18 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`, §20 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`) |
| Are we ISO 20022 compliant? | ⚠️ **Ask if you're NATIVE or translating** (§24.1) |
| What breaks in November 2026? | ⚠️ **Unstructured addresses, MT101 relay** (§24.1) |
| Why so many false compliance alerts? | ⚠️ **Unstructured name matching** (§8 → `banking-correspondent-swift-iso20022-and-governance`, §21 → `banking-compliance-security-and-remittance-costs`) |
| Why did the bank exit that country? | ⚠️ **De-risking. Penalty exceeded profit** (§6 → `banking-correspondent-swift-iso20022-and-governance`, §21 → `banking-compliance-security-and-remittance-costs`) |
| Was SWIFT hacked? | ⚠️ **In the famous case, no — the endpoint was** (§22 → `banking-compliance-security-and-remittance-costs`) |

### 28.2 Evaluating a payments claim
- [ ] ⚠️ **Is this about MESSAGING or SETTLEMENT?** (§1 → `banking-payments-banks-reserves-and-settlement`, §7 → `banking-correspondent-swift-iso20022-and-governance`)
- [ ] ⚠️ **What provides FINALITY, and under whose law?** (§5 → `banking-payments-banks-reserves-and-settlement`)
- [ ] Does it remove pre-funding, or just re-describe it? (§6 → `banking-correspondent-swift-iso20022-and-governance`)
- [ ] ⚠️ **For crypto claims: is the TOKEN in the transaction path?** (§12 → `banking-ripple-xrp-ledger-and-honest-assessment`)
- [ ] Pilot, MOU, or production volume? (§16 → `banking-ripple-xrp-ledger-and-honest-assessment`)
- [ ] ⚠️ **Who published the figure, and what do they hold?** (§16 → `banking-ripple-xrp-ledger-and-honest-assessment`, §24.2)
- [ ] Does it handle the on-ramp and off-ramp, or assume them? (§23 → `banking-compliance-security-and-remittance-costs`)
- [ ] ⚠️ **How does compliance screening work in it?** (§21 → `banking-compliance-security-and-remittance-costs`)
- [ ] What happens when a party fails mid-transaction? (§5 → `banking-payments-banks-reserves-and-settlement`)
- [ ] ⚠️ **Is the comparison against gpi and instant rails, or against 2015?** (§9 → `banking-correspondent-swift-iso20022-and-governance`, §17 → `banking-instant-payments-stablecoins-cbdcs-and-tokenization`)

---

## §29. Method

**§1–§23 → `banking-payments-banks-reserves-and-settlement`, `banking-correspondent-swift-iso20022-and-governance`, `banking-ripple-xrp-ledger-and-honest-assessment`, `banking-instant-payments-stablecoins-cbdcs-and-tokenization`, `banking-compliance-security-and-remittance-costs` rests on established institutional description** — **the balance-sheet mechanics of
banking, RTGS versus net settlement, correspondent structure, Herstatt risk, the SWIFT
message model, and the compliance regime.** ⚠️ **None needed verification; CPMI and BIS
material documents all of it, and the Bank of England settled the money-creation question in
2014.**

**Two searches were run in August 2026**, on **ISO 20022** and **what is actually settling
on blockchain rails** — ⚠️ **the first because §8 → `banking-correspondent-swift-iso20022-and-governance`'s migration passed its hardest deadline
and has another three months out, the second because §12 → `banking-ripple-xrp-ledger-and-honest-assessment`'s distinction has become the
central fact of the story and the popular framing gets it backwards.**

**Confidence.** **High** in §7 → `banking-correspondent-swift-iso20022-and-governance` and §6 → `banking-correspondent-swift-iso20022-and-governance`, which are the sections I'd most want read.
⚠️ **"SWIFT is messaging, not money movement" is the correction that dissolves most confused
claims in this area, including the ones made by people selling alternatives.** ⚠️ **And §6 → `banking-correspondent-swift-iso20022-and-governance`
is the more useful diagnosis: the cost, delay and opacity live in the correspondent
structure — pre-funded nostro accounts, intermediary chains, cut-off times — which is what
every serious alternative actually targets.**
**⚠️ §12 → `banking-ripple-xrp-ledger-and-honest-assessment`'s three-way distinction is the practical tool: ask of any claim whether it concerns
the company, the token, or the ledger.**

**High** on §24.1, which is unusually well-sourced because Swift documents its own
migration: ⚠️ **coexistence ended 22 November 2025, Swift reports 97% adoption, the next
hard deadline is 14 November 2026 for structured addresses and the MT101 relay.**
⚠️ **The gotcha is the part worth carrying — "97% adoption" and "fully migrated" differ,
because contingency processing and in-flow translation count as the former, and Swift's own
guidance addresses institutions in exactly that position.** **⚠️ A bank can be compliant
while capturing none of the actual benefit.**

**Moderate at best** on §24.2's specific figures, and I want to be explicit about why.
⚠️ **Almost every source is crypto-sector media, some explicitly price-focused, and several
numbers trace to single unverified reports.** ⚠️ **I have marked every figure as reported
and would not rely on any individual one.**
⚠️ **What I hold more firmly is the DIRECTION, because it appears consistently across
sources with differing editorial positions including ones sympathetic to XRP: institutions
are settling in stablecoins rather than in volatile bridge assets, and the ledger is being
used more than the token.** ⚠️ **The Forbes diagnostic — total XRPL transaction fees
relative to market capitalization — is worth carrying precisely because it is falsifiable
rather than narrative.**
**⚠️ And the standing warning for this whole topic: check whether a claim is about Ripple,
XRP, or the XRP Ledger, every single time.**

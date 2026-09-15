---
name: ecommerce-payment-methods-sca-fraud-and-pci
description: "Use when adding payment methods or hardening a checkout: cards and network tokens, wallets (Apple Pay, Google Pay), the bank rails underneath (ACH, SEPA, SWIFT and ISO 20022, open banking, instant payments such as FedNow, RTP, PIX, and UPI), BNPL; Strong Customer Authentication and 3-D Secure, authorization rates and decline handling; the fraud types, chargebacks and disputes; and PCI DSS v4.0.1 scope as architecture (the SAQ A trap, iframes and hosted fields, script integrity) plus the rest of payments security."
---

# eCommerce & Payments: Payment Methods, SCA and 3-D Secure, Fraud, and PCI DSS

> **Part 2 of 4** of the *eCommerce and Payments Development* reference (plugin `ecommerce-development`), covering §5–§8. Sibling skills: `ecommerce-payments-architecture-and-integration` (§0–§4), `ecommerce-billing-tax-platforms-and-checkout` (§9–§14), `ecommerce-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `ecommerce-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — accounting reality, distributed-systems truth, or a lesson every
>   payments team learns the hard way. Does not expire.
> - **[VERSIONED]** — API versions, regulatory deadlines, platform behaviour, market
>   state. Verify before relying on it.
> - **[CONTESTED]** — practitioners genuinely disagree.
>
> **⚠️ GOTCHA** boxes mark the mistakes that double-charge customers, lose orders, fail an
> audit, or quietly leak revenue for months before anyone notices.
>
> **Scope note:** this is an engineering document. It covers how these systems are built,
> integrated, and operated. **It is not legal, tax, or financial advice** — the regulatory
> material in §8 and §11 → `ecommerce-billing-tax-platforms-and-checkout` tells you what to ask your counsel and your acquirer, not what
> your obligations are.
>
> **The three framings that organize everything below:**
> 1. **Money is not data. It is data with an audit trail, a counterparty, and a
>    regulator.** A dropped message in most systems is an inconvenience; here it's a
>    customer charged twice, or an order shipped for free. **Every design decision follows
>    from that asymmetry.**
> 2. **The network will fail mid-transaction, and you must be correct anyway.** This is a
>    distributed-systems problem wearing a business costume. **Idempotency and
>    reconciliation (§3 → `ecommerce-payments-architecture-and-integration`) are not best practices — they are the load-bearing walls.**
> 3. **Your job is mostly to touch card data as little as possible.** PCI scope is a
>    function of architecture, and the difference between the easy compliance path and the
>    expensive one is decided in week one (§8).

---

## §5. Payment Methods and Rails

### 5.1 Cards

The default, and the most expensive. **Interchange + scheme fees + acquirer margin** is
what you're actually paying; "2.9% + 30¢" is a blended retail price over that. Know
**card-present vs. card-not-present** (CNP costs more and carries the fraud liability),
**debit vs. credit vs. prepaid**, and **commercial cards** (higher interchange, and Level
2/Level 3 data can reduce it for B2B).

**Network tokens** (replacing the PAN with a network-issued token) improve authorization
rates and survive card reissuance — **worth enabling; most PSPs support it**.

### 5.2 Beyond cards

**[DURABLE] Payment method mix is a localization problem, and getting it wrong silently
caps your conversion in a market.** Cards dominate the US; much of Europe runs on bank
transfers and local schemes (iDEAL in NL, Bancontact in BE, BLIK in PL); Germany
historically favours invoice and direct debit; Brazil runs on PIX; India on UPI; much of
Southeast Asia and Africa on wallets and mobile money.

- **Wallets** — Apple Pay, Google Pay, PayPal, Link. **Meaningful conversion lift on
  mobile** because they eliminate form entry, and they carry tokenized credentials.
- **Bank transfers / A2A** — ACH (US, cheap, slow, **reversible for up to 60 days on
  consumer accounts** — a real fraud exposure), SEPA Direct Debit (EU, with an 8-week
  no-questions refund right), open banking payment initiation.
- **Instant payments** — FedNow and RTP in the US, SEPA Instant in the EU, PIX, UPI,
  Faster Payments. **Generally irrevocable**, which changes the fraud model entirely:
  the risk moves from chargebacks to authorized push payment (APP) fraud (§7.1).
- **BNPL** — Klarna, Afterpay, Affirm. Higher conversion and AOV, higher fees, and the
  provider typically takes the credit risk.
- **Direct carrier billing**, **cash vouchers** (OXXO, Boleto), **crypto/stablecoin** (§14.3 → `ecommerce-billing-tax-platforms-and-checkout`).

### 5.3 The bank rails underneath

**[DURABLE] Worth understanding even if you never touch them directly**, because they
determine settlement timing and irrevocability.

**SWIFT** is the interbank *messaging* network — it moves instructions, not money; the
money moves through correspondent banking relationships and nostro/vostro accounts. This
is why international wires take days and why fees appear from intermediaries you never
chose. **ISO 20022** is the structured, data-rich message standard that has been replacing
the older MT formats across major payment systems, enabling far richer remittance data and
better sanctions screening and reconciliation. **[VERSIONED] Migration timelines differ by
scheme and market — verify the current state for any rail you depend on**, as several major
coexistence periods have recently ended or are ending.

**Card networks** (Visa, Mastercard, Amex, Discover, plus domestic schemes like Cartes
Bancaires and UnionPay) are a four-party model: cardholder, issuer, acquirer, merchant, with
the network in the middle setting rules and interchange.

---

## §6. SCA, 3-D Secure, and Authorization Rates

### 6.1 Strong Customer Authentication

**[DURABLE] SCA requires two of three factors** — knowledge, possession, inherence — for
in-scope electronic payments in the EU/UK. **3-D Secure 2.x is the dominant technical
mechanism for satisfying it on card-not-present transactions**, and it passes rich device
and transaction data to the issuer to enable frictionless authentication where risk is low.

**The exemptions matter commercially** — low value, transaction risk analysis (TRA),
recurring/MIT, merchant-initiated transactions, and trusted beneficiaries. **Requesting the
right exemption is the difference between a frictionless approval and an abandoned
checkout**, and modern PSP APIs handle much of this automatically when you use their
higher-level payment objects.

**[VERSIONED] PSD3/PSR refines the SCA framework rather than replacing 3DS2 — the protocol
itself is not changing.** Expect expanded SCA triggers (new token creation, spending-limit
changes) once the new rules apply, and note that **delegating SCA to a third party is
being treated as formal outsourcing**, pulling in EBA outsourcing guidelines and DORA
obligations — written agreements, SLAs, exit plans, audit rights.

### 6.2 Authorization rates

**[DURABLE] A 1% improvement in authorization rate is usually worth more than any
conversion optimization you'll do on the front end**, and almost nobody measures it.

Levers: **network tokens** (§5.1), **account updater** for expired/reissued cards, correct
**MCC** coding, **AVS/CVV** data quality, **smart retries** on soft declines (with respect
for network retry rules — excessive retries incur fees and can flag you), **local
acquiring** in major markets (a locally-acquired transaction approves materially better
than a cross-border one), and **passing full 3DS data** even when not required.

**Soft vs. hard declines**: soft (insufficient funds, do-not-honor, issuer unavailable) may
succeed on retry; **hard (stolen card, invalid account, revoked authorization) must never
be retried** — retrying hard declines is a compliance problem, not just futile.

---

## §7. Fraud and Disputes

### 7.1 The fraud types

| Type | Who loses | Notes |
|---|---|---|
| **Stolen card / CNP fraud** | **The merchant**, via chargeback | The classic. Liability may shift with 3DS |
| **Friendly fraud / first-party misuse** | The merchant | **The largest category by volume for many merchants**, and the hardest to fight |
| **Account takeover** | Customer and merchant | Protect accounts, not just checkout |
| **Card testing** | Merchant (fees, reputation) | Bots probing stolen numbers with tiny charges. **Rate-limit and CAPTCHA your payment endpoint** |
| **Refund/return abuse** | Merchant | Policy problem more than a technical one |
| **Triangulation, promo abuse, reseller fraud** | Merchant | Business-logic attacks |
| **APP fraud** | The customer (and increasingly the PSP) | Growing with instant rails; ⚠️ **PSD3/PSR shifts liability toward PSPs** — §17 → `ecommerce-reference` |

**[DURABLE] Fraud prevention is an optimization problem with two costs, and teams
systematically optimize only one.** False negatives cost you chargebacks; **false positives
cost you good customers, and are invisible unless you measure them.** A rule set tuned only
on chargeback rate will strangle revenue.

### 7.2 Chargebacks

```
customer disputes → issuer initiates → funds pulled from you + a fee
  → you accept, or REPRESENT with evidence
    → issuer decides → possible pre-arbitration → arbitration (expensive, rare)
```
**⚠️ You lose the fee either way, even when you win.** And **chargeback ratios are
monitored by the networks**; exceeding thresholds puts you in a monitoring program with
fines and, ultimately, loss of processing. **The ratio matters more than the absolute
number.**

**Prevention beats representment**: a clear and recognizable **billing descriptor** (a
startling share of disputes are "I don't recognize this charge"), obvious cancellation and
refund paths, delivery confirmation, pre-renewal notices for subscriptions, and responsive
support. **Order Insight / Consumer Clarity**-style network programs let issuers show
transaction detail in the banking app and deflect disputes before they start.

---

## §8. PCI DSS and Security

### 8.1 Scope is architecture

**[DURABLE] Everything in PCI is downstream of one question: does cardholder data ever
touch your systems?**

```
SAQ A       fully outsourced — hosted payment page or PSP-hosted iframe    ← aim here
SAQ A-EP    your page, but it affects the transaction (e.g. JS-based fields)
SAQ D       you touch, transmit, or store cardholder data                  ← expensive
```
**The strategic advice is simple: use the PSP's hosted fields, iframe, or redirect, store
only PSP tokens and IDs, and never let a PAN reach your server or your logs.** This keeps
you in the lightest tier and out of the most expensive parts of the standard.

### 8.2 The v4.0.1 e-commerce requirements — and the SAQ A trap

**[VERSIONED, and this is the part most merchants have wrong.]**

**PCI DSS v4.0.1's future-dated requirements became mandatory on 31 March 2025** — 51
requirements that had been "best practice" until that date, on top of 13 that applied
immediately. **There is no remaining transition phase, and v4.0.1 is the only active
version.** Two matter most for e-commerce:
- **Requirement 6.4.3** — all payment page scripts must be **authorized, integrity-checked,
  and inventoried**.
- **Requirement 11.6.1** — a **change- and tamper-detection mechanism** alerting on
  unauthorized changes to payment pages and scripts, evaluated **at least weekly**.

Both exist to address **Magecart-style e-skimming**, where malicious JavaScript is injected
into a checkout page to exfiltrate card data.

> **⚠️ GOTCHA — the SAQ A change looked like relief and is arguably the opposite.** In
> January 2025 the PCI SSC **removed 6.4.3, 11.6.1, and 12.3.1 from SAQ A** in response to
> merchant feedback — and **replaced them with an eligibility criterion**: the merchant must
> confirm **"their site is not susceptible to attacks from scripts that could affect the
> merchant's e-commerce system(s)."**
>
> **Read the scope change carefully.** The old requirements applied to the *payment page*.
> The new eligibility criterion applies to **your entire website**. Merchants using
> redirects — previously out of scope for 6.4.3 and 11.6.1 entirely — must now verify that
> **all scripts within their e-commerce system** are secure. **If you cannot make that
> confirmation, you are not eligible for SAQ A at all and must validate against SAQ A-EP**,
> which carries a far larger requirement set.
>
> A February 2025 PCI SSC FAQ clarified two routes to satisfy it: **implement 6.4.3 and
> 11.6.1 yourself anyway**, or **obtain written confirmation from a PCI DSS compliant
> third-party service provider** that its embedded payment solution protects against script
> attacks when implemented per their instructions. Practitioners also recommend
> demonstrating via web application testing or a properly configured WAF.
>
> The October 2024 SAQ A retired **31 March 2025**; the January 2025 (r1) version took
> effect the same day.

### 8.3 The rest of security

**CSP** and **Subresource Integrity (SRI)** are the practical implementations of 6.4.3 —
and are worth doing regardless of which SAQ you file. **Minimize third-party scripts on
checkout** (every analytics tag is a supply-chain risk on your highest-value page).
**Tokenize everything**; store PSP tokens, never PANs. **TLS 1.2+ everywhere.** Rate-limit
payment endpoints against card testing. Secrets in a manager, not env files in git. And
**PCI is contractual, not statutory in most jurisdictions** — but the financial consequences
(card-brand fines levied on your acquirer and passed to you, forensic investigation costs,
and potential loss of processing) are severe and multi-layered.

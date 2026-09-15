---
name: ecommerce-payments-architecture-and-integration
description: "Use when designing or integrating a payments system. Covers the shape of a commerce system, the order state machine and consistency, the payment lifecycle (authorization, capture, settlement, refunds, and money handling — minor units, rounding, currencies), integration engineering (idempotency keys, webhooks and replay, reconciliation, error handling and retries), and choosing among PSPs, gateways, and orchestrators (Stripe, Adyen, PayPal, Braintree) including API versioning. Includes the router for the whole ecommerce-development reference."
---

# eCommerce & Payments: Architecture, Payment Lifecycle, Integration Engineering, and PSPs

> **Part 1 of 4** of the *eCommerce and Payments Development* reference (plugin `ecommerce-development`), covering §0–§4. Sibling skills: `ecommerce-payment-methods-sca-fraud-and-pci` (§5–§8), `ecommerce-billing-tax-platforms-and-checkout` (§9–§14), `ecommerce-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> material in §8 → `ecommerce-payment-methods-sca-fraud-and-pci` and §11 → `ecommerce-billing-tax-platforms-and-checkout` tells you what to ask your counsel and your acquirer, not what
> your obligations are.
>
> **The three framings that organize everything below:**
> 1. **Money is not data. It is data with an audit trail, a counterparty, and a
>    regulator.** A dropped message in most systems is an inconvenience; here it's a
>    customer charged twice, or an order shipped for free. **Every design decision follows
>    from that asymmetry.**
> 2. **The network will fail mid-transaction, and you must be correct anyway.** This is a
>    distributed-systems problem wearing a business costume. **Idempotency and
>    reconciliation (§3) are not best practices — they are the load-bearing walls.**
> 3. **Your job is mostly to touch card data as little as possible.** PCI scope is a
>    function of architecture, and the difference between the easy compliance path and the
>    expensive one is decided in week one (§8 → `ecommerce-payment-methods-sca-fraud-and-pci`).

---

## §0. Routing

### 0.1 The question router

| Asked about... | Go to |
|---|---|
| System architecture and where the complexity lives | §1 |
| The payment lifecycle: auth, capture, settlement, refund | §2 |
| **Integration engineering: idempotency, webhooks, reconciliation** | **§3** |
| Choosing a PSP / gateway / processor | §4 |
| Payment methods and rails (cards, wallets, ACH/SEPA, SWIFT) | §5 → `ecommerce-payment-methods-sca-fraud-and-pci` |
| SCA, 3-D Secure, auth rates, declines | §6 → `ecommerce-payment-methods-sca-fraud-and-pci` |
| Fraud, chargebacks, disputes | §7 → `ecommerce-payment-methods-sca-fraud-and-pci` |
| PCI DSS scope and security | §8 → `ecommerce-payment-methods-sca-fraud-and-pci` |
| Subscriptions, billing, revenue recognition | §9 → `ecommerce-billing-tax-platforms-and-checkout` |
| Marketplaces, split payments, payouts | §10 → `ecommerce-billing-tax-platforms-and-checkout` |
| Tax, currency, cross-border | §11 → `ecommerce-billing-tax-platforms-and-checkout` |
| Platform choice: Shopify, headless, custom | §12 → `ecommerce-billing-tax-platforms-and-checkout` |
| Catalog, cart, checkout, conversion | §13 → `ecommerce-billing-tax-platforms-and-checkout` |
| Agentic commerce (AI agents buying things) | §14 → `ecommerce-billing-tax-platforms-and-checkout` |
| "Don't do this" | §15 → `ecommerce-reference` |
| "Which approach is better?" | §16 → `ecommerce-reference` (contested) |
| "Is this still current?" | §17 → `ecommerce-reference` |
| Docs, books, people | §18 → `ecommerce-reference` |

---

## §1. Architecture

### 1.1 The shape of the system

```
STOREFRONT ─── catalog · search · cart ─── CHECKOUT ─── payment
    │                                          │
    ├── CMS / merchandising                    ├── fraud screening
    ├── pricing & promotions                   ├── tax calculation
    └── personalization / recs                 └── address validation
                                               │
                                        ORDER MANAGEMENT (OMS)
                                               │
        ┌──────────────┬────────────────┬──────┴──────┬─────────────┐
     inventory     fulfillment      payments        tax         customer
     (ATP, holds)  (WMS, 3PL,       (capture,     (remittance)  (accounts,
                   shipping)         refunds,                    support)
                                     payouts)
                                               │
                                     LEDGER + RECONCILIATION
                                               │
                                          accounting / ERP
```

**[DURABLE] The hard parts are not where people expect.** Rendering a product page is
solved. The genuinely difficult problems are:
- **Inventory correctness under concurrency** — overselling is a customer-facing failure
  and an operational one. Reserve at cart or at order? For how long?
- **Order state as a distributed transaction** across payment, inventory, and fulfillment
  systems that can each fail independently.
- **Money movement correctness** (§2, §3).
- **Tax** (§11 → `ecommerce-billing-tax-platforms-and-checkout`) — deceptively deep.
- **Returns and partial fulfillment**, which turn a clean order model into a graph.

### 1.2 The order state machine

**[DURABLE] Model the order explicitly as a state machine, and make every transition
idempotent and logged.** Ad-hoc boolean flags (`is_paid`, `is_shipped`) collapse under
partial refunds, partial shipments, and cancellations.

```
created → payment_pending → payment_authorized → confirmed
   → [partially_]fulfilled → completed
        ↘ payment_failed   ↘ cancelled   ↘ [partially_]refunded  ↘ disputed
```
**⚠️ The states people forget**: authorized-but-not-captured (and the auth expiring —
typically ~7 days for card auths, shorter for some methods), partially captured, partially
refunded, refunded-after-dispute, and **fulfilled-then-chargebacked** (you have neither
the goods nor the money).

### 1.3 Consistency

**[DURABLE] You cannot have a distributed transaction across a payment processor, your
database, and a warehouse.** So you use **sagas with compensating actions**: authorize
payment → reserve inventory → if reservation fails, void the authorization. Design the
compensations *first*; they're the part that gets skipped and the part that matters.

**The outbox pattern** is the standard answer for "update the database and emit an event
atomically": write the event to an outbox table in the same transaction, then a relay
publishes it. Without it, you get orders that exist with no downstream notification, or
notifications for orders that rolled back.

**⚠️ Never make an external payment call inside a database transaction.** The call takes
seconds, holds locks, and if it times out you have no idea whether it succeeded — while
holding a transaction open. Authorize first, then record, with idempotency to make the
retry safe (§3.1).

---

## §2. The Payment Lifecycle

### 2.1 What actually happens

```
CUSTOMER → merchant → PSP/gateway → acquirer → CARD NETWORK → issuer
                                                                 │
   authorization decision ←──────────────────────────────────────┘
   (approve / decline / soft decline requiring SCA)

then, separately and later:
   CAPTURE  → clearing → SETTLEMENT (funds move, T+1 to T+3) → payout to you
```

**[DURABLE] The distinction that matters most: authorization ≠ capture ≠ settlement ≠
payout, and they happen at different times.**

| Step | What it is | Notes |
|---|---|---|
| **Authorization** | Issuer holds funds and promises them | Expires (~7 days typical, varies). Reduces the customer's available balance immediately |
| **Capture** | You claim the authorized funds | Can be partial. **Capture at fulfillment for physical goods, at purchase for digital** |
| **Void / reversal** | Cancel an uncaptured auth | **Always void rather than leaving an auth to expire** — the customer's money is held otherwise |
| **Clearing & settlement** | Networks and banks move real money | T+1 to T+3 typically |
| **Payout** | PSP sends you the net | Net of fees, refunds, chargebacks, reserves |
| **Refund** | Money back to the original method | ⚠️ Days to appear. **Fees are often not refunded** |
| **Chargeback** | Customer disputes via their bank | §7 → `ecommerce-payment-methods-sca-fraud-and-pci` |

**⚠️ The single most common junior mistake: treating a successful authorization as
"paid."** It isn't. It's a promise that can be voided, expire, fail at capture, or be
reversed. **Fulfil on capture, not on auth** — and even then, see §7 → `ecommerce-payment-methods-sca-fraud-and-pci`.

### 2.2 Amounts and money handling

**[DURABLE] Never use floating point for money.** `0.1 + 0.2 != 0.3`, and in a financial
system that becomes a reconciliation discrepancy nobody can explain. **Use integer minor
units** (cents) or an arbitrary-precision decimal type.

**⚠️ Not every currency has 2 decimal places.** JPY and KRW have 0; BHD, KWD, and JOD have
3. A hardcoded `× 100` breaks in those markets. **Use the ISO 4217 exponent.**

**Always store the currency with the amount.** An `amount` column without a `currency`
column is a bug waiting for your first international order. And **store the original
amount and currency alongside any converted values** — never only the converted figure.

**Rounding**: decide the rule, document it, apply it consistently, and **reconcile
line-item rounding against the order total** — tax and discount allocation across line
items is where the cents go missing.

---

## §3. Integration Engineering

**[DURABLE] This is the highest-value section in the document. Most payment bugs in
production are failures of these four things.**

### 3.1 Idempotency

**The problem**: your server sends a charge request. The network times out. **You do not
know whether the charge happened.** Retry and you may double-charge; don't retry and you
may lose the order.

**The solution**: an **idempotency key** on every mutating request. Stripe recommends
adding one to all POST requests; if it receives two requests with the same key, **it
returns the result of the first rather than executing twice**.

```
✓  key = hash(internal_checkout_attempt_id)     // deterministic, survives a crash
⚠️ key = uuid4()                                 // regenerated on retry → useless
```
**[DURABLE] Derive the key from the business action, not from the HTTP request.** A
payment tied to one internal checkout attempt must reuse the same key across all safe
retries — which means **generating and persisting it before the first call**, so a process
crash between generating and sending doesn't lose it. **⚠️ Stripe caches idempotency
results for 24 hours**; after that the same key creates a new request.

### 3.2 Webhooks

**[DURABLE] Webhooks are at-least-once, never exactly-once. That single fact drives every
operational decision.**

```
1. VERIFY THE SIGNATURE against the RAW request body — before parsing.
   ⚠️ Skip this and anyone can POST fake payment events to your endpoint.
2. RETURN 200 IMMEDIATELY. Process asynchronously.
   Stripe times out at ~30s and retries; a slow handler looks like a failure.
3. DEDUPLICATE on the event ID:
   INSERT event_id INTO processed_events  -- unique constraint
   -- unique violation → already handled → skip
4. Then do the work, in a transaction.
5. Re-fetch the resource from the API rather than trusting the payload.
```

> **⚠️ GOTCHA — the webhook failures that cost real money:**
> - **Fulfilling on the redirect URL instead of the webhook.** The user closes the tab
>   before redirecting and the order never completes. **The webhook is the source of
>   truth; the redirect is a UX nicety.**
> - **Non-idempotent handlers.** One practitioner reports observing the same
>   `checkout.session.completed` delivered **three times within 60 seconds** during a
>   provider infrastructure event, causing triple-provisioning.
> - **Returning 200 before processing** — the event is now lost, with no retry coming.
> - **Handling only the happy path.** A system that handles `invoice.paid` but not
>   `invoice.payment_failed` leaves users on paid tiers after their card declines.
>   **At scale this is quiet, continuous revenue leakage.**
> - **Assuming ordering.** Events can arrive out of order. Check the resource's current
>   state, don't infer it from event sequence.
> - **No dead-letter queue** for events that fail repeatedly.
>
> Stripe retries for **up to ~72 hours** with backoff, which is your safety net — but only
> if your endpoint returns non-2xx on genuine failure rather than swallowing errors.

### 3.3 Reconciliation

**[DURABLE] Your database and your processor's records will diverge. Plan for it.**
A nightly job comparing your orders against the processor's records for the past 24–48
hours surfaces discrepancies before they become financial disputes. Reconcile:
**auth vs. capture vs. settlement**, **your order total vs. the settled amount net of
fees**, **refunds issued vs. refunds settled**, and **payouts vs. the sum of their
constituent transactions**.

**[DURABLE] Build a ledger.** Double-entry, append-only, one row per money movement, never
updated in place. It is the only structure that survives partial refunds, disputes,
multi-currency, and an auditor. **Retrofitting a ledger after eighteen months of
production data is one of the worst projects in this domain** — do it at the start.

### 3.4 Error handling

**Decline vs. error vs. indeterminate** are three different things and need three
different behaviours. **⚠️ Treat a 500 or a timeout as *indeterminate*, not as failure** —
Stripe's own guidance is explicit that a 500 request's result is indeterminate, that they
attempt to reconcile such requests, and that you should configure webhook handlers to
receive event objects you'd never see in a normal API response.

**Retry with exponential backoff and jitter**, only on 5xx and network errors, **always
with the same idempotency key**, and with a cap.

**Never log full card numbers, CVVs, or API secrets** — this puts your logging
infrastructure in PCI scope (§8 → `ecommerce-payment-methods-sca-fraud-and-pci`) and it happens constantly. **Rotate any key that has ever
been committed to version control; assume it is compromised.**

---

## §4. PSPs and the Platform Layer

### 4.1 The categories

| Layer | What it does | Examples |
|---|---|---|
| **Payment gateway** | Transmits transaction data | Increasingly bundled |
| **Payment processor / acquirer** | Moves money, holds the merchant relationship | Chase Paymentech, Worldpay, Elavon |
| **PSP / aggregator** | Gateway + processing + your merchant account under theirs | **Stripe, PayPal, Square, Adyen, Braintree, Mollie, Razorpay** |
| **Orchestration** | Routes across multiple PSPs | Gr4vy, Primer, Spreedly |
| **Merchant of record (MoR)** | **Sells as the legal seller — takes on tax and compliance** | Paddle, Lemon Squeezy, FastSpring |

**[DURABLE] The MoR option deserves more consideration than it gets**, especially for
digital goods sold internationally. They become the legal seller, which means **they own
VAT/GST registration and remittance across jurisdictions** (§11 → `ecommerce-billing-tax-platforms-and-checkout`) — often the single
largest hidden cost for a small team selling globally. You pay a higher rate for it.

### 4.2 Choosing

**Ask about**: pricing (headline rate *plus* cross-border, currency conversion, chargeback,
and payout fees — **the effective rate is what matters, and it is never the headline**),
supported methods and geographies, **payout timing and reserves** (a 90-day rolling reserve
is a cash-flow event, not a footnote), API and SDK quality, webhook reliability, dispute
tooling, **account stability** (aggregators can and do freeze accounts — have a fallback),
and **data portability**: can you migrate stored payment credentials to another provider?
Networks support this and providers will facilitate it, but **ask before you're locked in**.

**⚠️ Test mode is not production.** Sandbox environments differ in latency, decline
behaviour, webhook timing, and edge cases. Budget for problems that only appear on live
traffic.

### 4.3 API versioning

**[DURABLE]** Payment APIs pin a version per account or per request, which is a genuine
kindness — but it means **your integration silently ages**. Upgrading is a real project
with behaviour changes. Track your pinned version, read the changelogs, and **upgrade
deliberately on a schedule** rather than discovering you're four years behind during an
incident.

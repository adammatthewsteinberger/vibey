---
name: ecommerce-billing-tax-platforms-and-checkout
description: "Use when building subscriptions and recurring billing (dunning, proration, trials), marketplaces and multi-party payments (merchant of record, KYC, split payments and payouts), sales tax, VAT, and cross-border (nexus, thresholds, duties), choosing platform vs headless vs custom (Shopify, composable commerce, build vs buy), designing the catalog, cart, and checkout (the data model, conversion), or evaluating agentic commerce — what it is, the standards contest, and the reality check."
---

# eCommerce & Payments: Subscriptions, Marketplaces, Tax, Platforms, Checkout, and Agentic Commerce

> **Part 3 of 4** of the *eCommerce and Payments Development* reference (plugin `ecommerce-development`), covering §9–§14. Sibling skills: `ecommerce-payments-architecture-and-integration` (§0–§4), `ecommerce-payment-methods-sca-fraud-and-pci` (§5–§8), `ecommerce-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> material in §8 → `ecommerce-payment-methods-sca-fraud-and-pci` and §11 tells you what to ask your counsel and your acquirer, not what
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
>    expensive one is decided in week one (§8 → `ecommerce-payment-methods-sca-fraud-and-pci`).

---

## §9. Subscriptions and Billing

**[DURABLE] Billing is where the interesting bugs live**, because it is a state machine
running unattended for years.

**The model**: customer → subscription → plan/price → invoice → payment attempt →
(success | dunning). **Proration** on mid-cycle changes is the classic source of
disagreement between your invoice and the customer's expectations — **decide the policy,
document it, and show the math on the invoice.**

**Dunning** — the retry sequence on failed payments — is directly revenue-relevant. **Smart
retry timing** (aligned with paydays and issuer behaviour) recovers materially more than
fixed daily retries. Combine with **card account updater**, pre-dunning notices before
expiry, and a clear in-product update path.

**⚠️ Involuntary churn — failed payments, not cancellations — is often the largest single
churn component, and it is the most tractable.** Teams obsess over the cancel flow and
ignore the retry logic.

**Also handle**: trials (and the conversion charge), **upgrade/downgrade proration**,
pausing, usage-based and metered billing (with idempotent usage records — double-counted
usage is a support nightmare), tax on recurring charges as the customer moves jurisdiction,
and **revenue recognition** (ASC 606 / IFRS 15 — cash received ≠ revenue recognized, and
your finance team needs the deferred-revenue schedule).

**⚠️ Make cancellation as easy as signup.** Beyond being decent, "negative option" and
click-to-cancel rules in several jurisdictions increasingly require it, and dark-pattern
cancellation flows are a regulatory and chargeback risk.

---

## §10. Marketplaces and Multi-Party Payments

**[DURABLE] The moment money flows to someone other than you, the compliance surface
changes dramatically.** You may be handling funds on behalf of third parties, which in many
jurisdictions is a regulated activity.

**The standard answer: use a PSP's multi-party product** (Stripe Connect, PayPal for
Marketplaces, Adyen for Platforms) so they carry the licensing, KYC/KYB, and payout
infrastructure. **Building this yourself means money-transmitter licensing in the US
(state by state) or a payment institution licence in the EU** — a multi-year, multi-million
undertaking that is almost never the right call.

**What you still own**: onboarding and **KYC/KYB** verification flows, the **split logic**
(platform fee, seller net, tax), **payout scheduling and reserves**, **negative balances**
(a seller refunds after you've paid them out — who eats it?), and **1099-K / DAC7 reporting**.

**⚠️ Chargeback liability in a marketplace is a contract question with a technical
implementation.** Decide explicitly whether the platform or the seller bears it, and build
the ledger to reflect that decision.

---

## §11. Tax and Cross-Border

**[DURABLE] Sales tax is far harder than engineers expect, and it is a genuine liability
rather than a rounding concern.**

**US sales tax** post-*Wayfair* is **economic nexus**: you may owe in a state where you have
no physical presence, based on revenue or transaction thresholds that **vary by state**.
Roughly 11,000+ taxing jurisdictions, product-level taxability rules (is a digital download
taxable? is a candy bar food?), and origin- vs. destination-based sourcing.
**EU VAT**: destination-based for B2C digital services, with **OSS/IOSS** simplifying
registration; **reverse charge** for B2B with a valid VAT number (**validate it — VIES**).
Plus GST regimes in dozens of other countries with their own thresholds.

**[DURABLE] Use a tax engine** — Avalara, Vertex, Stripe Tax, TaxJar, Anrok. Hardcoded tax
rates are a liability, not a shortcut. **Or use a merchant of record (§4.1 → `ecommerce-payments-architecture-and-integration`) and make it
their problem** — which for small teams selling digital goods internationally is often the
correct engineering decision dressed as a commercial one.

**Cross-border also means**: customs and duties (**DDP vs. DDU** — surprise duty bills at
delivery are a top cause of refused deliveries and chargebacks), **restricted and sanctioned
parties screening**, local consumer-protection and returns law (the EU's 14-day withdrawal
right), data residency, and **currency**: present prices in local currency, decide who bears
FX risk, and note that **dynamic currency conversion is generally bad for the customer and
a conversion killer**.

**[VERSIONED] The European Accessibility Act's requirements for e-commerce services became
enforceable on 28 June 2025** — for services in scope, accessibility is now a legal
obligation in the EU, not a nice-to-have. Verify scope and exemptions for your business.

---

## §12. The Platform Layer

### 12.1 Build vs. buy

**[DURABLE] The honest default for most businesses is a SaaS platform**, and teams
routinely underestimate what they're rebuilding: catalog, variants, pricing rules,
promotions, cart, checkout, payments, tax, shipping rate calculation, order management,
returns, admin tooling, and the reporting the business will ask for in month three.

| Option | Fits |
|---|---|
| **Shopify (+ Plus)** | Most DTC and mid-market. Enormous app ecosystem; **Shopify Payments' rates and the fee for using an external gateway are a real cost input** |
| **BigCommerce, Wix, Squarespace** | SMB to mid-market, varying by catalog complexity |
| **Adobe Commerce / Magento** | Large, complex catalogs and B2B; heavy to run |
| **Salesforce Commerce Cloud, SAP, Oracle** | Enterprise, deep ERP integration |
| **WooCommerce** | WordPress-native, cheap to start, yours to operate |
| **Commercetools, Elastic Path, Medusa, Saleor** | **Headless/composable** — API-first, you build the front end |
| **Custom** | Genuinely unusual models. **Rarely justified by "our business is special"** |

### 12.2 Headless and composable

**[CONTESTED]** *For*: front-end freedom, multi-channel (web, app, kiosk, agent), best-of-
breed components, better performance ceiling. *Against*: **you now own the integration
layer**, which is a permanent team cost; more services to operate; and you lose the
monolith's out-of-the-box admin. **The honest test: are you actually constrained by the
templating layer, or do you just want a nicer stack?** Composable makes sense at scale and
with a platform team; it is frequently a costly aesthetic choice below that.

**[DURABLE] Whatever you choose, the storefront's job is speed.** Core Web Vitals affect
both ranking and conversion, and the highest-leverage work is usually image optimization,
reducing third-party scripts (which is also §8.3 → `ecommerce-payment-methods-sca-fraud-and-pci`'s security advice), and caching strategy.

---

## §13. Catalog, Cart, and Checkout

### 13.1 The data model

**Products vs. variants** is the modelling decision everything else hangs off. A "product"
with options (size, colour) has **variants** as the actual sellable units with their own
SKU, price, and inventory. **⚠️ Getting this wrong forces a painful migration**, because
carts, orders, and inventory all reference the wrong grain.

**Inventory**: track available-to-promise, not just on-hand. **Decide when you reserve** —
at cart (protects the customer, risks hoarding), at checkout start (a reasonable middle),
or at order (risks overselling). **Multi-location inventory and backorders** turn this into
a real allocation problem.

**Pricing and promotions** get complicated faster than any other area: price lists,
customer-group pricing, quantity breaks, currency-specific prices, and **stacking rules for
discounts** (order of application changes the total — decide and document it). **⚠️ Test
promotion logic adversarially**; discount stacking is a business-logic vulnerability and
promo abuse is a real fraud category (§7.1 → `ecommerce-payment-methods-sca-fraud-and-pci`).

### 13.2 Checkout

**[DURABLE] Checkout conversion is where the money is, and the levers are well-established:**
guest checkout (**forced account creation is among the most reliably damaging choices you
can make**), minimal fields with sensible autofill and address autocomplete, **wallets
surfaced early** (Apple/Google Pay skip the form entirely), **all costs shown before the
final step** — surprise shipping and tax at the last screen is the top cited abandonment
reason — a visible progress indicator, inline validation, trust signals, and a mobile
experience designed first rather than adapted.

**Accessibility is a conversion feature and, increasingly, a legal requirement** (§11) —
keyboard navigation, labelled inputs, sufficient contrast, and screen-reader-usable error
messages.

**⚠️ The webhook, not the redirect, confirms the order** (§3.2 → `ecommerce-payments-architecture-and-integration`). Design the post-payment
experience so a customer who closes the tab still gets their order.

---

## §14. Agentic Commerce

**[VERSIONED — the newest layer here, moving fast, and full of premature certainty.]**

### 14.1 What it is

AI agents completing purchases on a user's behalf, which breaks the classic model where **a
human clicks buy on a trusted page**. That assumption underpins fraud liability, SCA, and
dispute rights, so the protocols exist mainly to answer: **how does the merchant know this
agent is authorized, and who is accountable when it goes wrong?**

### 14.2 The standards contest

| Protocol | Origin | Layer |
|---|---|---|
| **ACP** (Agentic Commerce Protocol) | **OpenAI + Stripe**, Sept 2025, Apache 2.0 | Agent-to-merchant **checkout**; shared payment tokens |
| **UCP** (Universal Commerce Protocol) | **Google + Shopify**, announced at NRF Jan 2026 | Full journey — **discovery through post-purchase** |
| **AP2** (Agent Payments Protocol) | **Google**, 60+ partners; **donated to the FIDO Alliance 28 April 2026** with v0.2 | **Authorization and accountability** — cryptographically signed mandates / verifiable credentials |
| **x402** | Coinbase | HTTP 402 revival for **stablecoin machine-to-machine micropayments** |
| **MPP** (Machine Payments Protocol) | Stripe + Tempo, **18 March 2026** | Agent pre-authorizes a spending limit, streams micropayments |
| **Visa Trusted Agent Protocol / Mastercard Agent Pay** | The networks | Agent-scoped tokenization on existing rails |

**⚠️ These are not interchangeable and they sit at different layers.** A plausible reading
of where it settles: **UCP-style discovery and cart standards, AP2-style verifiable
authorization underneath, and execution layers each major AI surface adopts its own way.**

### 14.3 The reality check

**⚠️ The obvious narrative is wrong in an instructive way. OpenAI's Instant Checkout —
the launch product for ACP, which put ChatGPT purchasing in front of the largest consumer
AI audience — was retired on 5 March 2026**, after roughly thirty Shopify merchants
integrated, with OpenAI pivoting to retailer-operated ChatGPT Apps. And **Forrester's data
shows US consumer adoption of Instant Checkout remained low and stagnant from debut to
discontinuation**; interest in AI agents making purchases is growing but described as
lukewarm.

**[CONTESTED] So: is this real?** *For building now*: the infrastructure investment from
Stripe, Google, Shopify, Visa, Mastercard and PayPal is enormous, the standards are
consolidating rather than proliferating, and being invisible to agent-mediated discovery is
a genuine risk if it lands. *Against*: consumer demand has not yet materialized, the
flagship implementation was withdrawn within six months, and the protocols are still
churning — **ACP's own spec history shows five revisions between September 2025 and April
2026.**

**[DURABLE] The advice that holds either way is not really about agents:** the thing that
makes you legible to an AI agent is **clean, accurate, machine-readable product data** —
precise titles, real-time stock and pricing, clear specs, standards-based schema, and a
catalog API that doesn't require executing your JavaScript. **That work pays off in search,
in marketplaces, in feeds, and in agent surfaces alike**, which makes it the rare hedge
with no downside. **Adopt a payment standard rather than building your own agent-payment
flow** — rolling your own means inheriting all the fraud liability yourself.

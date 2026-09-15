---
name: ecommerce-reference
description: "Use when reviewing a commerce or payments system for known anti-patterns (double charges, lost orders, silent revenue leaks), weighing contested questions (platform vs headless vs custom, one PSP or several, merchant of record vs doing it yourself, how aggressive to be on fraud, whether agentic commerce is real yet, when to reserve inventory, building a ledger vs trusting PSP reporting), checking whether a regulatory or platform claim is still current (snapshot verified August 2026), finding primary documentation and books, or needing the numbers, payment integration checklist, and triage. Companion to the other ecommerce-development skills."
---

# eCommerce & Payments: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 4 of 4** of the *eCommerce and Payments Development* reference (plugin `ecommerce-development`), covering §15–§20. Sibling skills: `ecommerce-payments-architecture-and-integration` (§0–§4), `ecommerce-payment-methods-sca-fraud-and-pci` (§5–§8), `ecommerce-billing-tax-platforms-and-checkout` (§9–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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
>    reconciliation (§3 → `ecommerce-payments-architecture-and-integration`) are not best practices — they are the load-bearing walls.**
> 3. **Your job is mostly to touch card data as little as possible.** PCI scope is a
>    function of architecture, and the difference between the easy compliance path and the
>    expensive one is decided in week one (§8 → `ecommerce-payment-methods-sca-fraud-and-pci`).

---

## §15. Anti-Patterns

| Anti-pattern | Why | Instead |
|---|---|---|
| Floating point for money | `0.1 + 0.2 != 0.3` → unexplainable discrepancies | Integer minor units or decimal (§2.2 → `ecommerce-payments-architecture-and-integration`) |
| Hardcoding `× 100` | JPY/KRW have 0 decimals; KWD/BHD have 3 | ISO 4217 exponent (§2.2 → `ecommerce-payments-architecture-and-integration`) |
| Amount column with no currency | Breaks on your first international order | Always store both |
| Treating authorization as payment | It can expire, fail at capture, or be voided | Fulfil on capture (§2.1 → `ecommerce-payments-architecture-and-integration`) |
| Leaving auths to expire instead of voiding | The customer's money stays held | Void explicitly (§2.1 → `ecommerce-payments-architecture-and-integration`) |
| Random UUID as the idempotency key | Regenerated on retry → no protection at all | Derive from the business action, persist before calling (§3.1 → `ecommerce-payments-architecture-and-integration`) |
| Fulfilling on the redirect URL | Customer closes the tab; order lost | **Webhook is the source of truth** (§3.2 → `ecommerce-payments-architecture-and-integration`) |
| Non-idempotent webhook handler | Same event delivered 3× in 60s is documented | Unique constraint on event ID (§3.2 → `ecommerce-payments-architecture-and-integration`) |
| Returning 200 before processing | Event lost, no retry | 200 immediately, process async, but only after durably recording it |
| Handling only the happy path | `invoice.paid` without `invoice.payment_failed` = silent revenue leak | Handle failures (§3.2 → `ecommerce-payments-architecture-and-integration`) |
| Treating a 500/timeout as failure | The result is **indeterminate** | Retry with the same key; reconcile (§3.4 → `ecommerce-payments-architecture-and-integration`) |
| Retrying hard declines | Futile and a compliance problem | Soft only (§6.2 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| No reconciliation job | Divergence found by an auditor, not by you | Nightly reconciliation (§3.3 → `ecommerce-payments-architecture-and-integration`) |
| No ledger, or a mutable one | Partial refunds and disputes destroy it | Append-only double-entry, from day one (§3.3 → `ecommerce-payments-architecture-and-integration`) |
| External payment call inside a DB transaction | Locks held across a network call of unknown outcome | Call first, then record (§1.3 → `ecommerce-payments-architecture-and-integration`) |
| Boolean flags instead of an order state machine | Collapses on partial refunds/shipments | Explicit states and transitions (§1.2 → `ecommerce-payments-architecture-and-integration`) |
| Card data touching your servers or logs | Puts your whole stack in PCI scope | Hosted fields/iframe; store tokens (§8.1 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Assuming the SAQ A change reduced your obligations | **The criterion now covers your entire site, not just the payment page** | Read §8.2 → `ecommerce-payment-methods-sca-fraud-and-pci`. Confirm eligibility or file SAQ A-EP |
| Loading many third-party scripts on checkout | Every tag is a Magecart vector on your highest-value page | Minimize; CSP + SRI (§8.3 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Optimizing fraud rules on chargeback rate alone | False positives are invisible and expensive | Measure both error types (§7.1 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Vague billing descriptor | A large share of disputes is "I don't recognize this" | Recognizable descriptor (§7.2 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Ignoring involuntary churn | Often the largest churn component | Smart dunning + account updater (§9 → `ecommerce-billing-tax-platforms-and-checkout`) |
| Hard-to-cancel subscriptions | Chargebacks, and a growing regulatory problem | Cancel as easily as signup (§9 → `ecommerce-billing-tax-platforms-and-checkout`) |
| Building marketplace payouts yourself | Money transmission licensing | Use a multi-party PSP product (§10 → `ecommerce-billing-tax-platforms-and-checkout`) |
| Hardcoded tax rates | A liability, not a shortcut | Tax engine, or a merchant of record (§11 → `ecommerce-billing-tax-platforms-and-checkout`) |
| Surprise costs at the final checkout step | Top cited abandonment cause | Show all costs early (§13.2 → `ecommerce-billing-tax-platforms-and-checkout`) |
| Forced account creation | Among the most damaging checkout choices | Guest checkout (§13.2 → `ecommerce-billing-tax-platforms-and-checkout`) |
| One payment method for every market | Silently caps conversion abroad | Localize the method mix (§5.2 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Never measuring authorization rate | Usually worth more than front-end CVR work | Instrument it (§6.2 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Building a bespoke agent-payment flow | You inherit all the fraud liability | Adopt a standard (§14.3 → `ecommerce-billing-tax-platforms-and-checkout`) |
| Assuming sandbox behaviour equals production | Latency, declines, webhook timing all differ | Budget for live-traffic surprises (§4.2 → `ecommerce-payments-architecture-and-integration`) |
| Committing an API key "temporarily" | Assume compromised the moment it lands | Rotate immediately; secrets manager (§3.4 → `ecommerce-payments-architecture-and-integration`) |

---

## §16. Contested Questions

**16.1 Platform vs. headless vs. custom.** §12 → `ecommerce-billing-tax-platforms-and-checkout`. The genuine test is whether the templating
layer is actually constraining you, and whether you have a team to own the integration
layer permanently.

**16.2 One PSP or several.** *Single*: simpler, better rates through volume, one
reconciliation. *Multiple (via orchestration)*: redundancy if a provider has an incident or
freezes your account, better auth rates via routing, and negotiating leverage. **The
break-even is lower than most teams assume once payment volume is material** — but the
operational cost of two reconciliations is real.

**16.3 Merchant of record vs. doing it yourself.** §4.1 → `ecommerce-payments-architecture-and-integration`, §11 → `ecommerce-billing-tax-platforms-and-checkout`. Higher rate versus owning
global tax registration and remittance. **For a small team selling digital goods
internationally, MoR is frequently the correct answer** and is dismissed too quickly on
headline rate alone.

**16.4 How aggressive to be on fraud.** §7.1 → `ecommerce-payment-methods-sca-fraud-and-pci`. There is no neutral setting; you are choosing
where to sit on a curve with two costs.

**16.5 Is agentic commerce real yet?** §14.3 → `ecommerce-billing-tax-platforms-and-checkout` — and the evidence genuinely cuts both ways.
The infrastructure is being built at enormous scale; the flagship consumer implementation
was withdrawn six months after launch with low, stagnant adoption.

**16.6 Reserve inventory when?** Cart, checkout start, or order. Customer experience versus
overselling risk versus hoarding. **Genre-dependent**: limited-drop retail and grocery want
opposite answers.

**16.7 Build a ledger, or trust the PSP's reporting?** *PSP*: less to build; they're the
system of record for money that moved. *Own ledger*: multi-PSP, multi-currency, marketplace
splits, and auditability all need it. **The threshold at which you need your own is lower
than it feels — and retrofitting is brutal (§3.3 → `ecommerce-payments-architecture-and-integration`).**

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **PCI DSS v4.0.1** | ⚠️ **All 51 future-dated requirements became mandatory 31 March 2025.** No remaining transition phase; **v4.0.1 is the only active version**. Key e-commerce ones: **6.4.3** (payment page scripts authorized, integrity-checked, inventoried) and **11.6.1** (change/tamper detection, evaluated **at least weekly**) | Low |
| **The SAQ A change** | ⚠️ **January 2025: PCI SSC removed 6.4.3, 11.6.1, and 12.3.1 from SAQ A** — and added an **eligibility criterion** that the merchant confirm **"their site is not susceptible to attacks from scripts that could affect the merchant's e-commerce system(s)."** **Scope widened from the payment page to the entire website.** Merchants using redirects, previously out of scope, must now verify all scripts. **Cannot confirm it → not SAQ A eligible → SAQ A-EP.** October 2024 SAQ A retired 31 Mar 2025; January 2025 (r1) took effect same day. **28 Feb 2025 FAQ** gives two routes: implement the controls anyway, or get **written confirmation from a compliant third-party provider** | Medium |
| **PSD3 / PSR** | Provisional political agreement **27 November 2025**; final compromise texts agreed **~22–23 April 2026**. ⚠️ **Application dates are reported inconsistently** — sources cite PSR applying **18, 21, or 27 months** after entry into force, with "realistic compliance" placed variously at **late 2027, Q1 2028, or Q2/Q3 2028**; **Verification of Payee provisions generally later (~27 months)**. **Verify against the Official Journal text** | **High** |
| **What PSD3/PSR changes** | Merges PSD2 and EMD2; **PSR is directly applicable** (removes cross-member-state variation). **Fraud liability shifts** — PSPs liable where prevention is inadequate; **APP fraud treated as unauthorized** with reimbursement; **impersonation/spoofing refund right**; mandatory **transaction monitoring**; PSPs may share IBAN fraud data. **⚠️ Delegating SCA to a third party is formal outsourcing** → EBA outsourcing guidelines + DORA | Medium |
| **3-D Secure** | **The protocol itself is not changing** under PSD3/PSR. Expect **expanded SCA triggers** (new token creation, spending-limit changes) | Medium |
| **Verification of Payee** | ⚠️ **Already mandatory since 9 October 2025** for euro-area PSPs under the separate **Instant Payments Regulation** (non-euro-area by **July 2027**). **PSD3/PSR did not create it** — it extends it to all credit transfers, any currency. Common point of confusion | Low |
| **European Accessibility Act** | **Enforceable since 28 June 2025** for in-scope services including e-commerce | Low |
| **Agentic: ACP** | **OpenAI + Stripe, 29 Sept 2025**, Apache 2.0, jointly governed with a stated path to broader community governance. **Spec revisions: 2025-09-29, 2025-12-12, 2026-01-16, 2026-01-30, 2026-04-17** — five in seven months | **High** |
| **Agentic: the plot twist** | ⚠️ **OpenAI Instant Checkout was retired 5 March 2026** after ~30 Shopify merchants integrated; OpenAI pivoted to **retailer-operated ChatGPT Apps**. **Forrester: US consumer adoption was low and stagnant from debut to discontinuation** | **High** |
| **Agentic: UCP** | **Google + Shopify**, unveiled at **NRF January 2026**; April 2026 release expanded partners past twenty. Covers **discovery through post-purchase** | **High** |
| **Agentic: AP2** | **Donated to the FIDO Alliance 28 April 2026** alongside **v0.2**; 60 organizations contributed; Verifiable Intent co-developed with Mastercard. Focus: **authorization, authenticity, accountability** via signed mandates | **High** |
| **Agentic: others** | **x402** (Coinbase) V2 Dec 2025; **Stripe integrated x402 on Base Feb 2026** (preview, USDC on Base/Solana/Tempo). **MPP** (Stripe + Tempo) launched **18 March 2026** with a spending-limit "sessions" model. **Visa Trusted Agent Protocol** and **Mastercard Agent Pay** extend network tokenization | **High** |
| **Stripe API** | Versions pinned per account/request; dated version strings (e.g. `2026-07-29.dahlia`). **Checkout Sessions is the currently recommended path.** Webhook retries **up to ~72 hours**; **idempotency results cached 24 hours** | Medium |
| **Scale anchor** | An industry summary reported **Stripe processed ~$1.9 trillion in total payment volume in 2025** | Annual |

**Goes stale fastest:** the agentic protocol landscape (everything in it); PSD3/PSR dates;
PSP API versions. **Essentially never stale:** §2 → `ecommerce-payments-architecture-and-integration` (the payment lifecycle), §3 → `ecommerce-payments-architecture-and-integration`
(idempotency, webhooks, reconciliation), §2.2 → `ecommerce-payments-architecture-and-integration` (money handling), §7.1 → `ecommerce-payment-methods-sca-fraud-and-pci`, §13.2 → `ecommerce-billing-tax-platforms-and-checkout`, §15.

---

## §18. The Canon

### 18.1 Primary documentation — read these directly
- **Stripe Docs** — genuinely the best payments documentation in existence, and useful even
  if you use another provider. Specifically: the **idempotency**, **advanced error
  handling**, and **webhook** pages, and **stripe.com/blog/idempotency** (a foundational
  essay on designing robust APIs).
- **PCI Security Standards Council** — the **Document Library** (PCI DSS v4.0.1, the SAQs),
  the **blog** (where the SAQ A changes and FAQs were announced), and the **E-commerce
  Guidance** from the task force.
- **PayPal Developer**, **Adyen Docs** (excellent on local payment methods and auth-rate
  optimization), **Braintree**, **Shopify Dev** (Admin and Storefront APIs, Functions).
- **EMVCo** for 3-D Secure specifications; **EBA** guidelines and **RTS on SCA**;
  the **Official Journal** for PSD3/PSR once published.
- **Agentic Commerce Protocol** (`agenticcommerce.dev`, and the spec repo),
  **AP2** via the FIDO Alliance, **UCP**.
- **ISO 20022** documentation and your specific scheme's migration guidance (§5.3 → `ecommerce-payment-methods-sca-fraud-and-pci`).

### 18.2 Books and long-form
| Author | Work | Why |
|---|---|---|
| **Pethuru Raj / various** | — | *(payments has no single canonical textbook — this is a docs-first field)* |
| **Baymard Institute** | Checkout and e-commerce UX research | **The empirical reference for §13.2 → `ecommerce-billing-tax-platforms-and-checkout`.** Their cart-abandonment and checkout-usability studies are the actual data behind most conversion advice |
| **Sam Newman** | *Building Microservices* | §1.3 → `ecommerce-payments-architecture-and-integration`'s sagas, outbox, and consistency patterns |
| **Martin Kleppmann** | ***Designing Data-Intensive Applications*** | The distributed-systems reasoning under §3 → `ecommerce-payments-architecture-and-integration` |
| **Martin Fowler** | *Patterns of Enterprise Application Architecture*; the **Money pattern** and **Ledger/Event Sourcing** material on martinfowler.com | §2.2 → `ecommerce-payments-architecture-and-integration` and §3.3 → `ecommerce-payments-architecture-and-integration` |
| **Gregor Hohpe & Bobby Woolf** | *Enterprise Integration Patterns* | Still the reference for webhook/messaging design |
| **"Payments Systems in the U.S."** (Carol Coye Benson et al.) | — | The clearest plain-English explanation of how the rails actually work |

### 18.3 Sites and people
**Baymard Institute** (checkout research), **Patrick McKenzie / patio11** (`kalzumeus.com`
and Bits about Money — **the best writing anywhere on how payments actually work
commercially**), **Stripe's engineering blog**, **Adyen's technical blog**,
**a16z fintech** and **Fintech Brainfood** (Simon Taylor) for market structure,
**The Paypers** and **PYMNTS** for industry news, **Merchant Risk Council** for fraud and
disputes, **Nilson Report** for card industry data, and **DefiLlama-style** trackers on the
crypto side. **OWASP** for the application-security layer of checkout.

---

## §19. Quick Reference

### 19.1 Numbers
- Card authorization holds: **~7 days** typical, varies by network and method.
- Settlement: **T+1 to T+3** typical.
- Stripe webhook retries: **up to ~72 hours**; **respond within ~30s**.
- Stripe idempotency cache: **24 hours**.
- ACH consumer reversals: **up to 60 days**. SEPA DD refund right: **8 weeks**.
- PCI DSS v4.0.1 future-dated requirements mandatory: **31 March 2025**.
- Requirement **11.6.1** tamper detection: evaluate **at least weekly**.
- Verification of Payee (euro-area, instant): **since 9 October 2025**.
- European Accessibility Act: **enforceable since 28 June 2025**.
- Currency decimals: **JPY/KRW = 0 · most = 2 · KWD/BHD/JOD = 3**.

### 19.2 Payment integration checklist
- [ ] Idempotency key on every mutating call, **derived from the business action and
      persisted before the call**
- [ ] Webhook signature verified against the **raw body**
- [ ] Webhook handler deduplicates on event ID with a **unique constraint**
- [ ] 200 returned fast; work done async; failures return non-2xx so retries happen
- [ ] Dead-letter queue for repeatedly failing events
- [ ] **Fulfilment triggered by webhook, never by redirect**
- [ ] Failure events handled, not just success events
- [ ] 5xx/timeouts treated as indeterminate and reconciled
- [ ] Nightly reconciliation job against the processor
- [ ] Append-only ledger recording every money movement
- [ ] Amounts in minor units with currency; ISO 4217 exponents respected
- [ ] Auths voided rather than left to expire
- [ ] No PAN, CVV, or secret in any log, ever
- [ ] Payment endpoints rate-limited against card testing
- [ ] Billing descriptor recognizable to a human
- [ ] Authorization rate instrumented and monitored
- [ ] PCI SAQ type confirmed — **including SAQ A eligibility under the 2025 criterion**

### 19.3 Triage
| Symptom | First look |
|---|---|
| Customer charged twice | Idempotency key regenerated on retry (§3.1 → `ecommerce-payments-architecture-and-integration`) |
| Order paid but never created | Fulfilment on redirect instead of webhook (§3.2 → `ecommerce-payments-architecture-and-integration`) |
| Duplicate fulfilment / double provisioning | Non-idempotent webhook handler (§3.2 → `ecommerce-payments-architecture-and-integration`) |
| Revenue quietly lower than expected | Unhandled `payment_failed` events; dunning (§3.2 → `ecommerce-payments-architecture-and-integration`, §9 → `ecommerce-billing-tax-platforms-and-checkout`) |
| Your totals ≠ processor's totals | No reconciliation; rounding allocation; fees (§2.2 → `ecommerce-payments-architecture-and-integration`, §3.3 → `ecommerce-payments-architecture-and-integration`) |
| Auth rate dropped | Card-on-file expiry, missing network tokens, routing change, 3DS config (§6.2 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Conversion drops in one country | Wrong payment methods for that market (§5.2 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Chargebacks rising | Descriptor recognition, delivery evidence, subscription notices (§7.2 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Failed a PCI assessment on scope | Card data or scripts touching systems you thought were out of scope (§8 → `ecommerce-payment-methods-sca-fraud-and-pci`) |
| Checkout abandonment spike at the last step | Surprise shipping/tax/duty (§13.2 → `ecommerce-billing-tax-platforms-and-checkout`, §11 → `ecommerce-billing-tax-platforms-and-checkout`) |
| Cents missing on multi-item orders | Rounding allocation across line items (§2.2 → `ecommerce-payments-architecture-and-integration`) |

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. The durable material — §1 → `ecommerce-payments-architecture-and-integration` (architecture),
§2 → `ecommerce-payments-architecture-and-integration` (payment lifecycle), §3 → `ecommerce-payments-architecture-and-integration` (integration engineering), §7.1 → `ecommerce-payment-methods-sca-fraud-and-pci`, §9 → `ecommerce-billing-tax-platforms-and-checkout`, §13.2 → `ecommerce-billing-tax-platforms-and-checkout`, §15 — rests on
distributed-systems fundamentals, provider documentation that has been stable for years,
and failure patterns reported consistently across practitioners. Every **time-sensitive**
claim (PCI deadlines, PSD3/PSR timing, agentic protocol state, API behaviour) was verified
against a primary or near-primary source in **August 2026** and is flagged in §17 with a
decay-risk rating. Where sources conflict — notably PSD3/PSR application dates — **the
conflict is reported rather than resolved**.

**Search log** (August 2026): PCI DSS 4.0.1 e-commerce requirements and the SAQ A changes ·
agentic commerce protocols (ACP, AP2, UCP, x402, MPP) and adoption · PSD3/PSR timeline,
SCA, and Verification of Payee · payment integration engineering (idempotency, webhooks,
reliability).

**Primary and near-primary sources consulted (selected):**
- **PCI Security Standards Council blog** — "Important Updates Announced for Merchants
  Validating to SAQ A" (Jan 2025), the **28 Feb 2025 FAQ** on the new eligibility criterion,
  and the Coffee with the Council episode on post-31-March-2025 e-commerce guidance;
  plus **TrustedSec**, **Akamai**, **SecurityMetrics**, and **Feroot** on the practical
  implications and the SAQ A eligibility trap
- **Stripe documentation** — idempotent requests, advanced error handling, server-side
  integration, and the agentic commerce materials; **agenticcommerce.dev** and the **ACP
  spec repository** for the revision history
- **Forrester** ("Agentic Payments In B2C Commerce: Where We Are Now") on Instant Checkout
  adoption; multiple independent reports on its **5 March 2026** retirement and the **AP2
  → FIDO Alliance donation (28 April 2026)**
- **Morrison Foerster**, **Arthur Cox**, **Norton Rose Fulbright**, **Herbert Smith
  Freehills Kramer**, **PwC Legal**, and **Worldline** on PSD3/PSR scope and timing;
  **openbankingtracker** and **GR4VY** on the developer-facing implications and the
  VoP/Instant Payments Regulation distinction
- Practitioner write-ups on webhook and idempotency failure modes, including documented
  cases of triple event delivery and the resulting double-provisioning

**Confidence statement.** **High confidence** in §2 → `ecommerce-payments-architecture-and-integration`, §3 → `ecommerce-payments-architecture-and-integration`, §5.1 → `ecommerce-payment-methods-sca-fraud-and-pci`–5.2, §7 → `ecommerce-payment-methods-sca-fraud-and-pci`, §9 → `ecommerce-billing-tax-platforms-and-checkout`, §13 → `ecommerce-billing-tax-platforms-and-checkout` and §19's
integration guidance — these rest on provider documentation, distributed-systems
fundamentals, and failure modes reported consistently by many independent practitioners.
**High confidence** in the PCI DSS dates and the substance of the SAQ A change, which come
from the PCI SSC's own announcements and FAQ. **Low-to-moderate confidence on PSD3/PSR
application dates specifically** (§17): six credible law-firm and industry sources give
materially different figures — 18, 21, and 27 months post-entry-into-force, and "realistic"
dates from late 2027 through Q2/Q3 2028 — because the texts were still in legal-linguistic
review and Official Journal publication timing was unsettled at the time of writing.
**I have reported the spread; verify against the published text before making a compliance
plan.** **Moderate confidence on §14 → `ecommerce-billing-tax-platforms-and-checkout`'s agentic landscape**: it is the fastest-moving
material here, much of it comes from vendor announcements and trade coverage with obvious
promotional incentives, and I have deliberately foregrounded the disconfirming evidence
(the Instant Checkout retirement, Forrester's adoption data) because the promotional
material substantially outweighs it in volume. **The §5.3 → `ecommerce-payment-methods-sca-fraud-and-pci` note on ISO 20022 is deliberately
undated** — migration deadlines differ by scheme and I did not verify them; check your
specific rail. Nothing here is legal, tax, or financial advice; §8 → `ecommerce-payment-methods-sca-fraud-and-pci` and §11 → `ecommerce-billing-tax-platforms-and-checkout` identify the
questions to put to your counsel and acquirer, not the answers.

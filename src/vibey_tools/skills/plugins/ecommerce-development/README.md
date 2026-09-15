# eCommerce and Payments Development Plugin

A deep technical reference for building commerce and payments systems: system architecture, the payment domain model from authorization through capture, settlement, and refunds, payment integration engineering (idempotency, webhooks, reconciliation, state machines), PSPs and gateways, payment methods and rails, SCA and 3-D Secure, authorization rates and decline handling, fraud and chargebacks, PCI DSS scope and the SAQ A trap, subscriptions and billing, marketplaces and payouts, tax and cross-border, the platform layer from Shopify to headless and custom builds, catalog, cart, and checkout conversion, and the emerging agentic commerce protocols. It is an engineering document, not legal, tax, or financial advice.

One reference, split into 4 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (verified August 2026) flags what goes stale first.

## Skills

- **ecommerce-payments-architecture-and-integration** — Architecture, Payment Lifecycle, Integration Engineering, and PSPs (§0–§4): Routing; Architecture; The Payment Lifecycle; Integration Engineering; PSPs and the Platform Layer.
- **ecommerce-payment-methods-sca-fraud-and-pci** — Payment Methods, SCA and 3-D Secure, Fraud, and PCI DSS (§5–§8): Payment Methods and Rails; SCA, 3-D Secure, and Authorization Rates; Fraud and Disputes; PCI DSS and Security.
- **ecommerce-billing-tax-platforms-and-checkout** — Subscriptions, Marketplaces, Tax, Platforms, Checkout, and Agentic Commerce (§9–§14): Subscriptions and Billing; Marketplaces and Multi-Party Payments; Tax and Cross-Border; The Platform Layer; Catalog, Cart, and Checkout; Agentic Commerce.
- **ecommerce-reference** — Anti-Patterns, Contested Questions, Currency, and Canon (§15–§20): Anti-Patterns; Contested Questions; Currency Snapshot; The Canon; Quick Reference; Sources and Method.

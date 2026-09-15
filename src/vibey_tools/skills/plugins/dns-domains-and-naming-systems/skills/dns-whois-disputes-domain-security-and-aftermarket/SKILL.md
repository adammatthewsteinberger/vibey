---
name: dns-whois-disputes-domain-security-and-aftermarket
description: "Use for domain ownership questions: WHOIS and RDAP and how GDPR changed what is visible, disputes including UDRP and URS and how they actually resolve, domain security covering registrar lock, transfer authorization, hijacking and expiry, and the aftermarket for valuing, buying and selling domains."
---

# DNS and Domain Names: WHOIS and RDAP, Disputes, Domain Security, and the Aftermarket

> **Part 4 of 6** of the *DNS, Domain Names and Naming Systems* reference (plugin `dns-domains-and-naming-systems`), covering §17–§20. Sibling skills: `dns-namespace-resolution-records-and-zones` (§0–§5), `dns-attacks-dnssec-encrypted-dns-and-operations` (§6–§12), `dns-icann-tlds-registries-and-registration` (§13–§16), `dns-blockchain-naming-alternatives-assessed` (§21–§25), `dns-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** DNS itself is stable. Two things moved. See §26 → `dns-reference` for ICANN's first new gTLD round since 2012, and the retreat of blockchain naming.

> **⚠️ The layer that turns names humans can remember into addresses machines can route —
> and the most successful distributed database ever built, running on a design from 1983.**
>
> **Complements a communications reference (email depends on MX and §5 → `dns-namespace-resolution-records-and-zones`'s DNS records), a
> cryptography reference (DNSSEC signing, certificate issuance), and a computer-hardware
> reference (networking).**
>
> **⚠️ GOTCHA** boxes mark where the mental model people carry is wrong in ways that cause
> outages.
>
> **The three ideas that organize this document:**
> 1. **⚠️ DNS IS A DELEGATION HIERARCHY, NOT A DIRECTORY** (§2 → `dns-namespace-resolution-records-and-zones`, §5 → `dns-namespace-resolution-records-and-zones`). **Nobody holds a list
>    of all domains. Each level delegates authority downward, and every resolution walks
>    that chain. Understanding delegation explains caching, propagation, DNSSEC and most
>    outages at once.**
> 2. **⚠️ CACHING IS WHY IT SCALES AND WHY IT SURPRISES YOU** (§6 → `dns-attacks-dnssec-encrypted-dns-and-operations`). **"DNS propagation" is
>    not a thing that happens. Old answers expire. The distinction determines what you can
>    and cannot fix quickly, and it is the single most common misunderstanding in
>    operations.**
> 3. **⚠️ A NAMESPACE NEEDS A SINGLE ROOT TO BE UNAMBIGUOUS** (§21 → `dns-blockchain-naming-alternatives-assessed`, §26.2 → `dns-reference`). **Every
>    alternative naming system faces the same problem: without one authoritative root, the
>    same name can mean different things to different software. This is not a political
>    objection to decentralization — it is what a name is for.**

---

## §17. ⚠️ WHOIS and RDAP

**⚠️ WHOIS was a 1980s directory of who runs what**, ⚠️ **originally a plain-text service
with no access control and no structure.**
**⚠️ GDPR changed everything in 2018**: ⚠️ **registrars redacted personal data en masse
because publishing it was unlawful, and ICANN's Temporary Specification became the interim
regime.**
**⚠️ The competing interests are genuine on both sides**: ⚠️ **registrant privacy and safety
versus law enforcement, security research, anti-abuse work and trademark enforcement —
⚠️ and the researchers' complaint that abuse investigation got materially harder is
substantiated, as is the privacy case.**
**⚠️ RDAP** is the structured replacement: ⚠️ **JSON over HTTPS with AUTHENTICATED
differentiated access, so accredited requesters can see more than the public — which is the
architectural answer to the tiered-access problem WHOIS could not express.**
**⚠️ Privacy/proxy services** sit in front of registrations, ⚠️ **and note the risk that a
proxy service is the legal registrant of record.**

---

## §18. Disputes

**⚠️ UDRP** is the main mechanism: ⚠️ **the complainant must show a confusingly similar mark,
no legitimate interest by the holder, AND registration and use in BAD FAITH — all three.**
⚠️ **Remedies are transfer or cancellation only; no damages.**
**⚠️ URS** is the faster, cheaper, higher-standard alternative for new gTLDs, ⚠️ **and it
only suspends rather than transfers.**
**⚠️ The rights protection mechanisms** around new TLD launches: ⚠️ **the Trademark
Clearinghouse, Sunrise registration, and Claims notices** (§26.1 → `dns-reference`).
**⚠️ REVERSE DOMAIN NAME HIJACKING** is the counterpart worth knowing — ⚠️ **a trademark
holder abusing the process against a legitimate registrant, and panels do find it.**
**⚠️ The honest observation**: ⚠️ **UDRP is faster and cheaper than litigation and has been
criticized for forum-shopping and complainant-favourable outcomes; ⚠️ generic-word domains
registered before a mark existed generally survive.**

---

## §19. ⚠️ Domain Security

```
⚠️ ⚠️ THE DOMAIN IS THE ROOT OF YOUR ONLINE IDENTITY. ⚠️ Whoever
   controls it can obtain certificates for it (§1), receive
   your email, pass password resets, and impersonate you
   completely. ⚠️ It deserves protection commensurate with that
⚠️ THE ATTACK PATHS, in rough order of prevalence
   ⚠️ 1. ⚠️ REGISTRAR ACCOUNT COMPROMISE  ⚠️ phishing, credential
      reuse, or social engineering the support desk
   ⚠️ 2. ⚠️ EXPIRY  ⚠️ the most common self-inflicted loss.
      ⚠️ Auto-renew plus a valid payment card plus a monitored
      contact address
   ⚠️ 3. ⚠️ DNS PROVIDER compromise or dangling delegation
   ⚠️ 4. ⚠️ SUBDOMAIN TAKEOVER  ⚠️ a CNAME points at a cloud
      resource you decommissioned; someone else claims that
      resource and now controls your subdomain. ⚠️ Extremely
      common, easy to scan for, and often uncleaned
   ⚠️ 5. Email compromise of the registrant contact
   ⚠️ 6. Registry-level attack (rare, catastrophic)
⚠️ ⚠️ THE DEFENCES, and they are cheap
   ⚠️ REGISTRAR LOCK and ⚠️ REGISTRY LOCK (⚠️ the latter requires
      out-of-band human verification to change anything — the
      single strongest control available and worth the fee for
      any significant domain)
   ⚠️ ⚠️ MFA on the registrar account, on a monitored address
   ⚠️ ⚠️ CAA RECORDS (§4) limiting who may issue certificates
   ⚠️ CERTIFICATE TRANSPARENCY MONITORING — ⚠️ you find out
      someone issued a cert for your name
   ⚠️ DNSSEC (§8) · expiry monitoring separate from the registrar
   ⚠️ ⚠️ AUDIT DANGLING DNS RECORDS regularly
```

---

## §20. The Aftermarket

**⚠️ Domains trade as assets**, ⚠️ **with a real secondary market, brokered sales and
auctions.**
**⚠️ Drop catching** — ⚠️ **specialized registrars competing for names at the instant of
deletion (§16 → `dns-icann-tlds-registries-and-registration`), which is an infrastructure arms race.**
**⚠️ Cybersquatting versus legitimate speculation** — ⚠️ **the legal line is §18's bad
faith, and registering generic words is not squatting.**
**⚠️ TYPOSQUATTING and combosquatting** are the abusive end, ⚠️ **and they underpin a large
share of phishing infrastructure.**
**⚠️ Expired-domain risk that people miss**: ⚠️ **a dropped domain retains inbound links,
residual traffic and — dangerously — any systems still configured to trust it, which is why
abandoned domains get re-registered maliciously.**

---

# PART III — ALTERNATIVES

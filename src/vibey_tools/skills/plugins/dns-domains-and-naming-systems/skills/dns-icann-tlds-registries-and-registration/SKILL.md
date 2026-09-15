---
name: dns-icann-tlds-registries-and-registration
description: "Use for how domain names are governed and sold: ICANN and control of the root zone, the TLD types across gTLD, ccTLD, sTLD and brand TLDs, the registry, registrar and registrant model and who actually holds what, and registration mechanics including EPP, grace periods, renewals and transfers."
---

# DNS and Domain Names: ICANN and the Root, TLD Types, the Registry / Registrar / Registrant Model, and Registration Mechanics

> **Part 3 of 6** of the *DNS, Domain Names and Naming Systems* reference (plugin `dns-domains-and-naming-systems`), covering §13–§16. Sibling skills: `dns-namespace-resolution-records-and-zones` (§0–§5), `dns-attacks-dnssec-encrypted-dns-and-operations` (§6–§12), `dns-whois-disputes-domain-security-and-aftermarket` (§17–§20), `dns-blockchain-naming-alternatives-assessed` (§21–§25), `dns-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §13. ⚠️ ICANN and the Root

**⚠️ ICANN** coordinates the DNS root, allocates TLDs, accredits registrars and administers
policy; ⚠️ **IANA (operated as PTI) performs the technical functions of the root zone.**
**⚠️ The IANA transition (2016)** ended US Commerce Department stewardship, ⚠️ **moving to a
multistakeholder accountability model — which is genuinely unusual as internet governance
goes and is regularly contested from several directions.**
**⚠️ The root zone** is small — ⚠️ **just the TLD delegations — and is signed with the root
KSK, whose ceremonies are conducted in public with published transcripts.** ⚠️ **The 2018
root KSK rollover was the first, and it was cautious precisely because a failure would have
been catastrophic** (§8 → `dns-attacks-dnssec-encrypted-dns-and-operations`).
**⚠️ The multistakeholder model** in practice: ⚠️ **GNSO, ccNSO, GAC (governments, advisory
not binding), ALAC, SSAC — and the criticisms worth knowing are process capture by industry,
glacial pace, and the persistent question of whether governments should have more than
advisory weight.**
**⚠️ Alternative roots have existed since the 1990s and have all failed** (§21 → `dns-blockchain-naming-alternatives-assessed`, §26.2 → `dns-reference`) —
⚠️ **which is the empirical backdrop to every proposal for a new one.**

---

## §14. TLD Types

**⚠️ gTLDs** — ⚠️ **the legacy set (.com, .org, .net, .info) plus over 1,200 delegated after
the 2012 round.**
**⚠️ ccTLDs** — ⚠️ **two-letter codes from ISO 3166-1, run under national policy rather than
ICANN contract, which is why their rules vary enormously.**
> **⚠️ GOTCHA — repurposed ccTLDs carry geopolitical risk that buyers systematically
> ignore.** ⚠️ **.io, .ai, .tv, .me and others are sold as generic and belong to actual
> territories, and territorial status changes have created real uncertainty for .io.**
> **⚠️ .su still exists for a state that does not. ⚠️ Building a brand on a ccTLD means
> accepting a sovereign decision you cannot appeal.**

**⚠️ Brand TLDs** (.google, .bmw) — ⚠️ **single-registrant, mostly used lightly, and a
defensive purchase as much as a product.**
**⚠️ Sponsored and restricted** (.edu, .gov, .mil, .bank) — ⚠️ **and their eligibility
requirements are exactly why they carry trust signal.**
**⚠️ IDN TLDs** in non-Latin scripts (§2 → `dns-namespace-resolution-records-and-zones`).
**⚠️ Special-use names** reserved by the IETF rather than delegated (§2 → `dns-namespace-resolution-records-and-zones`).

---

## §15. ⚠️ The Registry / Registrar / Registrant Model

```
⚠️ ⚠️ THREE DISTINCT PARTIES, and knowing which is which
   determines who you escalate to
   ⚠️ REGISTRY  ⚠️ operates the TLD and holds the authoritative
      database. ⚠️ One per TLD (Verisign for .com)
   ⚠️ REGISTRAR  ⚠️ sells to the public, accredited by ICANN,
      submits changes to the registry via EPP
   ⚠️ REGISTRANT  ⚠️ you
   ⚠️ RESELLERS sit under registrars and are NOT accredited —
      ⚠️ which matters when something goes wrong
⚠️ ⚠️ THE VERTICAL SEPARATION was mandated to prevent a registry
   favouring its own retail arm; ⚠️ it has since been relaxed
   for new gTLDs, and the concentration question recurs
⚠️ ⚠️ YOU DO NOT OWN A DOMAIN. ⚠️ You hold a renewable
   REGISTRATION — a contractual right of use. ⚠️ This is not
   pedantry: it determines what happens on expiry, on dispute
   (§18), and on registrar failure
⚠️ REGISTRY OPERATOR ECONOMICS  ⚠️ wholesale fee per domain per
   year, and .com pricing is set under a contract with ICANN
   that permits scheduled increases — ⚠️ a persistent source of
   complaint given the marginal cost of a database row
```

---

## §16. Registration Mechanics

**⚠️ EPP (Extensible Provisioning Protocol)** is how registrars talk to registries —
⚠️ **create, update, transfer, delete, and the authorization code that proves you may move a
domain.**
**⚠️ The lifecycle**: ⚠️ **available → registered → expired → AUTO-RENEW GRACE (~45 days,
recoverable at normal price) → REDEMPTION (~30 days, recoverable at a substantial fee) →
PENDING DELETE (5 days, nothing can be done) → dropped.**
⚠️ **Knowing this sequence is what lets you recover an accidentally lapsed domain — and
knowing the redemption fee is real is what motivates auto-renew.**
**⚠️ Transfers**: ⚠️ **unlock, get the auth code, initiate at the gaining registrar, approve;
⚠️ the 60-day lock after registration or a previous transfer is standard and catches
people mid-migration.**
**⚠️ Add Grace Period** and the historical abuse of it — ⚠️ **DOMAIN TASTING, registering in
bulk and refunding within five days, which was killed by making the refunds costly.**
**⚠️ ICANN fees, verification requirements** (⚠️ **failing to respond to a registrant
verification email suspends the domain, which surprises people**).

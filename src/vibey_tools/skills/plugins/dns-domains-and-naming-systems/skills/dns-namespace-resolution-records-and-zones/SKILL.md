---
name: dns-namespace-resolution-records-and-zones
description: "Use for how DNS actually works: what DNS is for beyond name-to-address mapping, the namespace and its hierarchy, resolution including recursive versus iterative and the resolver chain, the record types and what each is really used for, zones, delegation and the glue records that break things when wrong, and caching and TTL behaviour including negative caching. Includes the router for the whole DNS and domain names reference."
---

# DNS and Domain Names: What DNS Is For, the Namespace, Resolution, Record Types, Zones, Delegation and Glue, and Caching and TTL

> **Part 1 of 6** of the *DNS, Domain Names and Naming Systems* reference (plugin `dns-domains-and-naming-systems`), covering §0–§5. Sibling skills: `dns-attacks-dnssec-encrypted-dns-and-operations` (§6–§12), `dns-icann-tlds-registries-and-registration` (§13–§16), `dns-whois-disputes-domain-security-and-aftermarket` (§17–§20), `dns-blockchain-naming-alternatives-assessed` (§21–§25), `dns-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** DNS itself is stable. Two things moved. See §26 → `dns-reference` for ICANN's first new gTLD round since 2012, and the retreat of blockchain naming.

> **⚠️ The layer that turns names humans can remember into addresses machines can route —
> and the most successful distributed database ever built, running on a design from 1983.**
>
> **Complements a communications reference (email depends on MX and §5's DNS records), a
> cryptography reference (DNSSEC signing, certificate issuance), and a computer-hardware
> reference (networking).**
>
> **⚠️ GOTCHA** boxes mark where the mental model people carry is wrong in ways that cause
> outages.
>
> **The three ideas that organize this document:**
> 1. **⚠️ DNS IS A DELEGATION HIERARCHY, NOT A DIRECTORY** (§2, §5). **Nobody holds a list
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

## §0. Routing

| You want... | Go to |
|---|---|
| What DNS is for | §1 |
| The namespace | §2 |
| **⚠️ Resolution** | **§3** |
| Record types | §4 |
| **⚠️ Zones and delegation** | **§5** |
| **⚠️ Caching and TTL** | **§6 → `dns-attacks-dnssec-encrypted-dns-and-operations`** |
| **⚠️ Attacks on DNS** | **§7 → `dns-attacks-dnssec-encrypted-dns-and-operations`** |
| **⚠️ DNSSEC** | **§8 → `dns-attacks-dnssec-encrypted-dns-and-operations`** |
| **⚠️ Encrypted DNS** | **§9 → `dns-attacks-dnssec-encrypted-dns-and-operations`** |
| Modern extensions | §10 → `dns-attacks-dnssec-encrypted-dns-and-operations` |
| Operations | §11 → `dns-attacks-dnssec-encrypted-dns-and-operations` |
| DNS as infrastructure | §12 → `dns-attacks-dnssec-encrypted-dns-and-operations` |
| **⚠️ ICANN and the root** | **§13 → `dns-icann-tlds-registries-and-registration`** |
| TLD types | §14 → `dns-icann-tlds-registries-and-registration` |
| **⚠️ The registry model** | **§15 → `dns-icann-tlds-registries-and-registration`** |
| Registration mechanics | §16 → `dns-icann-tlds-registries-and-registration` |
| **⚠️ WHOIS and RDAP** | **§17 → `dns-whois-disputes-domain-security-and-aftermarket`** |
| Disputes | §18 → `dns-whois-disputes-domain-security-and-aftermarket` |
| **⚠️ Domain security** | **§19 → `dns-whois-disputes-domain-security-and-aftermarket`** |
| The aftermarket | §20 → `dns-whois-disputes-domain-security-and-aftermarket` |
| **⚠️ Why alternatives exist** | **§21 → `dns-blockchain-naming-alternatives-assessed`** |
| ENS | §22 → `dns-blockchain-naming-alternatives-assessed` |
| Other systems | §23 → `dns-blockchain-naming-alternatives-assessed` |
| **⚠️ Honest assessment** | **§24 → `dns-blockchain-naming-alternatives-assessed`** |
| Non-DNS namespaces | §25 → `dns-blockchain-naming-alternatives-assessed` |
| **What's live** | **§26 → `dns-reference`** |
| Misconceptions, numbers | §27–§28 → `dns-reference` |
| Sources, quick ref, method | §29–§31 → `dns-reference` |

---

## §1. What DNS Is For

```
⚠️ THE OBVIOUS JOB  ⚠️ name → IP address
⚠️ ⚠️ THE LESS OBVIOUS AND MORE IMPORTANT JOBS
   ⚠️ INDIRECTION  ⚠️ change where a name points without
      changing the name. ⚠️ This is what makes the whole web
      operable — hosts move, providers change, the name persists
   ⚠️ SERVICE DISCOVERY  ⚠️ MX for mail, SRV for services,
      NAPTR — ⚠️ DNS is how you find WHICH machine does WHAT
   ⚠️ ⚠️ POLICY DISTRIBUTION  ⚠️ SPF, DKIM, DMARC, CAA, DNSSEC
      records — ⚠️ DNS became the internet's general-purpose
      public assertion mechanism for a domain, largely by
      accident
   ⚠️ TRAFFIC STEERING  geographic and load-based (§12)
⚠️ ⚠️ AND THE UNDERAPPRECIATED ONE: DNS IS THE BASIS OF WEB PKI
   IDENTITY. ⚠️ A certificate authority proves you control a
   name by checking DNS or a resource under it — ⚠️ so whoever
   controls your DNS can obtain certificates for you (§19)
⚠️ THE SCALE  ⚠️ hundreds of millions of domains, trillions of
   queries daily, sub-100ms expectations, on a protocol from
   1983 with UDP as the default transport
```

---

# PART I — THE PROTOCOL

## §2. The Namespace

**⚠️ An inverted tree**: ⚠️ **the root (written as a bare dot), then top-level domains, then
second level, and downward.**
**⚠️ A fully qualified domain name ends in that dot** — ⚠️ **`www.example.com.` — and
software that omits it relies on search-list behaviour that causes surprising resolution
differences between machines.**
**⚠️ Labels** are up to 63 octets, ⚠️ **the whole name up to 255, and the practical
character set is letters, digits and hyphens (LDH).**
**⚠️ Internationalized domain names (IDN)** are encoded to ASCII via Punycode —
⚠️ **`xn--` prefixed — and ⚠️ HOMOGRAPH ATTACKS exploiting visually identical characters
across scripts are the security consequence, which is why browsers apply display rules
rather than showing Unicode unconditionally.**
**⚠️ DNS is case-insensitive** for matching, ⚠️ **and 0x20 encoding exploits case
randomization as an anti-spoofing measure** (§7 → `dns-attacks-dnssec-encrypted-dns-and-operations`).
**⚠️ Reserved and special-use names** — ⚠️ **`.local` for mDNS, `.onion` for Tor (§25 → `dns-blockchain-naming-alternatives-assessed`),
`.invalid`, `.test`, and `.internal` reserved for private use precisely so organizations
stop squatting names that might later be delegated.**

---

## §3. ⚠️ Resolution

> **⚠️ Knowing the two different kinds of server is what makes DNS debugging tractable.**
```
⚠️ ⚠️ THE TWO ROLES, and conflating them causes endless confusion
   ⚠️ RECURSIVE RESOLVER  ⚠️ does the WORK on your behalf —
      walks the hierarchy, caches results. ⚠️ Your ISP's, or
      8.8.8.8, or 1.1.1.1
   ⚠️ AUTHORITATIVE SERVER  ⚠️ holds the actual zone data for a
      domain and answers only for it. ⚠️ It does NOT recurse
⚠️ THE WALK, for a cold cache
   ⚠️ 1. Ask a ROOT server → "I don't know, but ask the .com
      servers, here they are"
   ⚠️ 2. Ask a .com server → "ask example.com's servers"
   ⚠️ 3. Ask example.com's server → the answer
   ⚠️ ⚠️ EACH STEP IS A REFERRAL, NOT A LOOKUP. The root does not
      know about your domain and never will
⚠️ STUB RESOLVER  ⚠️ what's in your OS — it just asks a recursive
   resolver and believes the answer
⚠️ ⚠️ THE 13 ROOT SERVER "ADDRESSES" ARE NOT 13 MACHINES.
   ⚠️ Thirteen is the count of NAMED addresses (a UDP packet
   size constraint from the original design); ⚠️ each is
   ANYCAST to hundreds of physical instances worldwide (§11)
⚠️ TRANSPORT  ⚠️ UDP 53 by default with a 512-byte classic limit,
   ⚠️ EDNS0 for larger, ⚠️ TCP fallback on truncation — and
   ⚠️ blocking DNS over TCP breaks things in confusing ways
⚠️ NEGATIVE ANSWERS  NXDOMAIN, and ⚠️ SOA-governed negative
   caching means "no such name" is cached too
```

---

## §4. Record Types

```
⚠️ THE COMMON ONES
   ⚠️ A / AAAA  IPv4 / IPv6 address
   ⚠️ CNAME  ⚠️ an ALIAS to another NAME. ⚠️ Cannot coexist with
      other records at the same name — ⚠️ WHICH IS WHY YOU
      CANNOT PUT A CNAME AT THE ZONE APEX (the apex needs SOA
      and NS). ⚠️ This trips up nearly everyone once (§10)
   ⚠️ MX  mail exchanger, with preference values
   ⚠️ TXT  ⚠️ arbitrary text — and therefore SPF, DKIM, DMARC,
      and domain-ownership verification for every SaaS product
   ⚠️ NS  delegation (§5) · ⚠️ SOA  zone parameters and the
      negative-cache TTL
   ⚠️ PTR  reverse lookup, ⚠️ and mail servers genuinely check it
   ⚠️ SRV  service location — host, port, priority, weight
   ⚠️ CAA  ⚠️ which certificate authorities may issue for this
      name. ⚠️ Cheap, underused, and directly limits the §19
      attack
   ⚠️ DNSKEY, DS, RRSIG, NSEC/NSEC3  DNSSEC (§8)
   ⚠️ SVCB / HTTPS  ⚠️ the modern one (§10)
⚠️ RRSET  ⚠️ all records of one type at one name are handled and
   signed as a SET, not individually
```

---

## §5. ⚠️ Zones, Delegation and Glue

```
⚠️ A ZONE is an administrative unit — ⚠️ a contiguous part of the
   tree managed together, bounded by delegations
⚠️ ⚠️ DELEGATION  ⚠️ the PARENT publishes NS records pointing to
   the child's servers. ⚠️ The parent does not hold the child's
   data — it only says who does
⚠️ ⚠️ THE NS RECORDS EXIST IN TWO PLACES — ⚠️ in the parent
   (authoritative for delegation) and in the child zone itself.
   ⚠️ When they disagree, resolution becomes unpredictable, and
   this is a real and common misconfiguration
⚠️ ⚠️ GLUE RECORDS  ⚠️ if example.com's nameserver is
   ns1.example.com, you have a CIRCULAR DEPENDENCY — you need
   the nameserver's address to look up the nameserver.
   ⚠️ The PARENT supplies the address directly. That is glue
   ⚠️ ⚠️ MISSING OR STALE GLUE IS A CLASSIC CAUSE OF A DOMAIN
   THAT WORKS FOR SOME PEOPLE AND NOT OTHERS
⚠️ ZONE TRANSFER  ⚠️ AXFR (full) and IXFR (incremental) with
   NOTIFY. ⚠️ Restrict AXFR — an open one hands an attacker
   your entire internal namespace
⚠️ PRIMARY and SECONDARY servers, ⚠️ and hidden primaries
⚠️ ⚠️ LAME DELEGATION  ⚠️ a nameserver is listed but does not
   answer authoritatively. ⚠️ Slow, intermittent failures
```

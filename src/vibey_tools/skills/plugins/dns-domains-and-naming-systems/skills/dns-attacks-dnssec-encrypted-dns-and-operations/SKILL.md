---
name: dns-attacks-dnssec-encrypted-dns-and-operations
description: "Use for DNS security and running DNS: the attack history from cache poisoning and Kaminsky through amplification and hijacking, DNSSEC with its chain of trust and honest deployment record, encrypted DNS via DoT, DoH and DoQ and what each does and does not hide, the modern extensions, operational practice including zone management and monitoring, and DNS as critical infrastructure with the outages that proved it."
---

# DNS and Domain Names: Attacks on DNS, DNSSEC, Encrypted DNS, Modern Extensions, Operations, and DNS as Infrastructure

> **Part 2 of 6** of the *DNS, Domain Names and Naming Systems* reference (plugin `dns-domains-and-naming-systems`), covering §6–§12. Sibling skills: `dns-namespace-resolution-records-and-zones` (§0–§5), `dns-icann-tlds-registries-and-registration` (§13–§16), `dns-whois-disputes-domain-security-and-aftermarket` (§17–§20), `dns-blockchain-naming-alternatives-assessed` (§21–§25), `dns-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ CACHING IS WHY IT SCALES AND WHY IT SURPRISES YOU** (§6). **"DNS propagation" is
>    not a thing that happens. Old answers expire. The distinction determines what you can
>    and cannot fix quickly, and it is the single most common misunderstanding in
>    operations.**
> 3. **⚠️ A NAMESPACE NEEDS A SINGLE ROOT TO BE UNAMBIGUOUS** (§21 → `dns-blockchain-naming-alternatives-assessed`, §26.2 → `dns-reference`). **Every
>    alternative naming system faces the same problem: without one authoritative root, the
>    same name can mean different things to different software. This is not a political
>    objection to decentralization — it is what a name is for.**

---

## §6. ⚠️ Caching and TTL

> **⚠️ §1 → `dns-namespace-resolution-records-and-zones`'s second organizing idea, and the operational one that matters most.**
```
⚠️ ⚠️ "DNS PROPAGATION" IS NOT A THING. ⚠️ Nothing propagates.
   ⚠️ Authoritative data changes INSTANTLY. What takes time is
   CACHED OLD ANSWERS EXPIRING
   ⚠️ THEREFORE the delay is bounded by the TTL THAT WAS IN
   EFFECT WHEN THE OLD ANSWER WAS CACHED — ⚠️ lowering the TTL
   now does not speed up a change you make now
⚠️ ⚠️ THE CORRECT PROCEDURE FOR A PLANNED CHANGE
   ⚠️ 1. LOWER THE TTL (say to 300s) · ⚠️ 2. WAIT for the OLD
   TTL to elapse · ⚠️ 3. make the change · 4. verify ·
   ⚠️ 5. raise the TTL back
⚠️ TTL AS A TRADE  ⚠️ short = agility and more query load and
   more exposure to resolver failures; long = efficiency and
   slow to change. ⚠️ Long for stable records, short before
   migrations
⚠️ ⚠️ TTLs ARE ADVISORY. ⚠️ Some resolvers clamp minimums, some
   serve stale on failure (⚠️ RFC 8767, which is a deliberate
   resilience feature), browsers cache separately, and the OS
   caches too. ⚠️ You do not control the whole chain
⚠️ NEGATIVE CACHING is governed by the SOA minimum — ⚠️ so
   creating a record that was recently missing can take longer
   to appear than changing an existing one
```

---

## §7. ⚠️ Attacks on DNS

```
⚠️ ⚠️ THE ORIGINAL SIN: DNS HAS NO AUTHENTICATION. ⚠️ A response
   is accepted if it matches the query, arrives on the right
   port, and has the right 16-bit transaction ID
⚠️ ⚠️ CACHE POISONING  ⚠️ inject a forged response before the
   real one arrives; the resolver caches your answer and serves
   it to everyone
   ⚠️ ⚠️ THE KAMINSKY ATTACK (2008) made this dramatically
   practical by attacking NONEXISTENT subdomains in a loop,
   removing the need to wait for a cache entry to expire —
   ⚠️ and it triggered a coordinated industry-wide emergency
   patch
   ⚠️ THE MITIGATION  ⚠️ SOURCE PORT RANDOMIZATION plus 0x20
   encoding — ⚠️ which raises the guessing cost enormously
   WITHOUT actually authenticating anything. ⚠️ DNSSEC is the
   real fix (§8)
⚠️ ⚠️ ON-PATH ATTACKS  ⚠️ trivially defeat plaintext DNS.
   ⚠️ This is the case for encrypted transport (§9)
⚠️ ⚠️ DNS AMPLIFICATION  ⚠️ small spoofed query, large response,
   directed at a victim. ⚠️ Open resolvers are the ammunition;
   ⚠️ response rate limiting and BCP 38 source filtering are
   the defences, and BCP 38 remains under-deployed
⚠️ NXDOMAIN and random-subdomain (water torture) attacks
   exhaust authoritative servers
⚠️ ⚠️ REGISTRAR-LEVEL AND REGISTRY-LEVEL ATTACKS  ⚠️ compromise
   the ACCOUNT and you need no protocol attack at all (§19).
   ⚠️ This is the highest-leverage attack and the least technical
```

---

## §8. ⚠️ DNSSEC

**⚠️ What it does**: ⚠️ **cryptographically signs DNS data so a resolver can verify
authenticity and integrity, with a chain of trust from the signed root downward.**
```
⚠️ THE MECHANISM  ⚠️ RRSIG signs each RRset · DNSKEY holds the
   zone's public keys · ⚠️ DS in the PARENT is a hash of the
   child's key — ⚠️ THAT is the delegation of trust, mirroring
   §5's delegation of authority
   ⚠️ KSK and ZSK separation lets you roll the zone key without
   touching the parent
⚠️ ⚠️ PROVING NONEXISTENCE IS THE HARD PART. ⚠️ You cannot sign
   an infinite set of names that do not exist
   ⚠️ NSEC proves a gap between two existing names — ⚠️ which
      allows ZONE WALKING, enumerating the whole zone
   ⚠️ NSEC3 hashes the names to prevent that, ⚠️ and is itself
      offline-crackable, hence NSEC3 with zero iterations plus
      white lies as current practice
⚠️ ⚠️ WHAT DNSSEC DOES NOT DO  ⚠️ IT DOES NOT ENCRYPT ANYTHING.
   ⚠️ Queries and answers remain fully visible. ⚠️ DNSSEC is
   INTEGRITY; §9 is CONFIDENTIALITY. They are orthogonal and
   constantly confused
⚠️ ⚠️ ADOPTION IS THE UNCOMFORTABLE PART  ⚠️ validation on the
   resolver side is now widespread, but SIGNING remains a
   minority of domains — and ⚠️ MISCONFIGURED DNSSEC TAKES YOUR
   DOMAIN COMPLETELY OFFLINE for validating resolvers, which is
   a failure mode worse than the attacks it prevents. ⚠️ Expired
   signatures have caused major national outages
⚠️ WHAT IT ENABLES  ⚠️ DANE (certificates in DNS), SSHFP,
   and authenticated §5 delegation
```

---

## §9. ⚠️ Encrypted DNS

```
⚠️ THE PROBLEM  ⚠️ classic DNS is plaintext, so your resolver,
   your ISP and anyone on path sees every name you look up —
   ⚠️ a metadata trove (see a communications reference §24)
⚠️ THE OPTIONS
   ⚠️ DoT (DNS over TLS)  ⚠️ port 853 — ⚠️ distinguishable and
      therefore blockable, which network operators like
   ⚠️ ⚠️ DoH (DNS over HTTPS)  ⚠️ port 443, indistinguishable
      from web traffic — ⚠️ which is precisely why it is
      CONTROVERSIAL. ⚠️ It bypasses network-level filtering,
      including both censorship AND legitimate enterprise
      controls and parental filters
   ⚠️ DoQ over QUIC · ⚠️ ODoH (Oblivious DoH) separates WHO is
      asking from WHAT is asked, using a proxy
⚠️ ⚠️ THE HONEST CRITIQUE OF DoH: IT MOVES TRUST RATHER THAN
   ELIMINATING IT. ⚠️ You stop trusting your ISP and start
   trusting a large DNS provider — ⚠️ and browser-default DoH
   centralizes visibility into a handful of operators, which is
   a real concern regardless of their current behaviour
⚠️ ENCRYPTED CLIENT HELLO (ECH) closes the adjacent leak —
   ⚠️ because encrypting DNS while SNI still reveals the
   hostname in the TLS handshake accomplishes much less than
   people assume
```

---

## §10. Modern Extensions

**⚠️ EDNS0** carries larger messages and option codes; ⚠️ **EDNS Client Subnet passes a
truncated client address to authoritative servers for geographic steering — ⚠️ useful for
CDNs and a genuine privacy leak, which is why some resolvers refuse it.**
**⚠️ The apex CNAME problem** (§4 → `dns-namespace-resolution-records-and-zones`) and its workarounds: ⚠️ **ALIAS/ANAME/CNAME-flattening
are PROVIDER-SPECIFIC, non-standard, and resolve server-side — which means behaviour differs
between DNS hosts.**
**⚠️ SVCB and HTTPS records** are the standardized fix and are genuinely significant:
⚠️ **they let a name advertise its protocol support, alternative endpoints, ECH
configuration and IP hints IN ONE LOOKUP — removing a round trip and enabling
HTTP/3 and ECH discovery without a redirect.**
**⚠️ Multicast DNS and DNS-SD** for local discovery (`.local`, and how printers and Chromecasts
are found).
**⚠️ DNS cookies and RRL** for spoofing and amplification resistance (§7).

---

## §11. Operations

**⚠️ ANYCAST is the central technique**: ⚠️ **announce the same IP from many locations, and
routing delivers each query to the nearest instance.** ⚠️ **This gives latency reduction,
DDoS absorption and failover simultaneously, and it is how the root and every major provider
operate** (§3 → `dns-namespace-resolution-records-and-zones`).
**⚠️ Diversity is the resilience lesson**: ⚠️ **use nameservers on separate networks and,
ideally, separate PROVIDERS — because a single provider's outage takes your domain off the
internet entirely regardless of how healthy your servers are.**
> **⚠️ GOTCHA — the 2016 Dyn DDoS is the reference case.** ⚠️ **Major sites became
> unreachable not because their infrastructure failed but because their single DNS provider
> was attacked.** **⚠️ Multi-provider DNS is the mitigation, and it is more work than it
> sounds because zone contents must stay synchronized.**

**⚠️ Monitoring**: ⚠️ **query volume and response codes, DNSSEC signature expiry (§8 — set
alerts, because this WILL be what takes you down), delegation consistency, and resolution
from multiple vantage points.**
**⚠️ Registry and registrar locks** (§19 → `dns-whois-disputes-domain-security-and-aftermarket`) belong in the operational runbook, not just in
security policy.

---

## §12. DNS as Infrastructure

**⚠️ CDN and global load balancing**: ⚠️ **answer differently by client location or server
health — which is DNS being used as a control plane, and it works because of §1 → `dns-namespace-resolution-records-and-zones`'s
indirection.**
> **⚠️ GOTCHA — DNS is a poor failover mechanism and people rely on it anyway.** ⚠️ **TTLs
> are advisory (§6), clients cache aggressively, and a browser may hold a resolved address
> for the life of a session.** **⚠️ Expect a long tail of traffic to the old address after
> any DNS-based failover, and design for it.**

**⚠️ Service discovery** in Kubernetes and elsewhere — ⚠️ **and note that cluster DNS
becomes a critical dependency whose failure looks like everything failing at once.**
**⚠️ DNS for blocklists and reputation** (RBLs for mail, §6 of a communications reference)
and ⚠️ **for filtering — which is what DoH (§9) disrupts.**
**⚠️ DNS as a covert channel**: ⚠️ **tunnelling and exfiltration over DNS work because DNS
is almost never blocked, and detecting them is a standard security-monitoring task.**

---

# PART II — DOMAINS AND GOVERNANCE

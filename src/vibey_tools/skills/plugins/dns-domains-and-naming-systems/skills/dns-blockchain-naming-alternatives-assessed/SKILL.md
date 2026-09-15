---
name: dns-blockchain-naming-alternatives-assessed
description: "Use when evaluating blockchain naming or another DNS alternative: why alternatives exist and what problem they claim to solve, ENS and how it actually resolves, the other systems including Handshake and Unstoppable Domains, an honest assessment of adoption, resolution dependence and the browser problem, and the non-DNS namespaces such as onion addresses and IPFS naming."
---

# DNS and Domain Names: Why Alternatives Exist, ENS, Other Systems, an Honest Assessment, and Non-DNS Namespaces

> **Part 5 of 6** of the *DNS, Domain Names and Naming Systems* reference (plugin `dns-domains-and-naming-systems`), covering §21–§25. Sibling skills: `dns-namespace-resolution-records-and-zones` (§0–§5), `dns-attacks-dnssec-encrypted-dns-and-operations` (§6–§12), `dns-icann-tlds-registries-and-registration` (§13–§16), `dns-whois-disputes-domain-security-and-aftermarket` (§17–§20), `dns-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ A NAMESPACE NEEDS A SINGLE ROOT TO BE UNAMBIGUOUS** (§21, §26.2 → `dns-reference`). **Every
>    alternative naming system faces the same problem: without one authoritative root, the
>    same name can mean different things to different software. This is not a political
>    objection to decentralization — it is what a name is for.**

---

## §21. ⚠️ Why Alternatives Exist

```
⚠️ THE GRIEVANCES, stated fairly — ⚠️ several are legitimate
   ⚠️ CENTRAL CONTROL  ⚠️ ICANN and registries can seize or
      suspend names; ⚠️ governments have seized domains
   ⚠️ RENEWAL  you never own it (§15)
   ⚠️ ⚠️ CENSORSHIP  ⚠️ DNS-level blocking is the most common
      state censorship mechanism worldwide
   ⚠️ COST and gatekeeping · ⚠️ WHOIS privacy (§17)
   ⚠️ Registrar and registry as points of failure (§19)
⚠️ THE PROPOSED ANSWER  ⚠️ put the namespace on a blockchain —
   cryptographic ownership, no registrar, censorship-resistant
⚠️ ⚠️ AND THE STRUCTURAL PROBLEM THAT DEFEATS IT (§1's third
   organizing idea)
   ⚠️ ⚠️ A NAME IS ONLY USEFUL IF EVERYONE RESOLVES IT THE SAME
      WAY. ⚠️ Multiple independent roots means the same string
      can resolve differently depending on your software —
      ⚠️ which is not decentralization succeeding, it is a
      namespace failing at its one job
   ⚠️ ⚠️ COLLISION  ⚠️ if a blockchain issues .wallet and ICANN
      later delegates .wallet, two authorities claim one string
   ⚠️ ⚠️ AND THE DISTRIBUTION PROBLEM IS THE FATAL ONE: browsers
      must resolve it. ⚠️ Alternative roots have been tried
      since the 1990s and ALL failed for this reason (§13)
```

---

## §22. ENS

**⚠️ The Ethereum Name Service** maps `.eth` names via smart contracts, ⚠️ **with a
registry, resolvers and registrar contracts, governed by a DAO with an ENS token.**
**⚠️ What it does genuinely well**: ⚠️ **replacing a hex wallet address with a readable name
is a real usability improvement with a real failure mode it removes — sending funds to a
mistyped address is irreversible.**
**⚠️ It resolves across wallets and dApps broadly** — ⚠️ **within the crypto ecosystem, ENS
is close to universal.**
**⚠️ It can also import DNS names**: ⚠️ **a DNSSEC-signed domain can be used on-chain
without inventing a new extension — which sidesteps §21's collision problem entirely and is
the more architecturally honest approach.**
**⚠️ It can point at IPFS content** for censorship-resistant static hosting (§25).
**⚠️ The limits**: ⚠️ **key loss is unrecoverable, gas costs and renewal exist, disputes have
no UDRP equivalent, and — decisively — ⚠️ no mainstream browser resolves `.eth` natively**
(§24, §26.2 → `dns-reference`).

---

## §23. Other Systems

**⚠️ Handshake (HNS)** — ⚠️ **the most ambitious: a proof-of-work blockchain intended to
replace the DNS ROOT ZONE itself, with TLDs auctioned on-chain.** ⚠️ **Technically
interesting and it required resolver software or extensions that were never adopted at
scale** (§26.2 → `dns-reference`).
**⚠️ Unstoppable Domains** — ⚠️ **a venture-backed company minting NFT names under
self-created extensions (.crypto, .nft, .x, .wallet) on Ethereum and later Polygon and
others, sold as one-time purchase with no renewal.** ⚠️ **Note the tension: a for-profit
company creating and controlling extensions is centralized in a way the pitch downplays.**
**⚠️ Namecoin** was the 2011 original (.bit), ⚠️ **and its trajectory prefigured the rest.**
**⚠️ Others**: ⚠️ **Solana Name Service, Bonfida, and various chain-specific systems — and
the proliferation is itself §21's fragmentation problem.**

---

## §24. ⚠️ Honest Assessment

> **⚠️ Read this before any promotional material, and see §26.2 → `dns-reference` for what happened.**
```
⚠️ ⚠️ WHAT IS GENUINELY GOOD
   ⚠️ WALLET-ADDRESS REPLACEMENT IS A REAL, SOLVED PROBLEM.
      ⚠️ alice.eth beats 0x71C7... and this use case has
      durable adoption
   ⚠️ Cryptographic ownership with no registrar to socially
      engineer (§19) is a real property
   ⚠️ Censorship resistance for the naming layer is real —
      ⚠️ though see the caveat below
⚠️ ⚠️ WHAT WAS OVERSOLD
   ⚠️ ⚠️ "REPLACING DNS" — ⚠️ browsers never resolved these
      natively, and without that a name is not a web address
   ⚠️ "OWN IT FOREVER" — ⚠️ true of the token, and the token is
      only meaningful while the resolution infrastructure and
      the chain persist
   ⚠️ ⚠️ CENSORSHIP RESISTANCE IN PRACTICE  ⚠️ the NAME may be
      uncensorable while the HOSTING, the gateway, the wallet
      and the exchange are not. ⚠️ Moving the choke point is
      not removing it
⚠️ ⚠️ THE STRUCTURAL VERDICT  ⚠️ THIS WAS A DISTRIBUTION
   PROBLEM, NOT A TECHNOLOGY PROBLEM. ⚠️ Chicken and egg: no
   users because browsers do not resolve it; no browser support
   because no users. ⚠️ Every alt-root since the 1990s has died
   here, and blockchain did not change the shape of that problem
⚠️ ⚠️ WHAT TO ACTUALLY DO  ⚠️ for a public website, use DNS.
   ⚠️ For crypto identity, ENS is genuinely useful. ⚠️ These are
   different tools for different jobs, and treating one as a
   replacement for the other is the error
```

---

## §25. Non-DNS Namespaces

**⚠️ Tor .onion** — ⚠️ **the address IS the public key (or its hash), so the name is
self-authenticating and needs no registry at all.** ⚠️ **The trade is that names are
unmemorable by construction — the strongest counterexample to the assumption that a
namespace needs an authority, achieved by giving up human-readability entirely.**
**⚠️ Zooko's triangle** is the framing worth carrying: ⚠️ **a naming system can be
human-meaningful, secure and decentralized — pick two.** ⚠️ **Petnames and various schemes
claim to square it; whether they do is genuinely contested.**
**⚠️ IPFS and IPNS** — ⚠️ **content addressing by hash means the name IS the integrity
check, and mutability requires IPNS or DNSLink (⚠️ which reintroduces DNS).**
**⚠️ DIDs (Decentralized Identifiers)** — ⚠️ **a W3C standard for identifiers with many
methods, aimed at identity rather than at locating hosts.**
**⚠️ mDNS/.local** (§10 → `dns-attacks-dnssec-encrypted-dns-and-operations`) and ⚠️ **NetBIOS as the historical local-namespace examples.**

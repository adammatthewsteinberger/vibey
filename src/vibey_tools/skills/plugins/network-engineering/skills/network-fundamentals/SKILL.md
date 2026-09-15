---
name: network-fundamentals
description: "Use when explaining or learning networking from first principles: OSI model, TCP/IP, DNS, DHCP, HTTP/S, routing, subnetting, VLANs, NAT, firewalls, VPNs, or any foundational networking concept. Great for onboarding engineers, explaining concepts to non-specialists, or working through network troubleshooting basics. Triggers on questions about packets, IP addresses, TCP handshake, DNS resolution, subnetting math, ARP, Ethernet, switches vs routers, or any Layer 1-7 question."
---

# Network Fundamentals: From First Principles to Production

## Why networks exist and the packet-switching breakthrough

A computer network is two or more devices connected to exchange data. Every protocol, device, and standard exists to make that exchange reliable, fast, and scalable.

The origin story matters. In the mid-1960s Bob Taylor at ARPA noticed he needed three separate terminals to connect to three different research computers. On October 29, 1969, UCLA sent "LOGIN" to Stanford Research Institute — the system crashed after "LO," but the full message went through within an hour. ARPANET was alive.

The key innovation was **packet switching**, independently conceived by Paul Baran (for nuclear-survivable military communications) and Donald Davies (who coined the term). Instead of dedicating a physical wire between two parties — how telephone calls worked — data is chopped into small pieces and routed independently through a shared network. Packet switching is a highway system shared by everyone, not a private road built just for you. It is why billions of people can use the Internet simultaneously.

**The postal system analogy** is the single most useful mental model. Data is a letter. The IP address is the mailing address. Packets are individual envelopes. Routers are postal sorting centers that read the address and forward the envelope toward its destination. This analogy scales surprisingly well into advanced topics.

## Packets: the unit of network communication

When you send a photo, it travels as packets — small, independently addressed chunks, each routed separately.

Each packet has three parts:
- **Header**: addressing and control information — source/destination addresses, sequence numbers, protocol identifiers. The envelope with addresses and postage.
- **Payload**: the actual data — a fragment of your photo.
- **Trailer**: CRC checksum for error detection. The receiver verifies the data was not corrupted.

Why packets instead of one big chunk? Three reasons: efficiency (statistical multiplexing lets multiple conversations share wires simultaneously), resilience (only the corrupt packet needs retransmission), and fairness (no single transfer monopolizes the link).

Key units: network speeds are measured in **bits** per second (Mbps, Gbps), while storage is measured in **bytes** (MB, GB). A 100 Mbps connection transfers about 12.5 MB/s. The standard maximum packet size — the **MTU (Maximum Transmission Unit)** — is **1,500 bytes**, a historical artifact of early Ethernet design that persists today.

## OSI model: networking's periodic table

The **OSI model** (ISO/IEC 7498, 1984) divides network communication into seven layers. It is a reference model — a conceptual framework, not what the Internet actually runs. Think of it as networking's periodic table: you do not use it to build molecules directly, but understanding it makes everything else make sense.

Data moves down the stack on the sending side. Each layer adds its own header (**encapsulation**). At the receiving side, each layer strips its header (**de-encapsulation**) and passes data up.

| Layer | Name | PDU | Real-world examples | Devices |
|-------|------|-----|---------------------|---------|
| 7 | Application | Data | HTTP, DNS, SMTP, SSH | — |
| 6 | Presentation | Data | TLS/SSL, data formatting | — |
| 5 | Session | Data | Session establishment | — |
| 4 | Transport | Segments/Datagrams | TCP, UDP, ports | — |
| 3 | Network | Packets | IP, ICMP, OSPF, BGP | Routers |
| 2 | Data Link | Frames | Ethernet, MAC addresses | Switches |
| 1 | Physical | Bits | Cables, Wi-Fi radio, voltages | Hubs |

Mnemonic: "**P**lease **D**o **N**ot **T**hrow **S**ausage **P**izza **A**way" (Physical → Application).

**The TCP/IP 4-layer model** is what the Internet actually runs. Developed by DARPA in the 1970s, it collapses OSI into four layers: Network Access (OSI 1-2), Internet (OSI 3), Transport (OSI 4), Application (OSI 5-7). Use OSI for troubleshooting ("which layer is the problem at?"); use TCP/IP for understanding the actual protocol stack.

## Layer 1-2: Physical media, Ethernet, MAC addresses, switches, ARP, VLANs

**Layer 1 — Physical**: raw bits on a wire. Electrical signals, fiber optics, Wi-Fi radio. Devices: hubs (dumb repeaters that blast traffic to every port — effectively extinct), cables, repeaters.

**MAC addresses** are 48-bit identifiers burned into every NIC at the factory: `00:1A:2B:3C:4D:5E`. The first 24 bits identify the manufacturer (OUI). The broadcast address `FF:FF:FF:FF:FF:FF` reaches every device on the local network. MAC addresses are physical and permanent; they enable delivery within a single network segment.

**Switches** read MAC addresses and forward frames only to the correct port. A switch builds a MAC address table by inspecting incoming traffic — it learns which MAC is on which port. Think of a mailroom clerk who reads the name on each envelope and places it in the correct mailbox. Switches operate at Layer 2 and create separate collision domains per port.

**ARP (Address Resolution Protocol, RFC 826)** bridges Layer 2 and Layer 3. Your computer knows the destination IP but Ethernet frames require a MAC address. ARP broadcasts: "Who has `192.168.1.20`? Tell `192.168.1.10`." Only the device with that IP responds with its MAC. Your computer caches this mapping (1-5 minutes). ARP has no authentication — a critical weakness enabling ARP spoofing (man-in-the-middle attacks). Defenses: Dynamic ARP Inspection on managed switches. IPv6 replaces ARP with NDP (Neighbor Discovery Protocol, RFC 4861).

**VLANs (IEEE 802.1Q)** create isolated broadcast domains within a single physical switch. Without VLANs, every port shares one broadcast domain — every ARP request reaches every device. VLANs insert a 4-byte tag into the Ethernet frame containing a 12-bit VLAN ID (supporting 4,094 usable VLANs). Access ports connect to end devices (one VLAN). Trunk ports carry multiple VLANs between switches. Inter-VLAN routing requires Layer 3: either a Layer 3 switch with SVIs or the older router-on-a-stick approach.

## Layer 3: IP addressing, subnetting, routing, NAT

**IPv4** (RFC 791, 1981) uses 32-bit addresses: `192.168.1.1`. 2³² = ~4.3 billion addresses. IANA exhausted them on February 3, 2011. RFC 1918 private ranges: `10.0.0.0/8` (~16.7M), `172.16.0.0/12` (~1M), `192.168.0.0/16` (~65K). These cannot appear on the public Internet.

**IPv6** (RFC 8200) uses 128-bit addresses: `2001:0db8:85a3::8a2e:0370:7334`. 2¹²⁸ ≈ 3.4 × 10³⁸ addresses — enough to assign trillions to every grain of sand on Earth.

**CIDR subnetting** (RFC 4632): a subnet mask divides an IP address into network bits (left) and host bits (right). CIDR notation appends the network bit count: `/24` = 24 network bits, 8 host bits, 2⁸−2 = **254 usable hosts**.

Quick reference:
| CIDR | Hosts | Usable | Example |
|------|-------|--------|---------|
| /8 | 16,777,216 | 16,777,214 | 10.0.0.0/8 |
| /16 | 65,536 | 65,534 | 172.16.0.0/16 |
| /24 | 256 | 254 | 192.168.1.0/24 |
| /25 | 128 | 126 | 192.168.1.0/25 |
| /26 | 64 | 62 | 192.168.1.0/26 |
| /27 | 32 | 30 | 192.168.1.0/27 |
| /28 | 16 | 14 | 192.168.1.0/28 |
| /30 | 4 | 2 | point-to-point links |

**Subnetting example**: Divide `192.168.1.0/24` into four equal subnets. Need 2 extra bits (2²=4), making /26. Each /26 has 62 usable hosts:
- `192.168.1.0/26` — hosts .1 to .62
- `192.168.1.64/26` — hosts .65 to .126
- `192.168.1.128/26` — hosts .129 to .190
- `192.168.1.192/26` — hosts .193 to .254

**NAT (RFC 3022)** lets many internal devices share a single public IP using port numbers (PAT). Device `10.0.0.10:3017` → NAT rewrites source to `203.0.113.1:1024` → records mapping → translates responses back. One public IP supports ~65,000 concurrent connections. NAT breaks end-to-end principle and complicates peer-to-peer, VoIP, and IPsec. CGNAT (100.64.0.0/10, RFC 6598) adds a second NAT layer at ISPs.

**Routing tables** use longest prefix match — the most specific matching entry always wins. When multiple protocols advertise the same prefix, administrative distance (AD) determines trust: Connected=0, Static=1, eBGP=20, OSPF=110, iBGP=200.

## Layer 4: TCP vs UDP — reliability vs speed

**TCP (RFC 793)** is connection-oriented: establishes a session before data transfer, guarantees every byte arrives in order, retransmits lost data. Uses acknowledgments, sequence numbers, sliding window for flow control, and congestion control algorithms (slow start, congestion avoidance, fast retransmit). Header: 20-60 bytes. Use for: HTTP/HTTPS, SSH, FTP, email — anything where data integrity matters.

**UDP (RFC 768)** is connectionless: fires packets with no handshake, no ACKs, no ordering, no congestion control. Header: 8 bytes (source port, destination port, length, checksum). Use for: DNS queries, video streaming, VoIP, gaming — anything where speed matters more than perfection. A dropped video frame causes a brief glitch; retransmitting it would introduce unacceptable delay.

**QUIC** (RFC 9000, developed by Google) runs over UDP but implements TCP's reliability at the application layer, eliminating head-of-line blocking. HTTP/3 uses QUIC. As of 2025, over 25% of Internet traffic runs on it.

## The TCP three-way handshake

Before any data flows, both sides synchronize state:

1. **SYN**: Client → `Seq=1000, SYN`. "I want to talk. My sequences start at 1000."
2. **SYN-ACK**: Server → `Seq=5000, Ack=1001, SYN+ACK`. "I hear you. My sequences start at 5000."
3. **ACK**: Client → `Seq=1001, Ack=5001`. Both enter ESTABLISHED. Data flows.

Why three steps? Both directions need to synchronize sequence numbers. Logically four exchanges, compressed to three because the server combines SYN+ACK. Connection teardown uses four-way FIN→ACK→FIN→ACK because each direction closes independently.

## Layers 5-7: TLS, HTTP, DNS

**TLS 1.3 handshake** (RFC 8446) completes in a single round trip: client sends supported cipher suites and key share in ClientHello; server responds with its key share, certificate, and verification — everything after ServerHello is encrypted. Both sides derive symmetric session keys. Only ephemeral key exchanges (ECDHE) are permitted, guaranteeing **forward secrecy** — compromising a server's long-term key cannot decrypt past sessions.

**HTTP versions**:
- HTTP/1.1: text-based, one request per connection (pipelining was unreliable)
- HTTP/2 (RFC 9113): binary framing, multiplexing — multiple requests over one TCP connection
- HTTP/3 (RFC 9114): uses QUIC (UDP), eliminates head-of-line blocking, 1-RTT connection setup (0-RTT for resumed)

HTTP status codes: 2xx success (200 OK, 201 Created), 3xx redirect (301 Permanent, 304 Not Modified), 4xx client error (400 Bad Request, 403 Forbidden, 404 Not Found), 5xx server error (500 Internal, 503 Unavailable).

**DNS resolution** when you visit `www.example.com`:
1. Browser checks cache → empty
2. Asks recursive resolver (ISP DNS or 8.8.8.8)
3. Resolver asks root server: "Where is .com?" → returns TLD server addresses
4. Resolver asks .com TLD: "Where is example.com?" → returns authoritative nameserver
5. Resolver asks authoritative server: "What is www.example.com?" → returns A record: `93.184.216.34`
6. Result cached for TTL duration (minutes to hours)

Key DNS record types: **A** (→IPv4), **AAAA** (→IPv6), **CNAME** (alias), **MX** (mail), **NS** (nameserver), **TXT** (SPF, DKIM, verification).

**DHCP DORA process**: Discover (client broadcasts from 0.0.0.0 to 255.255.255.255) → Offer (server proposes IP, subnet, gateway, DNS) → Request (client accepts) → Acknowledge (server confirms). Lease duration: typically 8 hours to 8 days. Client renews at 50% of lease.

## Network devices: roles and layers

| Device | Layer | Function |
|--------|-------|----------|
| Hub | L1 | Dumb repeater — blasts to all ports. Extinct. |
| Switch | L2 | Reads MAC addresses, forwards to correct port only. |
| Router | L3 | Forwards packets between networks using IP, routing table. |
| Firewall | L3-L7 | Controls traffic based on rules; stateful inspection. |
| Load Balancer | L4/L7 | Distributes traffic across server pools. |
| Access Point | L1-L2 | Bridges Wi-Fi (802.11) to wired Ethernet (802.3). |

**Stateless firewalls** (packet filters): inspect each packet against rules (source/destination IP, ports, protocol). Fast but cannot distinguish legitimate responses from attacks. **Stateful firewalls** maintain a connection state table. Return traffic matching an established session is automatically permitted — only outbound rules needed. **NGFWs** add application awareness, deep packet inspection, TLS decryption, user identity.

## VPNs: site-to-site vs client

**Site-to-site VPN**: connects two entire networks (e.g., office to data center). Transparent to end users. Uses IPsec (tunnel or transport mode).

**Client VPN (remote access)**: individual device connects to corporate network. Options:
- **IPsec**: strong security, complex NAT traversal issues
- **OpenVPN**: TLS-based, runs over TCP or UDP, firewall-friendly
- **WireGuard**: modern, simple, high-performance, uses ChaCha20/Poly1305 cryptography

VPNs encrypt traffic and provide network-level access but grant broad network access upon authentication — a violation of least privilege. Zero Trust Network Access (ZTNA) is replacing VPNs for this reason.

## Data center networking: spine-leaf

Traditional three-tier networks (core/distribution/access) used STP to prevent loops by blocking redundant links — wasted bandwidth and caused 30-50 second convergence delays.

**Spine-leaf (Clos) topology**: every leaf switch connects to every spine switch. Any server-to-server communication traverses exactly 3 hops (leaf → spine → leaf). ECMP load-balances across all spine links simultaneously — no blocked paths. Adding capacity is horizontal: more spines increase bisection bandwidth; more leaves add server ports. Layer 3 routing (typically eBGP) replaces STP entirely.

East-west traffic (server-to-server) now accounts for 70-80%+ of data center traffic, driven by microservices and distributed storage — the primary reason spine-leaf won.

## Cloud networking fundamentals

**VNets (Azure) / VPCs (AWS/GCP)**: isolated virtual networks in the cloud. Subnets divide the address space. Route tables control traffic flow.

**VNet/VPC peering**: connects two virtual networks at the cloud backbone layer. Traffic stays on Microsoft's/Amazon's network, not the public Internet.

**Private endpoints**: expose Azure PaaS services (Storage, SQL, Key Vault) with a private IP inside your VNet, eliminating public Internet exposure.

**ExpressRoute (Azure) / Direct Connect (AWS)**: dedicated private connectivity between your on-premises network and the cloud. Bypass the public Internet for reliability and predictable performance.

## Performance metrics

- **Bandwidth**: maximum theoretical capacity — the pipe width. 1 Gbps = 1 billion bits/second.
- **Latency**: time for one packet to travel source → destination. Components: propagation delay (speed of light), transmission delay, processing delay, queuing delay. Typical: <1ms LAN, 40-80ms cross-country, 500-700ms geostationary satellite.
- **Throughput**: actual data rate achieved — always ≤ bandwidth.
- **Jitter**: variation in packet delay. Devastating for VoIP (acceptable: <30ms). High bandwidth with high latency means poor interactive responsiveness even if large transfers complete quickly.

## Troubleshooting toolkit

| Tool | What it does | Example |
|------|-------------|---------|
| `ping` | Tests reachability (ICMP echo) | `ping 8.8.8.8` |
| `traceroute`/`tracert` | Shows hop-by-hop path | `traceroute google.com` |
| `nslookup`/`dig` | DNS queries | `dig +short example.com A` |
| `netstat`/`ss` | Shows active connections, listening ports | `ss -tulnp` |
| `tcpdump` | Captures packets on Linux | `tcpdump -i eth0 port 80` |
| `Wireshark` | GUI packet analysis | Filter: `tcp.port == 443` |
| `nmap` | Network scanning | `nmap -sV -p 1-1000 host` |
| `ip route` | Show routing table | `ip route show` |
| `arp -a` | Show ARP cache | Local MAC→IP mappings |

**Troubleshooting methodology — work the OSI stack**:
1. L1: Is the cable connected? Link lights on?
2. L2: ARP resolving? Any duplicate MACs? VLAN misconfiguration?
3. L3: Can you ping the default gateway? Is routing correct? NAT configured?
4. L4: Is the service listening on the right port? (`netstat`/`ss`)
5. L7: DNS resolving? TLS certificate valid? Application responding?

## The thread connecting everything

Every major networking technology exists because the previous approach hit a scaling wall: classful addressing → CIDR; STP → ECMP; flood-and-learn → EVPN; MPLS signaling → Segment Routing; iptables → eBPF. Understanding why each transition happened matters more than memorizing configurations.

The control plane / data plane separation is the most powerful architectural pattern in networking. It appears everywhere: BGP EVPN managing VXLAN data planes, Kubernetes controllers managing pod networking, load balancers managing traffic distribution. Master this pattern once and you have leverage across every domain.

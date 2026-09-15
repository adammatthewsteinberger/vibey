---
name: network-modern-stack
description: "Use for modern and advanced networking topics: eBPF-based networking, Cilium for Kubernetes, AKS networking modes, SPIFFE/SPIRE workload identity, zero trust networking, BGP fabrics, EVPN/VXLAN overlays, SRv6, network observability, or cloud-native network security. Triggers on Cilium, eBPF, AKS CNI, service mesh, Azure CNI Overlay, kube-proxy replacement, Hubble, SPIRE, network SLOs, chaos engineering for networks, or any production-scale Kubernetes networking question. Also use for Python network automation with Nornir, Scapy, or NAPALM."
---

# Modern Network Stack: 2026 Gold Standards

## The protocol stack in 2026

The OSI model remains a pedagogical framework, but production networking has evolved significantly. Key shifts:

**BGP as universal control plane**: not just for inter-domain routing, but for data center fabrics (eBGP underlay), EVPN overlays (MP-BGP), and segment routing advertisement. RPKI adoption crossed 50% of IPv4 routes — nearly all Tier-1 transit providers now reject RPKI-invalid prefixes. BGPsec remains largely experimental; the industry focused on RPKI/ROV and ASPA objects for path security.

**OSPF v3** (RFC 5340) serves as the workhorse underlay routing protocol in spine-leaf fabrics, providing ECMP paths between VTEPs.

**MPLS → SR-MPLS → SRv6 trajectory**: SR-MPLS eliminates the complexity of RSVP-TE and LDP signaling. SRv6 (Segment Routing over IPv6) is the next wave, driven by 5G network slicing. Microsoft Azure's Fairwater data center uses SRv6 for what it describes as the largest AI backend network in the world. Bell Canada, Alibaba, and Rakuten have all committed to SRv6 migrations.

## Spine-leaf dominance and east-west traffic

East-west traffic now accounts for **70-80%+ of data center traffic**. Spine-leaf (Clos) topology replaced three-tier architectures because STP could not handle the east-west explosion driven by microservices and distributed storage.

In spine-leaf, every leaf connects to every spine: predictable two-hop latency, ECMP load balancing across all paths, horizontal scalability. Layer 3 routing (eBGP) replaces STP entirely.

**EVPN-VXLAN** is the standard overlay control plane:
- **VXLAN** (RFC 7348): MAC-in-UDP encapsulation. Uses 24-bit VNI supporting ~16 million logical segments (versus VLAN's 4,096 limit). UDP port 4789. VTEPs terminate tunnels at each leaf.
- **EVPN** (carried over MP-BGP): distributes MAC/IP reachability explicitly, eliminating flood-and-learn. Route Type 2 (MAC/IP Advertisement) is the workhorse. Spine switches serve as BGP route reflectors. Distributed anycast gateways eliminate traffic tromboning for east-west routing.
- **GENEVE** (RFC 8926): emerging as VXLAN's successor due to extensible TLV metadata. AWS Gateway Load Balancer already uses GENEVE. Cilium supports it as an alternative encapsulation.

**Symmetric IRB** is the production standard for inter-subnet routing in EVPN-VXLAN fabrics: each VTEP only configures VLANs for locally connected hosts, using a dedicated L3 VNI per tenant VRF. Both ingress and egress perform routing and bridging. Asymmetric IRB (every VTEP must host every VLAN's routing state) does not scale.

## eBPF: the kernel-programmable network primitive

**eBPF (extended Berkeley Packet Filter) is the most consequential networking technology of the decade.** It allows sandboxed programs to execute inside the Linux kernel without modifying kernel source or loading modules. Programs are written in restricted C, verified for safety by an in-kernel verifier, and JIT-compiled to native instructions.

### Three hook points that matter for networking

**XDP (eXpress Data Path)**: operates at the NIC driver level before socket buffer allocation — the earliest possible interception point. Achieves **~194 Gbps throughput**, roughly **12.4× iptables performance**. Best for: DDoS mitigation at line rate, L4 load balancing, packet filtering at wire speed. Cloudflare auto-mitigated a record 3.8 Tbps DDoS attack using XDP-based filtering at ~10 million packets/second per core.

**TC (Traffic Control)**: hooks after socket buffer creation, supporting both ingress and egress with full conntrack integration. This is Cilium's primary enforcement point. Enables more complex processing with access to full kernel metadata.

**Socket-level programs**: enable custom load balancing (SO_REUSEPORT) and socket-to-socket shortcuts that bypass the entire network stack — Cilium's kube-proxy replacement intercepts connections at the `connect()` syscall.

### Production deployments

**Meta's Katran**: XDP-based L4 load balancer processing all facebook.com traffic. 3× more packets with 7× less CPU than its IPVS predecessor, using modified Maglev consistent hashing with DSR.

**Cloudflare's Unimog**: edge load balancing at under 1% CPU utilization.

**Tetragon / Falco**: runtime security monitoring via eBPF.

**Hubble**: deep network observability without sidecars or instrumentation.

## Cilium: the production Kubernetes networking standard

**Cilium** (CNCF graduated, acquired by Cisco via Isovalent) is eBPF-native Kubernetes networking, security, and observability — replacing kube-proxy entirely.

Key metrics:
- **72× CPU reduction** at Seznam.cz after replacing kube-proxy
- O(1) hash-based service routing versus iptables' O(n) linear rule matching
- Identity-based enforcement (not IP-based) that survives pod restarts

### What Cilium provides

**Networking**: pod-to-pod networking via eBPF, VXLAN or GENEVE encapsulation, native routing mode (no overlay) for BGP-integrated environments.

**kube-proxy replacement**: intercepts connections at socket level (the `connect()` syscall), eliminating per-packet NAT overhead and conntrack table contention. Result: dramatically lower CPU at scale.

**Network Policy**: L3/L4/L7 enforcement. FQDN-based egress filtering. DNS-aware policies. HTTP method/path filtering. L7 Kafka/gRPC policies with ACNS.

**Hubble observability**: flow-level visibility, identity-aware traffic logs, DNS latency metrics, pre-built Grafana dashboards — all without sidecars. Real-time `hubble observe` CLI and UI.

**Cilium Service Mesh**: sidecarless service mesh using ztunnels for L4 mTLS and optional waypoint proxies for L7. Dramatically lower overhead than Envoy-sidecar approaches.

### CiliumNetworkPolicy example

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-payments-to-db
spec:
  endpointSelector:
    matchLabels:
      app: postgres
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: payments-service
    toPorts:
    - ports:
      - port: "5432"
        protocol: TCP
```

FQDN-based egress (requires ACNS or Cilium Enterprise):
```yaml
spec:
  endpointSelector:
    matchLabels:
      app: backend
  egress:
  - toFQDNs:
    - matchName: "api.external-service.com"
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP
```

## AKS networking: the complete decision guide

### CNI selection — the most consequential AKS decision

Microsoft now explicitly recommends **Azure CNI Overlay** for most scenarios. **Kubenet is retiring March 31, 2028**.

| Mode | Recommended | Pod IPs | Scale | Notes |
|------|-------------|---------|-------|-------|
| Azure CNI Overlay + Cilium | **Yes — production standard** | Separate CIDR, SNAT to node | 5,000 nodes, 250 pods/node | Conserves VNet IP space |
| Azure CNI Pod Subnet | Specific use case | Direct VNet IPs | 5,000 nodes | Use when external systems need pod IPs |
| Azure CNI Node Subnet | Legacy | VNet IPs, pre-allocated | 5,000 nodes | Being superseded |
| Kubenet | No — retiring | VNET IPs for nodes, private for pods | 400 nodes | Linux only, requires UDR management |

**The gold-standard production command**:
```bash
az aks create \
  --name myCluster --resource-group myRG --location eastus \
  --network-plugin azure --network-plugin-mode overlay \
  --pod-cidr 192.168.0.0/16 --network-dataplane cilium \
  --enable-acns --generate-ssh-keys
```

This deploys: Azure CNI Overlay + Cilium eBPF data plane + Advanced Container Networking Services for L7 policies, FQDN filtering, and Hubble observability.

### Network Policy engine comparison

**Azure Network Policy Manager (NPM)**: retiring. Windows support ends September 2026, Linux September 2028. iptables enforcement. Caps at 250 nodes/20,000 pods. No L7 or FQDN capabilities.

**Calico**: standard Kubernetes NetworkPolicy with better scalability. Cross-platform (Linux + Windows). AKS-managed Calico does not expose advanced features.

**Cilium** (Microsoft's recommendation): L3/L4/L7 enforcement, FQDN-based egress, DNS-aware policies, identity-based (not IP-based) enforcement, Hubble observability — all via eBPF with no iptables overhead.

Microsoft's official position: "We recommend using Cilium, which provides robust support for Kubernetes-native policies, extended features such as Layer 7 policy and FQDN filtering, and an eBPF-based dataplane that offers better performance, scalability, and security compared to iptables-based solutions."

### AKS DNS optimization

Default `ndots:5` causes excessive DNS queries for external names. **Optimize to `ndots:2` or `ndots:1`** for pods making frequent external DNS calls.

CoreDNS autoscaling formula: `replicas = max(ceil(cores/coresPerReplica), ceil(nodes/nodesPerReplica))` with minimum 2 replicas.

The **LocalDNS** feature deploys a per-node DNS proxy as a systemd service for lower latency and reduced conntrack usage.

### Ingress and egress

**Ingress — transitioning away from NGINX**: NGINX Ingress Controller is being retired (March 2026 announcement). Moving to **Gateway API** as the long-term standard, via the application routing add-on with Istio control plane. For new L7 ingress with WAF: **Application Gateway for Containers** supports Gateway API natively.

**Egress control options**:
- Default `loadBalancer`: creates public IP for SNAT. Simplest but least controlled.
- **Azure Firewall with UDR** (`userDefinedRouting`): FQDN filtering, compliance, full visibility.
- **NAT Gateway** (StandardV2): simpler IP management without FQDN filtering.

Required AKS egress destinations: `*.azmk8s.io:443`, `mcr.microsoft.com:443`, `management.azure.com:443`, `login.microsoftonline.com:443`.

**Load balancer decision tree**:
- HTTP/S global workloads → Azure Front Door (with Private Link to AKS internal LB)
- Regional L7 with WAF → Application Gateway
- Non-HTTP protocols → Azure Load Balancer Standard
- DNS-based multi-region → Traffic Manager

## SPIFFE/SPIRE: cryptographic workload identity

**IP addresses are not identity** in dynamic environments. Pod IPs change with every restart. VMs are ephemeral. IP-based ACLs become stale within minutes.

**SPIFFE** (CNCF graduated) solves this with a universal identity format: `spiffe://trust-domain/workload-identifier` (e.g., `spiffe://acme.com/ns/payments/sa/payment-processor`).

Identity is encoded in a cryptographically verifiable document called an **SVID**:
- **X.509 SVID** (preferred): used for mTLS between services
- **JWT SVID**: used when mTLS is not possible

SVIDs are short-lived (typically 1 hour), automatically rotated, and issued without static secrets.

**SPIRE architecture**:
- **SPIRE Server** (StatefulSet): central authority, signs SVIDs, manages the trust domain
- **SPIRE Agents** (DaemonSet on every node): expose the Workload API via Unix domain socket, perform attestation

**Two-phase attestation**:
1. Agent proves node identity (using AWS Instance Identity Documents, Kubernetes service account tokens, GCP Identity Tokens)
2. When a workload requests identity, Agent inspects kernel metadata (cgroups, PID, container properties) and matches against registration entries mapping workload properties to SPIFFE IDs

In AKS, **Microsoft Entra Workload Identity** provides federated identity credentials. The cluster exposes an OIDC issuer endpoint; a trust relationship links Kubernetes ServiceAccounts to Entra managed identities; pods receive projected tokens exchanged for Entra tokens to access Azure resources.

## Zero Trust networking in production

**BeyondCorp principles** (Google, 2011): connecting from a particular network must not determine accessible services; access is granted based on user and device context; all access must be authenticated, authorized, and encrypted.

**NIST SP 800-207** (2020) seven tenets:
1. All data sources and computing services are resources requiring authenticated access
2. All communication is secured regardless of location (no trusted network)
3. Access is per-session, not per-user
4. Access is dynamically determined by policy
5. The enterprise monitors and measures integrity of all assets
6. Authentication and authorization are dynamic and strictly enforced
7. Maximum information collected about current state of assets, infrastructure, and communications

**NIST SP 800-207A** (2023) extended this to cloud-native applications, explicitly recommending service meshes, SPIFFE identity, and sidecar proxies.

**CISA 2025 "Journey to Zero Trust Microsegmentation"**: recommends phased adoption with attribute-based (not IP-based) access rules.

### Default-deny network policy pattern

```yaml
# Start with default deny for all ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
# Then allow DNS (required for service discovery)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
spec:
  podSelector: {}
  egress:
  - ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

Layer incrementally: allow DNS first → add namespace isolation via namespaceSelector → add pod-level microsegmentation for specific service-to-service flows → add FQDN-based egress policies → add L7 HTTP method/path filtering with Cilium.

Use **Hubble** to observe actual traffic flows before writing restrictive policies.

### mTLS implementation comparison (latency overhead)

From academic benchmarking (arXiv:2411.02267):
- Istio sidecar: **166%** overhead
- Cilium: **99%** overhead
- Linkerd: **33%** overhead
- Istio Ambient: **8%** overhead

Sidecarless architectures show dramatic advantages. For AKS, Cilium mTLS (public preview) uses ztunnel + SPIRE with TLS 1.3 sessions for transparent pod-to-pod encryption.

## Service meshes: when to use which

**Istio** (Google/IBM/Lyft): most feature-rich. Envoy proxies as sidecars, istiod as control plane. Newer Ambient Mesh eliminates per-pod sidecars using node-level ztunnels (L4) and optional waypoint proxies (L7), reducing resource overhead by up to 92%. The Istio add-on for AKS is GA (revisions asm-1-25 through asm-1-28).

**Linkerd** (Buoyant, CNCF graduated): Rust-based proxy consuming only ~10MB RAM per instance — roughly 8× more efficient than Istio's Envoy. Trades feature breadth for operational simplicity. Enables mTLS by default with zero configuration.

**Cilium Service Mesh**: use if already using Cilium CNI. No additional infrastructure. L4 mTLS via ztunnel, L7 via waypoint proxies. Hubble observability included.

**Decision rule**: use Cilium if already on Cilium CNI; use Linkerd for lowest overhead with minimal features; use Istio for maximum features and multi-cluster support.

## Network observability

**Monitoring** asks "is it working?" **Observability** asks "why is it behaving this way?" In distributed systems, the difference is existential.

### Network SLO targets

| Tier | Availability SLO | Downtime/month |
|------|-----------------|----------------|
| Ultra-critical (payments) | 99.99% | 4.4 minutes |
| Tier-1 services | 99.9% | 43.8 minutes |
| Important, non-critical | 99.5% | 3.6 hours |

Key SLIs: packet loss rate, RTT at p50/p95/p99, DNS resolution time, connection establishment time. Latency SLOs: p95 < 200ms and p99 < 500ms for critical paths.

**Multi-burn-rate alerting** is the gold standard:
- Fast burn (2% budget consumed in 1 hour): P0
- Medium burn (5% in 6 hours): P1
- Slow burn (10% in 3 days): P2

When budget is exhausted: feature freeze.

### Observability stack for AKS

**ACNS (Advanced Container Networking Services)**: enterprise-grade network observability for both Cilium and non-Cilium clusters. Includes container network metrics, network logs (source/destination IPs, ports, protocols, flow direction), and pre-configured Azure Managed Grafana dashboards for DNS, pod flows, drops, and L7 traffic.

**Hubble** (automatically enabled with ACNS on Cilium clusters):
- `hubble observe --namespace payments` — real-time flow visibility
- `hubble observe --verdict DROPPED` — see all dropped packets and why
- DNS latency metrics per service

**Retina** (retina.sh): open-source eBPF-based observability, CNI-agnostic.

**OpenTelemetry**: vendor-neutral APIs and SDKs for traces, metrics, and logs. OTel Collector acts as telemetry pipeline (receivers, processors, exporters). OTLP over gRPC (port 4317) or HTTP (port 4318). W3C TraceContext headers for distributed trace propagation.

**Cardinality explosion warning**: in cloud-native environments, every unique combination of metric labels creates a separate time series. 20,000 metrics in a monolith can become 800 million in microservices. Never use unbounded values (user IDs, request IDs) as metric labels.

## Chaos engineering for networks

**Steady-state hypothesis**: define what "normal" looks like before injecting failures. Abort criteria: stop experiment if specific conditions are breached. Blast radius limiting: start with a small subset of traffic or pods.

**Chaos Mesh** (CNCF incubating): Kubernetes-native network chaos via CRDs. Can inject latency, packet loss, network partitions, bandwidth throttling.

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: payment-latency-test
spec:
  action: delay
  mode: one
  selector:
    namespaces: [payments]
    labelSelectors:
      app: payment-service
  delay:
    latency: "100ms"
    correlation: "25"
    jitter: "10ms"
  duration: "10m"
```

Linux `tc/netem` is the kernel-level foundation for network emulation. The key insight from Google's SRE practice: chaos experiments must be grounded in SLO preservation, not just recovery testing.

## Python network automation

### The essential toolkit (2026 versions)

**Nornir 3.5.0** (Python 3.9+): pure-Python automation framework. Benchmarks at roughly **100× faster than Ansible** for network device operations, using multi-threaded task execution with plugin architecture (nornir-netmiko, nornir-scrapli, nornir-napalm).

**Scapy 2.7.0**: gold standard for packet crafting, analysis, and protocol research. Replaces ~85% of nmap, hping, arpspoof, and tcpdump functionality in a single library.

**Netmiko 4.6.0**: supports ~80 device types across Cisco, Arista, Juniper, Nokia, Fortinet, Palo Alto. Abstracts SSH through Paramiko.

**NAPALM ~5.0.0**: vendor-neutral API for configuration management — diff, rollback, validation — across Cisco IOS/IOS-XR/NX-OS, Arista EOS, Juniper Junos.

**AsyncSSH 2.22.0** / **Scrapli**: use for managing hundreds to thousands of concurrent connections. Use Paramiko/Netmiko for standard device automation; use AsyncSSH or Scrapli for massive concurrency.

**pygnmi 0.8.15**: gNMI Get/Set/Subscribe for streaming telemetry subscriptions.

### Async automation pipeline for 1000+ devices

The gold-standard four-stage pattern: Inventory (NetBox API) → Dispatcher (Nornir filtering by site/role) → Workers (ThreadPoolRunner with 50-100 threads) → Aggregator (structured JSON/DB results with validation).

```python
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio

sem = asyncio.Semaphore(50)  # Max 50 concurrent connections

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=30))
async def configure_device(device):
    async with sem:
        async with asyncssh.connect(device['host']) as conn:
            result = await conn.run('show version')
            return result.stdout
```

Rate limiting uses `asyncio.Semaphore`. Error handling uses **tenacity** with exponential backoff. Python 3.11+'s `asyncio.TaskGroup` enables structured concurrency with `except*` for handling multiple failures.

### CI/CD validation pipeline

**Batfish**: gold standard for offline network configuration validation. Builds mathematical models from device configs and validates BGP sessions, ACL rules, and routing behavior without touching live devices.

Pipeline: Git push → lint configs → Batfish pre-deployment validation → deploy to staging via Nornir → pytest network assertions → production deploy with approval gate.

## The five convergent gold standards for 2026

1. **eBPF has replaced iptables** as the production data plane — Cilium in Kubernetes, Katran for load balancing, XDP for DDoS mitigation.

2. **Workload identity (SPIFFE/SPIRE, Entra Workload ID) has replaced network identity** as the authentication primitive. Cryptographic proof, not IP address, determines access.

3. **Overlay networking (Azure CNI Overlay, EVPN-VXLAN)** has decoupled pod/workload addressing from physical infrastructure, solving IP exhaustion.

4. **Segment Routing (SRv6)** is replacing MPLS as the carrier-grade forwarding plane, driven by 5G slicing and hyperscale AI networks.

5. **Gateway API is succeeding the Ingress specification** as the Kubernetes traffic management standard, with NGINX Ingress Controller entering retirement.

**The definitive AKS production stack**: Azure CNI Overlay + Cilium data plane + ACNS + Entra Workload Identity + cert-manager + Azure Firewall Premium for egress + Azure Front Door for ingress + Hubble/Grafana for observability.

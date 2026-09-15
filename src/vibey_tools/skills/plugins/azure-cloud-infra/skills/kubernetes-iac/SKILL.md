---
name: kubernetes-iac
description: Use whenever working with Kubernetes infrastructure-as-code, AKS provisioning, Helm charts, Kustomize overlays, GitOps with Flux or ArgoCD, Terraform for AKS, Bicep for Azure resources, or AKS security hardening. Triggers on any AKS, Kubernetes IaC, GitOps, or cluster configuration request.
---

# Kubernetes IaC for AKS: Comprehensive Reference

## Core Principle: Separation of Concerns

**Platform IaC** (Terraform/Bicep for AKS cluster, VNet, ACR, Key Vault) and **Application IaC** (Helm/Kustomize for workload manifests) operate on completely different lifecycles, use different tools, require different credentials, and must live in **separate repositories with separate pipelines**.

| Dimension | Platform IaC | Application IaC |
|---|---|---|
| Changes | Infrequently (cluster upgrades, networking) | Daily (app deployments) |
| Blast radius | High — can destroy the cluster | Namespace-scoped |
| Credentials | Cloud-provider credentials (Terraform/Bicep) | Cluster credentials only |
| Owner | Platform team | Application teams |
| Tools | Terraform, Bicep | Helm, Kustomize |

**Never mix platform and app resources in one Terraform state.** An application change must never be able to accidentally destroy the cluster.

---

## GitOps: The Operational Model

GitOps extends declarative IaC to operations via four principles:
1. **Git as single source of truth** for all desired state
2. **Pull-based deployment** — in-cluster agent pulls changes (eliminates stored cluster credentials in CI)
3. **Continuous reconciliation** — automatically corrects drift
4. **Declarative descriptions** for everything

### Flux CD v2 vs ArgoCD — When to Choose Each

| Aspect | Flux CD v2 | ArgoCD |
|---|---|---|
| UI | None (CLI only) | Rich web dashboard with app visualization, diff views |
| Architecture | Modular Kubernetes-native controllers | Monolithic with CRDs |
| SOPS secrets | Native integration | Requires plugins |
| Kustomize + Helm | kustomize-controller as post-renderer (unique capability) | Separate paths |
| Multi-cluster | Supported | ApplicationSets with generators (Git directory, cluster, list, matrix) |
| After Weaveworks shutdown | Continues under AWS, Microsoft, community | Stable, CNCF graduated |

**Choose ArgoCD** for teams wanting UI-driven operations and easier onboarding. **Choose Flux** for platform teams wanting composable, Kubernetes-native controllers with tighter GitOps purity and native SOPS encryption.

### GitOps Repository Structure

Separate application source repos from GitOps config repos:
- **App repo**: source code + Dockerfile; CI builds images and updates the config repo
- **Config repo**: Kubernetes manifests; GitOps agent deploys from here

**Directory-based promotion on a single branch** (not branch-per-environment):
```
config-repo/
├── envs/
│   ├── dev/          # kustomization.yaml pointing to base + dev overlay
│   ├── staging/
│   └── prod/
├── base/             # shared manifests
└── platform/         # cluster-level config (RBAC, namespaces, network policies)
```

Promotion = copying version information between directories via PR. Clear visibility, easy rollback via `git revert`, no merge conflicts between environments.

---

## Helm Chart Design

### Chart Structure
```
my-chart/
├── Chart.yaml          # metadata, version, appVersion
├── values.yaml         # defaults
├── values.schema.json  # validation schema (ALWAYS include)
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── _helpers.tpl    # reusable named templates
│   └── NOTES.txt
├── charts/             # chart dependencies
└── .helmignore
```

### values.schema.json — Catch Misconfigurations Early

Helm validates values against this schema at install/upgrade time before anything reaches the cluster:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "replicaCount": {
      "type": "integer",
      "minimum": 1
    },
    "image": {
      "type": "object",
      "properties": {
        "repository": { "type": "string" },
        "tag": { "type": "string" }
      },
      "required": ["repository", "tag"]
    }
  },
  "required": ["replicaCount", "image"]
}
```

### _helpers.tpl — Naming and Labels

Define common labels, selectors, and naming in `_helpers.tpl` and reference with `{{ include "mychart.labels" . | nindent 4 }}`. This ensures consistency and enables upgrades to find existing resources.

### Versioning and Registries

- Follow SemVer 2.0.0 strictly: MAJOR for breaking value schema changes, MINOR for new features, PATCH for fixes
- Push charts to OCI-based registries (ACR, GHCR): `helm push mychart-1.0.0.tgz oci://myregistry.azurecr.io/charts`
- Use `helm registry login` with Workload Identity or managed identity credentials

### Anti-Patterns to Avoid

- Over-templating: parameterizing everything "just in case" creates unmaintainable charts
- God charts: one chart for an entire platform with dozens of conditionally-enabled components
- `:latest` tags in default values — breaks reproducibility and rollback
- Not using `.helmignore` — test files bloat packaged charts

---

## Kustomize: Overlays and Patches

### Base + Overlay Pattern

```
kubernetes/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml      # references ../base
    │   └── patches/
    │       └── deployment-replicas.yaml
    ├── staging/
    │   └── kustomization.yaml
    └── prod/
        └── kustomization.yaml
```

**base/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
```

**overlays/prod/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: myapp-prod
resources:
  - ../../base
patches:
  - path: patches/deployment-prod.yaml
images:
  - name: myapp
    newTag: "1.2.3"
```

**Keep namespace declarations out of base resources.** Specify namespaces in overlay `kustomization.yaml` files so the base is reusable across environments without modification.

### ConfigMapGenerator — Automatic Rolling Updates

ConfigMapGenerator creates resources with content-hash suffixed names, automatically triggering rolling updates when content changes:

```yaml
configMapGenerator:
  - name: app-config
    envs:
      - .env.prod
    literals:
      - LOG_LEVEL=info

secretGenerator:
  - name: db-credentials
    files:
      - password.txt
```

This is a critical advantage over manually managed ConfigMaps — no more "did the deployment pick up the config change?"

### Strategic Merge Patches

```yaml
# patches/deployment-prod.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: myapp
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            memory: "512Mi"
```

### Kustomize + Helm Combined

Flux's kustomize-controller can post-render Helm output with Kustomize patches — combine both tools in a single pipeline. Use Helm for third-party charts (Prometheus, NGINX, cert-manager) and Kustomize for overlaying environment-specific patches.

---

## Terraform for AKS Provisioning

### Module Structure (Preferred Over Workspaces)

**Directory-based separation is preferred over workspaces for production** — workspaces create risk of applying to the wrong environment.

```
infrastructure/
├── modules/
│   ├── vnet/           # VNet, subnets, NSGs
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── aks/            # AKS cluster, node pools
│   ├── acr/            # Azure Container Registry
│   ├── keyvault/       # Key Vault + RBAC
│   └── monitoring/     # Log Analytics, Managed Prometheus
└── environments/
    ├── dev/
    │   └── main.tf     # composes modules with dev values
    ├── staging/
    └── prod/
```

Each environment root module composes the modules with different variable values. Bridge environments via Terraform outputs consumed by application configuration.

### Remote State in Azure Blob Storage

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stterraformstate"
    container_name       = "tfstate"
    key                  = "prod/aks.tfstate"
  }
}
```

Azure Blob Storage natively supports state locking via blob leases — no extra configuration needed. Enable blob versioning for rollback. One state file per environment prevents cross-environment blast radius.

### OIDC Authentication for CI/CD (No Stored Secrets)

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=4.14.0"    # Pin exactly; commit .terraform.lock.hcl
    }
  }
}

provider "azurerm" {
  features {}
  use_oidc = true  # Uses OIDC federated credentials from GitHub Actions
}
```

### AKS Cluster Module Example

```hcl
module "aks" {
  source = "../../modules/aks"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  cluster_name        = "aks-${var.environment}"

  # System node pool
  system_node_count  = 3
  system_vm_size     = "Standard_D4s_v5"
  availability_zones = ["1", "2", "3"]

  # Networking — Azure CNI Overlay with Cilium (recommended for new clusters)
  vnet_subnet_id     = module.vnet.aks_subnet_id
  network_plugin     = "azure"
  network_plugin_mode = "overlay"
  network_dataplane  = "cilium"

  # Identity — user-assigned for pre-provisioned role assignments
  identity_type      = "UserAssigned"
  user_assigned_identity_id = azurerm_user_assigned_identity.aks.id

  # Security
  enable_oidc_issuer       = true
  enable_workload_identity = true
  azure_rbac_enabled       = true   # Azure RBAC for Kubernetes authorization
  private_cluster_enabled  = true

  # Add-ons
  enable_azure_policy = true
  enable_key_vault_secrets_provider = true
  enable_monitor       = true
}
```

### Azure Verified Modules

The **Azure Verified Modules** (`Azure/avm-ptn-aks-production/azurerm`, released October 2024) provide enterprise-grade, Microsoft-supported AKS provisioning. Use as the starting point for production clusters.

```hcl
module "aks_production" {
  source  = "Azure/avm-ptn-aks-production/azurerm"
  version = "~> 0.1"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  name                = "aks-prod"
}
```

---

## Bicep: Azure-Native Alternative

Bicep requires **no state management** — Azure Resource Manager tracks state directly. Eliminates an entire category of operational concerns (state locking, corruption, storage). Day-zero support for new Azure features.

**When to choose Bicep:** Azure-only teams wanting the simplest experience, teams without Terraform investment.

**When to choose Terraform:** Multi-cloud environments, non-Azure resources (Datadog, GitHub, DNS providers), or teams with existing Terraform investment.

```bicep
param location string = resourceGroup().location
param clusterName string

resource aks 'Microsoft.ContainerService/managedClusters@2024-02-01' = {
  name: clusterName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${aksIdentity.id}': {}
    }
  }
  properties: {
    agentPoolProfiles: [
      {
        name: 'system'
        count: 3
        vmSize: 'Standard_D4s_v5'
        mode: 'System'
        osType: 'Linux'
        availabilityZones: ['1', '2', '3']
        enableAutoScaling: true
        minCount: 3
        maxCount: 9
        nodeTaints: ['CriticalAddonsOnly=true:NoSchedule']
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      networkPluginMode: 'overlay'
      networkDataplane: 'cilium'
    }
    oidcIssuerProfile: { enabled: true }
    securityProfile: { workloadIdentity: { enabled: true } }
    enableRBAC: true
    aadProfile: {
      managed: true
      enableAzureRBAC: true
    }
  }
}
```

Use `az deployment group what-if` for plan-equivalent previews before applying.

---

## AKS Security Hardening

### Pod Security Standards (Replace Deprecated PSPs)

Enforce the **Restricted** profile on all production namespaces:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: myapp-prod
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.28
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

A Restricted-compliant pod security context:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault
```

Migrate gradually: set `warn` and `audit` modes first, then switch to `enforce` after validating workloads.

### Network Policies — Default Deny

Apply a default deny-all NetworkPolicy to every namespace, then explicitly allow required communication:

```yaml
# 1. Default deny all ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress

# 2. Allow DNS (always required)
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

With Cilium on AKS, leverage CiliumNetworkPolicy for L7 and FQDN-based filtering (Azure CNI Overlay + Cilium is the recommended stack for new clusters).

### Workload Identity Setup (Replaces Deprecated Pod Identity)

```bash
# Enable on cluster
az aks update \
  --resource-group myRG \
  --name myAKS \
  --enable-oidc-issuer \
  --enable-workload-identity

# Create user-assigned managed identity
az identity create \
  --name myapp-identity \
  --resource-group myRG

# Get OIDC issuer URL
OIDC_ISSUER=$(az aks show --resource-group myRG --name myAKS \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)

# Create federated credential
az identity federated-credential create \
  --name myapp-federated \
  --identity-name myapp-identity \
  --resource-group myRG \
  --issuer "$OIDC_ISSUER" \
  --subject "system:serviceaccount:myapp:myapp-sa" \
  --audiences api://AzureADTokenExchange
```

Kubernetes service account annotation:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
  namespace: myapp
  annotations:
    azure.workload.identity/client-id: "<managed-identity-client-id>"
```

Pod label to trigger token injection:
```yaml
spec:
  serviceAccountName: myapp-sa
  labels:
    azure.workload.identity/use: "true"
```

### OPA Gatekeeper / Azure Policy

Azure Policy for AKS enforces governance at admission time using built-in initiative including Deployment Safeguards. Key policies to enforce:

- Require resource limits on containers
- Disallow privileged containers
- Require non-root user
- Require readOnlyRootFilesystem
- Restrict allowed registries (only pull from ACR)
- Enforce image signing (via Ratify + cosign)

Enable via Terraform:
```hcl
resource "azurerm_kubernetes_cluster" "main" {
  # ...
  azure_policy_enabled = true
}
```

### Container Scanning — Trivy

Run Trivy in CI/CD pipeline to fail builds on CRITICAL/HIGH findings:

```yaml
- name: Scan container image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'myapp:${{ github.sha }}'
    format: 'sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'
    output: 'trivy-results.sarif'

- name: Upload Trivy scan results
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: 'trivy-results.sarif'
  if: always()
```

Deploy Trivy Operator for continuous in-cluster scanning of running workloads.

### Private Cluster Configuration

Production AKS clusters should use API server VNet integration — control plane accessible only from private network:

```hcl
resource "azurerm_kubernetes_cluster" "main" {
  private_cluster_enabled             = true
  private_cluster_public_fqdn_enabled = false
  api_server_access_profile {
    vnet_integration_enabled = true
    subnet_id                = azurerm_subnet.apiserver.id
  }
}
```

For management access use Azure Bastion for SSH tunneling, or `az aks command invoke` to run kubectl without direct network access.

---

## Node Pool Design

Production AKS clusters must **separate system and user node pools**:

```hcl
# System node pool — only critical add-ons
resource "azurerm_kubernetes_cluster" "main" {
  default_node_pool {
    name                        = "system"
    vm_size                     = "Standard_D4s_v5"
    node_count                  = 3
    zones                       = ["1", "2", "3"]
    only_critical_addons_enabled = true  # Taint: CriticalAddonsOnly=true:NoSchedule
    os_sku                      = "AzureLinux"
  }
}

# User node pool — application workloads
resource "azurerm_kubernetes_cluster_node_pool" "user" {
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  name                  = "user"
  vm_size               = "Standard_D8s_v5"
  min_count             = 3
  max_count             = 20
  enable_auto_scaling   = true
  zones                 = ["1", "2", "3"]
  os_sku                = "AzureLinux"
}
```

**Azure Linux 2.0 reaches EOL in November 2025. Migrate to AzureLinux 3 before March 2026.**

Kubenet is deprecated with removal scheduled March 2028. **Azure CNI Overlay powered by Cilium** is the recommended networking stack for new clusters — 30% reduction in service routing latency, replaces kube-proxy with eBPF, built-in network policy.

---

## Upgrade Strategy

Use both cluster auto-upgrade and node OS auto-upgrade with separate maintenance windows:

```hcl
resource "azurerm_kubernetes_cluster" "main" {
  automatic_upgrade_channel  = "stable"  # Auto-upgrade to latest patch of N-1 minor version
  node_os_upgrade_channel    = "NodeImage"

  maintenance_window_auto_upgrade {
    frequency   = "Weekly"
    interval    = 1
    duration    = 4
    day_of_week = "Sunday"
    start_time  = "02:00"
    utc_offset  = "+00:00"
  }

  maintenance_window_node_os {
    frequency   = "Weekly"
    interval    = 1
    duration    = 4
    day_of_week = "Wednesday"
    start_time  = "02:00"
    utc_offset  = "+00:00"
  }
}
```

Configure surge upgrades on node pools (`max_surge = "33%"`) to provision extra nodes during rolling upgrades. Always define PodDisruptionBudgets — misconfigured PDBs block the entire upgrade process.

---

## Environment Promotion Pattern

**Dev → Staging → Prod via overlay promotion:**

1. CI builds image, tags it with git SHA: `myapp:abc1234`
2. CI updates the image tag in `envs/dev/kustomization.yaml` via PR
3. GitOps agent deploys to dev
4. Validate in dev, promote: update `envs/staging/kustomization.yaml` via PR
5. Validate in staging, promote: update `envs/prod/kustomization.yaml` via PR with required approvals

**With ArgoCD ApplicationSets:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp
spec:
  generators:
  - list:
      elements:
      - cluster: dev
        url: https://dev-aks.example.com
      - cluster: staging
        url: https://staging-aks.example.com
      - cluster: prod
        url: https://prod-aks.example.com
  template:
    metadata:
      name: 'myapp-{{cluster}}'
    spec:
      source:
        repoURL: https://github.com/myorg/config-repo
        path: 'envs/{{cluster}}'
      destination:
        server: '{{url}}'
        namespace: myapp
```

---

## Production Workload Checklist

Every production Deployment should have:

- Minimum 3 replicas
- PodDisruptionBudget with `maxUnavailable: 1` (never `maxUnavailable: 0` — blocks cluster upgrades)
- HPA with stabilization windows to prevent flapping
- Topology spread across zones (`DoNotSchedule`) and nodes (`ScheduleAnyway`)
- All three probe types: startup (`failureThreshold: 60`, slow start tolerance), liveness (lightweight self-check only, never check external deps), readiness (checks dependencies, removes from Service endpoints)
- Resource requests always set; memory limits always set; CPU limits not set (causes CFS throttling)
- Non-root user, readOnlyRootFilesystem, no privilege escalation, drop ALL capabilities
- Dedicated ServiceAccount with `automountServiceAccountToken: false`
- ServiceMonitor for Prometheus scraping
- Distroless or Chainguard base images (no shell, no package manager)
- Images pinned by digest, not tag: `myapp@sha256:abc123...`

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    memory: "256Mi"    # Always set memory limit
    # No CPU limit — allow bursting to avoid CFS throttling
```

---

## Secret Management Options

Three approaches for different needs:

1. **External Secrets Operator (ESO)** — recommended for GitOps. Synchronizes secrets from Azure Key Vault into Kubernetes Secrets via ExternalSecret CRDs safe to commit to Git. Authenticate to Key Vault using Workload Identity.

2. **Azure Key Vault CSI Driver** — mounts secrets directly as CSI volumes (secrets never stored in etcd). Ideal when avoiding Kubernetes Secrets entirely. Enable with `enable_key_vault_secrets_provider = true` in Terraform.

3. **SOPS with Azure Key Vault** — encrypts secret values while keeping keys readable. Perfect for GitOps diffs. Native Flux support. Keys are readable in Git; only values are encrypted.

Never store unencrypted secrets in Git. Four defense layers: pre-commit hooks with gitleaks, CI gitleaks scanning, SOPS encryption, ExternalSecret CRDs as the primary pattern.

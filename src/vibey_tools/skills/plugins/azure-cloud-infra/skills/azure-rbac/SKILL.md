---
name: azure-rbac
description: Use whenever working with Azure Role-Based Access Control, Azure resource permissions, service principals, managed identities, scope hierarchy, control plane vs data plane authorization, AKS RBAC, or GitHub Actions Azure authentication. Triggers on any question about who can do what on Azure resources.
---

# Azure RBAC: Comprehensive Reference and Patterns

## The Four Pillars

Every Azure RBAC operation resolves to four interlocking concepts:

1. **Security principal** — the identity requesting access. Four types:
   - **User** — individual Entra ID profile (including B2B guests)
   - **Group** — Entra ID group; role assignments are transitive through nested groups
   - **Service principal** — application identity for code and automation
   - **Managed identity** — Azure-managed service principal with automatic credential lifecycle

2. **Role definition** — a named collection of permissions specifying allowed operations at control and data planes. Azure ships 250+ built-in roles; tenants can create up to 5,000 custom roles.

3. **Scope** — the boundary where access applies. Strict hierarchy: **management group → subscription → resource group → resource**. Permissions cascade downward automatically.

4. **Role assignment** — binds one role definition to one security principal at one scope. Permissions are the additive union of all assignments. There is no implicit deny.

---

## Control Plane vs Data Plane — The #1 Production Incident Source

Azure operations split into two layers that NEVER cross:

**Control plane** — requests to `https://management.azure.com`. Creates, configures, and deletes Azure resources. ARM handles authorization.

**Data plane** — requests to resource-specific endpoints (`https://myaccount.blob.core.windows.net`, `https://myvault.vault.azure.net`). Uses the capabilities of a resource.

### THE CRITICAL RULE: `*` in Actions does NOT grant DataActions

Owner has `Actions: ["*"]`. Owner can fully manage a storage account but **cannot read a single blob** without an additional data plane role. This catches even experienced engineers.

| Control plane role | Data plane role | Resource |
|---|---|---|
| Storage Account Contributor | Storage Blob Data Contributor | Blob Storage |
| Key Vault Contributor | Key Vault Secrets User | Key Vault |
| Cosmos DB Contributor | Cosmos DB Built-in Data Contributor | Cosmos DB |
| Cognitive Services Contributor | Cognitive Services OpenAI User | Azure OpenAI |

**Always assign data plane roles alongside control plane roles when workloads need to access resource data.**

---

## Scope Hierarchy and Inheritance

```
/providers/Microsoft.Management/managementGroups/<mgId>     ← management group
/subscriptions/<subId>                                       ← subscription
/subscriptions/<subId>/resourceGroups/<rgName>              ← resource group
/subscriptions/<subId>/resourceGroups/<rgName>/providers/   ← resource
  <provider>/<type>/<name>
```

Inheritance flows strictly downward. You **cannot break inheritance** the way NTFS permissions can be severed. The only mechanism to block inherited permissions is a **deny assignment**, which only Azure itself can create (via Deployment Stacks, managed applications, Service Fabric managed clusters).

### Hard limits (cannot be increased)
- 4,000 role assignments per subscription
- 500 role assignments per management group
- PIM eligible assignments do NOT count toward these limits
- Management group scope assignments do NOT count against per-subscription limits

---

## Built-In Role Catalog: Key Roles

### Privileged roles
| Role | GUID | Key permissions |
|---|---|---|
| **Owner** | `8e3af657-a8ff-443c-a75c-2fe8c4bcb635` | `Actions: ["*"]` — full management + role assignment |
| **Contributor** | `b24988ac-6180-42a0-ab88-20f7382dd24c` | `Actions: ["*"]` minus authorization writes. Cannot assign roles. |
| **Reader** | `acdd72a7-3385-48ef-bd42-f606fba81ae7` | `Actions: ["*/read"]` — no data plane access |
| **User Access Administrator** | `18d7d88d-d35e-4fb5-a5c3-7773c20a72d9` | Manage RBAC only |
| **Role Based Access Control Administrator** | `f58310d9-a9f6-439a-9e8d-f62e7b41a168` | Narrower UAA alternative; supports ABAC conditions |

### Storage roles
| Role | Plane | Key capability |
|---|---|---|
| Storage Account Contributor | Control | Manage accounts; can retrieve keys |
| Storage Blob Data Owner | Data | Full blob CRUD + ACL owner (ADLS Gen2 super-user) |
| Storage Blob Data Contributor | Data | Read/write/delete blobs and containers |
| Storage Blob Data Reader | Data | Read and list blobs/containers |

### Key Vault roles
| Role | Plane | Scope |
|---|---|---|
| Key Vault Contributor | Control ONLY | Manage vault resource, NOT access secrets/keys |
| Key Vault Secrets User | Data | Read secret contents only |
| Key Vault Secrets Officer | Data | Full CRUD on secrets |
| Key Vault Administrator | Data | All data plane operations |

### AKS roles — two separate systems
**ARM-level (control plane for the AKS resource):**
| Role | GUID | Grants |
|---|---|---|
| AKS Cluster Admin Role | `0ab0b1a8-8aac-4efd-b8c2-3ee1fb270be8` | Retrieves admin kubeconfig with `cluster-admin` binding |
| AKS Cluster User Role | `4abbcc35-e782-43d8-92c5-2d3f1bd2253f` | Retrieves user kubeconfig (required for `az aks get-credentials`) |

**Kubernetes data plane (DataActions):**
| Role | Access level |
|---|---|
| AKS RBAC Cluster Admin | Super-user — all resources in all namespaces |
| AKS RBAC Admin | Admin within namespace |
| AKS RBAC Writer | Read/write most objects including Secrets |
| AKS RBAC Reader | Read-only; cannot view Secrets |

Scope Azure RBAC assignments to a specific Kubernetes namespace:
```bash
az role assignment create --role "AKS RBAC Writer" \
  --assignee <AAD-ENTITY-ID> \
  --scope "$AKS_ID/namespaces/my-namespace"
```

### Cosmos DB — data plane is its own RBAC system
Cosmos DB data plane RBAC is **not standard Azure RBAC**. Built-in data roles:
- `00000000-0000-0000-0000-000000000001` — Cosmos DB Built-in Data Reader
- `00000000-0000-0000-0000-000000000002` — Cosmos DB Built-in Data Contributor

Assign with `az cosmosdb sql role assignment create`. Not available in the Azure portal.

```bash
az cosmosdb sql role assignment create \
  --account-name myCosmosAccount --resource-group myRG \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id "<managed-identity-object-id>" --scope "/"
```

---

## Role Definition Structure

```json
{
  "Name": "VM Operator",
  "IsCustom": true,
  "Description": "Can monitor, start, restart, and stop VMs. Cannot create or delete.",
  "Actions": [
    "*/read",
    "Microsoft.Compute/virtualMachines/start/action",
    "Microsoft.Compute/virtualMachines/restart/action",
    "Microsoft.Compute/virtualMachines/deallocate/action"
  ],
  "NotActions": [],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/<subscription-id>"
  ]
}
```

Action strings: `{Company}.{ProviderName}/{resourceType}/{action}`. Wildcards supported. `NotActions` is NOT a deny — it subtracts from wildcards but can be overridden by another role assignment.

Custom role limits:
- 5,000 per Entra tenant
- `AssignableScopes` cannot use root (`/`) — only built-in roles
- Only one management group allowed in `AssignableScopes`
- Custom roles with `DataActions` cannot be assigned at management group scope

---

## Managed Identity Patterns — Zero-Credential Architecture

Managed identities eliminate all credentials from Azure workload configurations.

**System-assigned**: tied to resource lifecycle; deleted when resource is deleted. Use when permissions should follow the resource.

**User-assigned**: pre-created, shareable across multiple resources, survives resource deletion. Preferred for production — create with role assignments before cluster provisioning.

```bash
# Create user-assigned managed identity
az identity create --name myapp-identity --resource-group myRG

# Assign a role to it
az role assignment create \
  --assignee-object-id "$(az identity show --name myapp-identity --resource-group myRG --query principalId -o tsv)" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/<sub>/resourceGroups/myRG/providers/Microsoft.Storage/storageAccounts/myStorage"
```

**For AKS workloads** — use Workload Identity (replaces deprecated Pod Identity, EOL September 2025):
1. Enable OIDC issuer and Workload Identity on the cluster
2. Create a user-assigned managed identity with role assignments
3. Create a Kubernetes service account annotated with `azure.workload.identity/client-id`
4. Create a federated identity credential linking the managed identity to the service account
5. Label pods with `azure.workload.identity/use: "true"`

---

## GitHub Actions OIDC Federation (Recommended — No Stored Secrets)

GitHub Actions' built-in OIDC provider issues short-lived JWTs during workflow runs. Entra ID trusts this issuer via a federated credential.

**Setup:**

1. Create an app registration and add a federated credential:
```json
{
    "name": "GitHubActions-Production",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:my-org/my-repo:environment:Production",
    "audiences": ["api://AzureADTokenExchange"]
}
```

2. Assign RBAC roles to the service principal.

3. Configure the workflow:
```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: azure/login@v2
    with:
      client-id: ${{ secrets.AZURE_CLIENT_ID }}
      tenant-id: ${{ secrets.AZURE_TENANT_ID }}
      subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

**Subject claim formats:**
- Branch: `repo:<org>/<repo>:ref:refs/heads/<branch>`
- Tag: `repo:<org>/<repo>:ref:refs/tags/<tag>`
- Environment: `repo:<org>/<repo>:environment:<name>`
- Pull request: `repo:<org>/<repo>:pull-request`

**Critical gotchas:**
- Environment names are case-sensitive
- Wildcards not supported in federated credential properties
- Maximum 20 federated credentials per application
- Audience must be `api://AzureADTokenExchange` for public cloud

**Typical role assignments for a DevOps service principal:**
| Scenario | Role | Scope |
|---|---|---|
| Deploy ARM/Bicep | Contributor | Resource group |
| Deploy ARM/Bicep with role assignments | Contributor + User Access Administrator | Resource group |
| Push to ACR | AcrPush | ACR resource |
| Deploy to AKS | AKS Cluster User + AKS RBAC Writer | AKS resource |
| Access Key Vault secrets | Key Vault Secrets User | Key Vault |
| Access blob storage data | Storage Blob Data Contributor | Storage account |

---

## IaC: Bicep Patterns for Role Assignments

**API version:** `2022-04-01`

```bicep
// Basic role assignment
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, roleDefinitionId)
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'   // ALWAYS specify this
  }
}
```

**Resource-level scoping:**
```bicep
resource blobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, principalId, blobContributorRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
```

**CRITICAL Bicep rules:**
- `name` must be a deterministic GUID using `guid()` with stable seeds (scope ID + principal ID + role definition ID) for idempotency
- Always specify `principalType` — omitting it causes intermittent failures with service principals and managed identities
- Deploying role assignments requires `Microsoft.Authorization/roleAssignments/write` — Contributor alone is NOT sufficient. Use Owner or User Access Administrator.

**Reusable module** (`modules/roleAssignment.bicep`):
```bicep
param principalId string
param roleDefinitionId string
@allowed(['User','Group','ServicePrincipal','ForeignGroup','Device'])
param principalType string = 'ServicePrincipal'

resource role 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, resourceGroup().id, principalId, roleDefinitionId)
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
  }
}
```

---

## IaC: Terraform Patterns

```hcl
resource "azurerm_role_assignment" "example" {
  scope                = data.azurerm_subscription.primary.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.example.principal_id
  principal_type       = "ServicePrincipal"
}
```

**Bulk assignments:**
```hcl
variable "role_assignments" {
  type = map(object({
    principal_id         = string
    role_definition_name = string
    scope                = string
  }))
}

resource "azurerm_role_assignment" "bulk" {
  for_each             = var.role_assignments
  scope                = each.value.scope
  role_definition_name = each.value.role_definition_name
  principal_id         = each.value.principal_id
}
```

**Custom role definition:**
```hcl
resource "azurerm_role_definition" "vm_operator" {
  name        = "vm-operator"
  scope       = data.azurerm_subscription.primary.id
  description = "Can start and restart VMs"

  permissions {
    actions     = ["*/read",
                   "Microsoft.Compute/virtualMachines/start/action",
                   "Microsoft.Compute/virtualMachines/restart/action"]
    not_actions = []
  }

  assignable_scopes = [data.azurerm_subscription.primary.id]
}
```

Use `skip_service_principal_aad_check = true` to avoid AAD replication delays. Import existing assignments with:
```bash
terraform import azurerm_role_assignment.example \
  "/subscriptions/<sub>/providers/Microsoft.Authorization/roleAssignments/<guid>"
```

---

## Azure CLI Quick Reference

```bash
# Create assignment using object ID (faster — bypasses Graph query)
az role assignment create \
  --assignee-object-id "<objectId>" \
  --assignee-principal-type "ServicePrincipal" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>"

# List assignments for a specific principal
az role assignment list --assignee "<principalId>" --scope "<scope>"

# List all Owner assignments on a subscription
az role assignment list --role "Owner" --scope "/subscriptions/<sub>"

# Find action strings for a provider
az provider operation show --namespace Microsoft.Storage
az provider operation show --namespace Microsoft.Compute

# Create custom role from JSON file
az role definition create --role-definition @vm-operator.json
```

---

## Common Mistakes and Production Incidents

**1. Owner can't read blobs** — Owner and Contributor have zero data plane permissions. Always assign the appropriate data plane role alongside control plane roles. Storage Blob Data Contributor for blobs, Key Vault Secrets User for secrets.

**2. Propagation delays** — Role assignment changes take up to 10 minutes to propagate. Managed identities added to groups can take up to 24 hours. Add retry logic with 5–10 minute delays in CI/CD pipelines after role assignment creation.

**3. Missing `principalType` in IaC** — Omitting `principalType` in Bicep/ARM causes intermittent failures. Always specify it explicitly.

**4. Contributor can't deploy role assignments** — Creating `Microsoft.Authorization/roleAssignments` resources requires Owner or User Access Administrator. Contributor alone fails with `AuthorizationFailed`.

**5. Reader exposes too much** — Reader at subscription scope grants access to configurations, network topology, IP ranges, connection strings, and container images. Scope Reader to resource groups or use custom roles with only necessary read actions.

**6. Classic admin roles are retired** — Classic admin roles (Account Administrator, Service Administrator, Co-Administrator) retired August 31, 2024. Migrate to RBAC Owner and remove classic assignments.

**7. Cosmos DB data plane RBAC not in portal** — Cosmos DB's native data plane role assignments cannot be managed through the Azure portal. Use CLI, PowerShell, Bicep, or REST API.

**8. 4,000 limit per subscription** — Strategies: assign roles to groups not individuals, use PIM eligible assignments (don't count), assign at management group scope (don't count against per-sub limit), use ABAC conditions instead of per-resource assignments.

---

## Azure RBAC vs Entra ID Roles

These are completely separate systems:
- **Azure RBAC**: controls access to Azure resources (VMs, storage, networking) via the Azure Resource Manager API (`management.azure.com`)
- **Entra ID roles**: control access to directory objects (users, groups, app registrations) via Microsoft Graph API

The overlap: a Global Administrator can enable "Access management for Azure resources" to grant User Access Administrator at tenant root scope — use only for recovery scenarios.

---

## Best Practices

**Security principals:**
- Always assign roles to groups, not individual users (reduces assignment count, simplifies onboarding/offboarding)
- Prefer user-assigned managed identities over service principals for Azure workloads
- Use system-assigned managed identities only when permissions should be tied to the resource lifecycle

**Privileged access:**
- Limit Owner to 3 or fewer per subscription
- Use PIM eligible assignments for all privileged roles (Owner, User Access Administrator, Contributor at subscription scope)
- Classic admin roles are retired — do not use

**Role design:**
- Use `Role Based Access Control Administrator` over `User Access Administrator` when delegating RBAC management — it supports ABAC conditions preventing privilege escalation
- Use groups over individuals to maximize the value of each role assignment against the 4,000 limit
- Use explicit action strings (not wildcards) for security-sensitive custom roles — wildcards automatically include future operations Microsoft adds to a provider

**ABAC conditions** (GA for Blob and Queue Storage): replace thousands of per-resource assignments with a single conditional assignment scoped by blob index tags, container names, or blob paths.

---

## Auditing: KQL Queries

**Who assigned what role, when:**
```kql
AzureActivity
| where TimeGenerated > ago(30d)
| where OperationNameValue =~ "Microsoft.Authorization/roleAssignments/write"
| where ActivityStatusValue =~ "Start"
| extend props = parse_json(tostring(Properties_d.requestbody))
| extend RoleDef = tostring(props.Properties.RoleDefinitionId)
| extend PrincipalId = tostring(props.Properties.PrincipalId)
| project TimeGenerated, Caller, RoleDef, PrincipalId, ResourceId
```

**Detect all RBAC changes:**
```kql
AzureActivity
| where CategoryValue == "Administrative"
| where OperationNameValue in (
    "Microsoft.Authorization/roleAssignments/write",
    "Microsoft.Authorization/roleAssignments/delete")
| where ActivityStatusValue == "Succeeded"
| project TimeGenerated, Caller, OperationNameValue, ResourceId
| order by TimeGenerated desc
```

**Find unused custom roles:**
```kql
AuthorizationResources
| where type =~ "microsoft.authorization/roledefinitions"
| where tolower(tostring(properties.type)) == "customrole"
| extend rdId = tolower(id)
| join kind=leftouter (
    AuthorizationResources
    | where type =~ "microsoft.authorization/roleassignments"
    | summarize Count = count() by RoleId = tolower(tostring(properties.roleDefinitionId))
) on $left.rdId == $right.RoleId
| where isempty(Count)
| project RoleName = tostring(properties.roleName), rdId
```

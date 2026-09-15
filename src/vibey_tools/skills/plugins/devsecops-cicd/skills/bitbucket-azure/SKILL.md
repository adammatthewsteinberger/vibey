---
name: bitbucket-azure
description: Use when working with Bitbucket Pipelines in Azure/Microsoft environments, or when comparing Bitbucket vs GitHub Actions vs Azure DevOps for CI/CD. Triggers on any Bitbucket Pipelines question, especially regarding Azure authentication, OIDC, deployment environments, or pricing.
---

# Bitbucket Pipelines for Azure Shops: Complete Reference

## TL;DR Decision Guide

**Use Bitbucket Pipelines if:**
- Already committed to the Atlassian/Jira ecosystem
- Azure surface is App Service, AKS, ACR, Static Web Apps
- Acceptable to mitigate the OIDC-to-Azure gap with per-environment service-principal secrets + auto-rotation

**Switch to GitHub Actions or Azure DevOps if:**
- Security posture requires federated identity end-to-end with zero stored secrets
- Need hosted Windows or macOS runners (Bitbucket has Linux-only hosted runners)
- Release pipelines require multi-stage, multi-approver gates with auditable approvals
- DevSecOps requires first-party SCA/secret scanning/SBOM (GitHub Advanced Security)

---

## The Critical Azure OIDC Gap

**Bitbucket Pipelines OIDC tokens CANNOT be used to log into Azure (Entra ID).** This is not a configuration issue — it is an architectural incompatibility confirmed by Atlassian.

Atlassian Team (Theodora Boudale, 27 Feb 2024): *"Bitbucket's OIDC tokens cannot be used for logging in to Azure."*

Feature request BCLOUD-22206 ("Provide native support for authentication using OIDC within the Azure platform") is status **Gathering Interest, Unresolved** as of January 2026. Atlassian has not committed to building this.

**Root cause:** Bitbucket's `sub` claim is not in a stable, predictable subject-identifier format that Entra's federated-credential validator accepts. Entra also rejects Bitbucket's ARI-format audience for public cloud applications:
> "Failed to update federated credential. Expression is not supported for applications in this cloud 'Public' using issuer 'https://api.bitbucket.org/…/pipelines-config/identity/oidc'."

Contrast with GitHub Actions (`azure/login@v1` with federated credentials) and GitLab CI/CD — both federate seamlessly into Entra without stored secrets. Bitbucket cannot.

---

## Mitigation Options for Azure Authentication

### Option A: Per-Environment Service Principal Secrets (Most Common)

Provision one service principal per environment, scoped tightly to a resource group:

```bash
az ad sp create-for-rbac \
  --name bitbucket-prod \
  --role Contributor \
  --scopes /subscriptions/<sub>/resourceGroups/rg-prod
```

Store `AZURE_APP_ID`, `AZURE_PASSWORD`, `AZURE_TENANT_ID` as **deployment variables** (not repository variables) so they are only injected when `deployment: <env>` is on the step:

```yaml
- step:
    name: Deploy to Prod
    deployment: production    # Scopes these variables to this step only
    script:
      - pipe: microsoft/azure-arm-deploy:1.0.0
        variables:
          AZURE_APP_ID: $AZURE_APP_ID
          AZURE_PASSWORD: $AZURE_PASSWORD
          AZURE_TENANT_ID: $AZURE_TENANT_ID
          AZURE_RESOURCE_GROUP: rg-prod
          AZURE_TEMPLATE_LOCATION: infra/main.bicep
```

**Auto-rotate secrets** via a scheduled custom pipeline:
```yaml
custom:
  rotate-azure-credentials:
    - variables:
        - name: TARGET_ENV
          default: prod
          allowed-values: [dev, staging, prod]
    - step:
        script:
          - az login --service-principal -u $AZURE_APP_ID -p $AZURE_PASSWORD --tenant $AZURE_TENANT_ID
          - NEW_SECRET=$(az ad app credential reset --id $AZURE_APP_ID --query password -o tsv)
          - curl -X PUT "https://api.bitbucket.org/2.0/repositories/$BITBUCKET_WORKSPACE/$BITBUCKET_REPO_SLUG/deployments_config/environments/$ENV_UUID/variables/$VAR_UUID" \
              -H "Authorization: Bearer $BITBUCKET_ACCESS_TOKEN" \
              -d "{\"value\": \"$NEW_SECRET\", \"secured\": true}"
```

### Option B: Token Broker Azure Function (Recommended for Zero Long-Lived Secrets)

Build an Azure Function that:
1. Validates the incoming `BITBUCKET_STEP_OIDC_TOKEN` against Bitbucket's JWKS endpoint
2. Verifies expected claims: `workspaceUuid`, `repositoryUuid`, `deploymentEnvironmentUuid`
3. On success, mints a short-lived (1-hour) client secret on a per-environment App Registration
4. Returns temporary credentials to the pipeline

```yaml
- step:
    oidc: true    # Enables BITBUCKET_STEP_OIDC_TOKEN in this step
    deployment: production
    script:
      # Exchange Bitbucket OIDC token for short-lived Azure credentials
      - |
        CREDS=$(curl -s -X POST "https://token-broker.azurewebsites.net/api/exchange" \
          -H "Content-Type: application/json" \
          -d "{\"oidcToken\": \"$BITBUCKET_STEP_OIDC_TOKEN\", \"environment\": \"production\"}")
        export AZURE_APP_ID=$(echo $CREDS | jq -r '.clientId')
        export AZURE_PASSWORD=$(echo $CREDS | jq -r '.clientSecret')
        export AZURE_TENANT_ID=$(echo $CREDS | jq -r '.tenantId')
      - az login --service-principal -u $AZURE_APP_ID -p $AZURE_PASSWORD --tenant $AZURE_TENANT_ID
```

The token broker validates Bitbucket OIDC (which works fine for non-Azure targets) and then uses a "Management App" with `Application.ReadWrite.OwnedBy` to mint short-lived credentials. Treat the Function as security-critical: rate-limit by repository UUID, log every exchange to a Sentinel workspace.

### Option C: Azure Pipelines as Orchestrator

Keep Bitbucket as code host but run deployment legs on Azure Pipelines with its native workload-identity service connection:

- Bitbucket Cloud is a first-class repository type in Azure Pipelines (YAML pipelines + PR triggers supported)
- Azure Pipelines builds the **latest commit on the PR source branch** (not merge commit — Bitbucket Cloud doesn't expose merge-commit info via API)
- Keep CI (build, test, lint) on Bitbucket Pipelines; run deployment legs on Azure Pipelines

### Option D: HashiCorp Vault as Intermediary

Bitbucket OIDC works fine with Vault (unlike Azure). Use Vault's `azure` secrets engine:

```yaml
- step:
    oidc: true
    script:
      - vault login -method=jwt jwt=$BITBUCKET_STEP_OIDC_TOKEN role=bitbucket-deployer
      - AZURE_CREDS=$(vault read azure/creds/deployer -format=json)
      - export AZURE_APP_ID=$(echo $AZURE_CREDS | jq -r '.data.client_id')
      - export AZURE_PASSWORD=$(echo $AZURE_CREDS | jq -r '.data.client_secret')
```

---

## Pipeline Model and Core Mechanics

### Single-File Structure

Everything in `bitbucket-pipelines.yml` at the repo root. Unlike GitHub Actions (multiple `.github/workflows/*.yml` files), Bitbucket uses a single file. YAML anchors and the new shared-config import mechanism mitigate duplication.

```yaml
image: atlassian/default-image:4    # Default Docker image for all steps

definitions:
  caches:
    custom-cache: ./build-cache     # Custom path-based cache
  services:
    docker:
      memory: 3072                  # Increase beyond default 1 GB for image builds
    postgres:
      image: postgres:16
      variables:
        POSTGRES_PASSWORD: testpw

pipelines:
  default:                          # Runs on push to any branch not matched below
    - step:
        script:
          - echo "build and test"

  branches:
    main:
      - stage:
          name: Build & Test
          steps:
            - step:
                name: Build
                script:
                  - npm ci
                  - npm run build
                artifacts:
                  - dist/**          # Available to subsequent steps
            - parallel:
                fail-fast: true
                steps:
                  - step:
                      name: Unit Tests
                      script: [npm test]
                  - step:
                      name: Integration Tests
                      script: [npm run test:integration]
                      services: [postgres]
      - step:
          name: Deploy to Production
          deployment: production     # Environment-scoped variables + Deployments dashboard
          trigger: manual           # Any write-access user can trigger
          script:
            - pipe: atlassian/azure-aks-helm-deploy:1.0.0
              variables:
                AZURE_APP_ID: $AZURE_APP_ID
                AZURE_PASSWORD: $AZURE_PASSWORD
                AZURE_TENANT_ID: $AZURE_TENANT_ID
                CLUSTER_NAME: aks-prod
                RESOURCE_GROUP: rg-prod
                RELEASE_NAME: myapp
                CHART: ./charts/myapp
                VALUES_FILE: helm/values-prod.yaml

  pull-requests:
    '**':
      - step:
          script:
            - npm test
            - npm run lint

  tags:
    'v*.*.*':
      - step:
          deployment: production
          script:
            - echo "Deploying tag $BITBUCKET_TAG"
```

### Triggers Block (November 2025+)

The new `triggers:` block enables event-driven chaining:

```yaml
pipelines:
  custom:
    deploy-after-scan:
      triggers:
        - type: pipeline-completed
          pipeline: security-scan
          condition:
            status: successful
      steps:
        - step:
            script:
              - echo "Security scan passed, deploying"
```

Supported event types: `repository-push`, `pullrequest-push`, `pipeline-completed`, `deployment-completed`, `pullrequest-created/updated/fulfilled/rejected/reviewer-status-updated`.

---

## Azure Pipes Reference

Microsoft and Atlassian maintain these pipes for Azure deployments:

| Pipe | Purpose |
|---|---|
| `microsoft/azure-cli-run:1.x` | Run arbitrary `az` commands |
| `microsoft/azure-arm-deploy:1.x` | Deploy ARM/Bicep templates |
| `microsoft/azure-functions-deploy:1.x` | Deploy Azure Functions |
| `atlassian/azure-web-apps-deploy:1.x` | Deploy zip-based App Service code |
| `atlassian/azure-web-apps-containers-deploy:1.x` | Deploy container images to App Service |
| `microsoft/azure-aks-deploy:1.x` | kubectl against AKS |
| `atlassian/azure-aks-helm-deploy:1.x` | Helm against AKS |
| `microsoft/azure-storage-deploy:1.x` | Sync to Azure Storage |
| `microsoft/azure-static-web-apps-deploy:1.x` | Deploy to Azure Static Web Apps |

All pipes expect `AZURE_APP_ID`, `AZURE_PASSWORD`, `AZURE_TENANT_ID` as variables. ACR pushes:

```yaml
script:
  - docker build -t myregistry.azurecr.io/myapp:$BITBUCKET_COMMIT .
  - docker login myregistry.azurecr.io -u $AZURE_APP_ID -p $AZURE_PASSWORD
  - docker push myregistry.azurecr.io/myapp:$BITBUCKET_COMMIT
```

---

## Deployment Environments and Variables

Bitbucket has three variable scopes:
1. **Workspace variables** — shared across all repos in the workspace
2. **Repository variables** — scoped to one repo
3. **Deployment variables** — scoped to a specific environment (`deployment: production`)

Use deployment variables for environment-specific credentials. Variables marked **Secured** are masked in logs and not accessible via the API after creation.

**Important:** The only built-in gate is `trigger: manual` — any user with write access can trigger. There is no native multi-approver workflow, no required reviewers, no environment protection rules equivalent to GitHub Environments or Azure DevOps Approvals & Checks.

On **Premium** plan, deployment permissions allow restricting which users can deploy to each environment. For multi-approver workflows, integrate Jira Service Management change management.

---

## YAML Anchors for In-Repo Reuse

YAML anchors are the mechanism for deduplication within a single `bitbucket-pipelines.yml`:

```yaml
definitions:
  steps:
    - step: &build-step
        name: Build
        script:
          - npm ci
          - npm run build
        caches: [node]
        artifacts: [dist/**]

    - step: &test-step
        name: Test
        script: [npm test]
        caches: [node]

pipelines:
  branches:
    main:
      - step: *build-step
      - step: *test-step
      - step:
          name: Deploy
          script: [./deploy.sh]

    develop:
      - step: *build-step
      - step: *test-step
```

For reuse across repos, use the shared pipeline config mechanism (Premium feature):
```yaml
# In consuming repo's bitbucket-pipelines.yml
import:
  repository: myorg/shared-pipelines
  ref: main
  path: security-scan-pipeline

pipelines:
  branches:
    main:
      - import: security-scan-pipeline
```

---

## Runners: Hosted vs Self-Hosted

### Hosted Runners (Atlassian-managed)

**Linux only** — x86_64 by default, ARM available via `runtime.cloud.arch: arm`. No hosted Windows, no hosted macOS.

Step sizes and memory:
| Size | Memory | vCPU | Minute multiplier |
|---|---|---|---|
| 1x (default) | 4 GB | 2 | 1x |
| 2x | 8 GB | 4 | 2x |
| 4x | 16 GB | 8 | 4x |
| 8x | 32 GB | 16 | 8x |
| 16x–32x | 64–128 GB | 32–64 | 16x–32x |

**Size multipliers consume minutes at the multiplier rate** — a 4x step costs 4 minutes per 1 minute of wall-clock time. This is the single most common source of cost surprise.

```yaml
- step:
    name: Heavy Build
    size: 4x    # Costs 4x minutes — check before committing to this size
    script:
      - mvn clean package
```

**Docker service memory** is capped at 1 GB independent of step `size:`. Modern images exceed this. Always set explicitly for image-heavy pipelines:

```yaml
definitions:
  services:
    docker:
      memory: 3072    # 3 GB — must set separately from step size
```

### Self-Hosted Runners

Required for Windows, macOS, or builds needing private network access (private AKS clusters, App Service with IP restrictions).

```yaml
- step:
    name: Windows Build
    runs-on:
      - self.hosted    # Routes to self-hosted runners
      - windows        # Label filtering
    script:
      - dotnet build
      - dotnet test
```

**Pricing (March 2026 model):** Up to 100 free self-hosted runners per workspace. Premium Runners add-on billed by maximum concurrent build slots used per month. V3/V4 runners deprecated mid-2026 — migrate to V5.

---

## Pricing (May 2026, Atlassian List)

| Plan | Price | Build minutes/mo | Concurrent steps | Key features |
|---|---|---|---|---|
| **Free** | $0 (≤5 users) | 50 | 10 | Unlimited repos, basic CI/CD |
| **Standard** | $3.65/user/mo (flat $18.25/mo for 1–5) | 2,500 | up to 600 | 4x/8x step sizes |
| **Premium** | $7.25/user/mo (flat $36.25/mo for 1–5) | 3,500 | up to 600 | IP allowlisting, merge checks, deployment permissions, required 2SV |

- Overage: $10 per 1,000 additional minutes
- Additional LFS storage: $10 per 100 GB
- Build minutes are **workspace-pooled** — a single noisy repo can starve all others. No per-repo quota.

**SSO is a separate Atlassian Guard subscription**: Guard Standard $4.20/user/mo, Guard Premium $8.18/user/mo. For 100-user enterprise on Premium + Guard Premium: effective $15.43/user/month, not $7.25.

**Cost intuition:** A 16-minute pipeline fanning out across 4 parallel containers can easily consume 70+ workspace minutes per run. 100 runs/day = ~210,000 minutes/month = ~$2,100/month in overage above the Standard plan's 2,500 bundled minutes.

---

## Comparison: Bitbucket vs GitHub Actions vs Azure DevOps

| Feature | Bitbucket Pipelines | GitHub Actions | Azure DevOps |
|---|---|---|---|
| Pipeline structure | Single YAML file | Multiple workflow files | YAML + classic editor |
| Hosted OS | Linux only | Linux, Windows, macOS | Linux, Windows, macOS |
| OIDC to Azure | **Not supported** | Native (azure/login) | Native (workload identity) |
| Multi-approver gates | trigger: manual only | Environments + required reviewers | Approvals & Checks |
| Marketplace | 50–100+ pipes | 20,000+ actions | Thousands of extensions |
| Free build minutes/mo | 50 | 2,000 | 1,800 |
| Native secret scanning | No (third-party pipes) | Yes (GitHub Advanced Security) | No (third-party tasks) |
| Jira integration | Native | Via GitHub Issues | Via Azure Boards |
| Matrix builds | Manual parallel expansion | Native strategy.matrix | Via PowerShell loops |
| Job DAG | No (sequential + parallel) | Yes (needs:) | Yes (dependsOn) |

---

## Known Limitations and Gotchas

1. **No OIDC to Azure** — the largest gap for Azure shops. No committed delivery from Atlassian.

2. **Hosted Linux only** — .NET Framework builds, Windows containers, iOS/macOS all require self-hosted runners.

3. **One YAML file per repo** — 30-workflow GitHub repos collapse into one potentially sprawling file.

4. **Docker service 1 GB memory cap** — independent of step `size:`. OOM in docker build does not respond to `size: 4x` alone — must also raise `definitions.services.docker.memory`.

5. **Docker cache limited to 1 GB** — modern images quickly exceed this. Use registry cache (`--cache-from`), self-hosted runners with disk, or Depot.

6. **Artifacts expire after 14 days** — manual gate steps become un-clickable if the gate is held longer than 2 weeks because input artifacts are gone.

7. **No matrix builds** — multi-runtime test matrices (Node 18×20×22 on Linux×Windows) that are one-liners in GHA require hand-expansion in Bitbucket.

8. **Parallel steps cannot reliably share artifacts** — only the first finishing step can write a given cache. Fan-out → fan-in patterns require careful design.

9. **IP allowlisting** — use `runtime.cloud.atlassian-ip-ranges: true` to constrain hosted runs to publishable IP ranges for Azure resources with IP restrictions.

10. **Pushing more than 5 tags/branches/bookmarks in one push skips pipeline runs entirely** — anti-runaway protection that can bite automation scripts.

11. **IPv4 only** — if your Azure landing zone requires IPv6, this is a blocker.

12. **Self-hosted runner pricing in flux** — the model changed significantly in early 2026; verify before any architectural commitment.

---

## Security Scanning Integration

Bitbucket has no first-party security scanning comparable to Dependabot or CodeQL. Wire in third-party tools via pipes:

```yaml
pipelines:
  pull-requests:
    '**':
      - parallel:
          steps:
            - step:
                name: Snyk Dependency Scan
                script:
                  - pipe: snyk/snyk-scan:1.0.0
                    variables:
                      SNYK_TOKEN: $SNYK_TOKEN
                      SEVERITY_THRESHOLD: high
                      FAIL_ON_ISSUES: 'true'

            - step:
                name: Secrets Scan
                script:
                  - pip install gitleaks
                  - gitleaks detect --source . --verbose

            - step:
                name: SonarCloud Analysis
                script:
                  - pipe: sonarsource/sonarcloud-scan:2.0.0
                    variables:
                      SONAR_TOKEN: $SONAR_TOKEN
```

For a comprehensive DevSecOps posture on Bitbucket, the pipeline cannot match GitHub Actions' first-party toolchain (Dependabot + CodeQL + secret scanning built into the platform). Budget for Snyk or Mend licenses as equivalents.

---

## Recommendations by Team Profile

**Azure shop committed to Atlassian ecosystem:**
Use Bitbucket Pipelines for CI, store Azure credentials as deployment-scoped secured variables, automate rotation, enforce Premium deployment permissions to restrict who can deploy to production.

**Security review demands zero long-lived secrets:**
Build the Azure Function token broker (Option B above). 1 engineering-week to build, negligible runtime cost. Treats the function as security-critical with rate limiting and Sentinel logging.

**Large enterprise with .NET + Azure portfolio:**
Hybrid: Bitbucket as code host, Azure Pipelines YAML pipelines for deployment legs (workload-identity service connections, native Windows/macOS hosted agents). One Azure DevOps Basic license per active user cleanly resolves the OIDC gap and hosted runner limitations.

**Migration trigger thresholds:**
- If monthly Bitbucket overage minutes bill exceeds ~$1,500, model GitHub Actions or Azure Pipelines economics
- If maintaining more than 10 self-hosted runners, evaluate the Premium Runners tier or GitHub's larger hosted runners
- If BCLOUD-22206 ships native Azure OIDC, retire the token broker immediately

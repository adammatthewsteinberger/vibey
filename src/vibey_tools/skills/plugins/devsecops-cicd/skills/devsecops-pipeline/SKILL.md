---
name: devsecops-pipeline
description: Use whenever building or reviewing CI/CD security pipelines, DevSecOps GitHub Actions workflows, SAST/DAST/SCA scanning, secrets scanning, container scanning, IaC scanning, or security gates in deployment pipelines. Essential for any security-in-pipeline work.
---

# DevSecOps Pipeline: Security-in-CI/CD Reference

## The Full 6-Job GitHub Actions Pipeline

The complete DevSecOps pipeline integrates SAST, SCA, secrets scanning, container scanning, IaC scanning, and a deploy job that only runs if all security gates pass.

```yaml
# .github/workflows/devsecops.yml
name: DevSecOps Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  security-events: write
  contents: read
  id-token: write    # Required for OIDC Azure auth in deploy job

jobs:
  # ── JOB 1: SAST — Static Application Security Testing ──────────────────────
  sast-semgrep:
    name: SAST (Semgrep)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: 'p/security-audit p/owasp-top-ten p/csharp p/typescript p/secrets'
          generateSarif: true
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep.sarif
        if: always()

  sast-codeql:
    name: SAST (CodeQL)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: 'csharp, javascript'   # CodeQL excels at C# and TypeScript
          queries: security-extended
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
        with:
          output: codeql-results.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: codeql-results.sarif
        if: always()

  # ── JOB 2: SCA — Software Composition Analysis (dependencies) ─────────────
  sca-snyk:
    name: SCA (Snyk)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Snyk for .NET
        uses: snyk/actions/dotnet@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: '--severity-threshold=high --all-projects'
      - name: Run Snyk for Node
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: '--severity-threshold=high'

  # ── JOB 3: Secrets Scanning ─────────────────────────────────────────────────
  secrets-scan:
    name: Secrets Scan (Gitleaks)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0    # Full history — scan all commits, not just latest
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}   # Required for org scans

  # ── JOB 4: Container Scanning ───────────────────────────────────────────────
  container-scan:
    name: Container Scan (Trivy)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .
      - name: Scan filesystem (catches IaC and deps in repo)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
          format: sarif
          output: trivy-fs.sarif
      - name: Scan container image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:${{ github.sha }}'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
          format: sarif
          output: trivy-image.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-image.sarif
        if: always()

  # ── JOB 5: IaC Scanning ─────────────────────────────────────────────────────
  iac-scan:
    name: IaC Scan (Checkov)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Checkov for Terraform
        uses: bridgecrewio/checkov-action@master
        with:
          directory: infra/
          framework: terraform
          soft_fail: false
          output_format: sarif
          output_file_path: checkov-tf.sarif
      - name: Checkov for Bicep
        uses: bridgecrewio/checkov-action@master
        with:
          directory: infra/
          framework: bicep
          soft_fail: false
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: checkov-tf.sarif
        if: always()

  # ── JOB 6: Deploy — Only if ALL security gates pass ─────────────────────────
  deploy:
    name: Deploy to Production
    needs: [sast-semgrep, sast-codeql, sca-snyk, secrets-scan, container-scan, iac-scan]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: production    # Requires environment protection rules
    steps:
      - uses: actions/checkout@v4
      - name: Azure Login (OIDC — no stored secrets)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - name: Deploy
        run: |
          echo "All ${{ needs.sast-semgrep.result }}, ${{ needs.sca-snyk.result }} security gates passed — deploying"
          # az deployment group create ...
```

---

## Job-by-Job Breakdown

### Job 1: SAST — Static Application Security Testing

Two tools for different strengths:

**Semgrep** — best for custom rules and rapid rule authorship. Rulesets to enable:
- `p/security-audit` — broad security patterns
- `p/owasp-top-ten` — OWASP Top 10 checks
- `p/csharp` — C#-specific patterns
- `p/typescript` — TypeScript/React patterns
- `p/secrets` — hardcoded credential detection

**CodeQL** — best for C# and TypeScript deep semantic analysis. Finds:
- SQL injection (including EF Core string interpolation)
- Cross-site scripting
- Path traversal
- Insecure deserialization
- Missing authorization

Use `languages: csharp, javascript` and `queries: security-extended` for the most thorough analysis. `autobuild` handles .NET solution files automatically.

Both tools upload SARIF results to GitHub's Security tab. Results persist and can be reviewed even if the job fails — always use `if: always()` on SARIF upload steps.

### Job 2: SCA — Software Composition Analysis

Snyk scans dependency trees for known vulnerabilities (CVEs) in NuGet and npm packages.

`--severity-threshold=high` fails the job on HIGH or CRITICAL findings. Use `--all-projects` for monorepo solutions with multiple `.csproj` files.

**Complement with Dependabot** for automated PR-based updates:
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
  - package-ecosystem: "nuget"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

Also enable NuGet audit in `.csproj` to catch vulnerabilities at build time locally:
```xml
<PropertyGroup>
    <NuGetAudit>true</NuGetAudit>
    <NuGetAuditMode>all</NuGetAuditMode>
    <NuGetAuditLevel>low</NuGetAuditLevel>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
</PropertyGroup>
```

### Job 3: Secrets Scanning with Gitleaks

`fetch-depth: 0` is critical — scans the entire git history, not just the latest commit. A secret committed 6 months ago and "deleted" in a subsequent commit is still in history.

**Pre-commit hook to catch secrets before they reach CI:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

Install pre-commit: `pip install pre-commit && pre-commit install`

**Custom Gitleaks rules** for organization-specific patterns:
```toml
# .gitleaks.toml
[[rules]]
  id = "azure-connection-string"
  description = "Azure Storage Connection String"
  regex = '''DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{88}'''
  tags = ["azure", "storage"]
```

### Job 4: Container Scanning with Trivy

Two scan modes:

**Filesystem scan** (`scan-type: fs`) — scans the repository for vulnerable packages declared in `package-lock.json`, `packages.lock.json`, etc. Runs without building the image, so it catches issues early.

**Image scan** — scans the built container image including OS packages. This catches vulnerabilities in the base image that aren't visible in dependency files.

**Container security best practices enforced by Trivy scanning:**

```dockerfile
# Use distroless (no shell, no package manager — minimal attack surface)
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base

# Run as non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

# Read-only filesystem (use volume mounts for writable paths)
# Enforced at pod level: readOnlyRootFilesystem: true

# No SUID/SGID binaries
RUN find / -perm /6000 -type f -exec chmod a-s {} \; 2>/dev/null || true
```

**Trivy Operator** for continuous in-cluster scanning (deploy separately):
```bash
helm install trivy-operator aquasecurity/trivy-operator \
  --namespace trivy-system \
  --create-namespace \
  --set="trivy.ignoreUnfixed=true"
```

### Job 5: IaC Scanning with Checkov

Checkov covers 1000+ built-in policies for CIS benchmarks, HIPAA, PCI-DSS, and SOC2 across:
- Terraform (Azure provider)
- Bicep / ARM templates
- Kubernetes YAML manifests
- Dockerfile
- GitHub Actions workflows

`soft_fail: false` makes the job fail on policy violations. Use `check` / `skip-check` for exceptions:

```yaml
- uses: bridgecrewio/checkov-action@master
  with:
    directory: infra/
    framework: terraform
    soft_fail: false
    skip-check: >
      CKV_AZURE_88,
      CKV2_AZURE_21
```

Document every skipped check with justification in a comment or separate file. Unapproved exceptions require a security review.

---

## Semgrep PostToolUse Hook for Real-Time Scanning

Wire Semgrep to scan files immediately after Claude Code edits them:

```json
// .claude/settings.json
{
  "hooks": {
    "PostToolUse": {
      "Edit": "semgrep scan --config p/secrets --config p/owasp-top-ten --quiet ${CLAUDE_FILE_PATH}",
      "Write": "semgrep scan --config p/secrets --config p/owasp-top-ten --quiet ${CLAUDE_FILE_PATH}"
    }
  }
}
```

This catches AI-generated security anti-patterns immediately during development, before they reach CI:
- Hardcoded credentials (CWE-798)
- SQL injection via string interpolation (CWE-89)
- Missing authorization decorators (CWE-862)
- XSS in React via `dangerouslySetInnerHTML` (CWE-79)

---

## Quality Gates and Exception Process

**Gate thresholds:**
- SAST: fail on HIGH or CRITICAL severity findings
- SCA: fail on HIGH or CRITICAL CVEs
- Secrets: fail on any detected secret
- Container: fail on CRITICAL or HIGH CVEs in base image or installed packages
- IaC: fail on HIGH severity policy violations (MEDIUM as warning only)

**Exceptions process:**
1. Security engineer reviews the finding
2. Documents justification in code comment or exceptions file
3. Uses tool-specific suppression annotation:

```csharp
// Semgrep suppression
var query = $"SELECT * FROM Users WHERE Id = {userId}";  // nosemgrep: sql-injection
// EXCEPTION: userId is validated as integer before this point — confirmed 2026-01-15

// Trivy suppression (in Trivy config file)
// trivy:ignore:CVE-2024-12345
```

```yaml
# Checkov suppression inline
resource "azurerm_storage_account" "main" {
  # checkov:skip=CKV_AZURE_33: Public access needed for CDN static assets — reviewed 2026-01-15
  allow_nested_items_to_be_public = true
}
```

---

## DAST: OWASP ZAP for Deployed Environments

Run DAST against a deployed staging environment (not in the main PR pipeline — deploy first):

```yaml
dast-zap:
  name: DAST (OWASP ZAP)
  needs: [deploy-staging]
  runs-on: ubuntu-latest
  steps:
    - name: ZAP Baseline Scan
      uses: zaproxy/action-baseline@v0.10.0
      with:
        target: 'https://staging.myapp.example.com'
        rules_file_name: '.zap/rules.tsv'
        cmd_options: '-a'    # Include alpha passive scan rules

    - name: ZAP Full Scan (weekly only)
      if: github.event_name == 'schedule'
      uses: zaproxy/action-full-scan@v0.10.0
      with:
        target: 'https://staging.myapp.example.com'
        rules_file_name: '.zap/rules.tsv'
```

ZAP rules file to suppress known false positives:
```tsv
# .zap/rules.tsv
10035	IGNORE	(Strict-Transport-Security Header Not Set)
10038	IGNORE	(Content Security Policy Header Not Set)
```

---

## Secrets Management — No Hardcoded Credentials

**In GitHub Actions workflows:**
- Use `${{ secrets.* }}` for sensitive values
- Use OIDC federation for Azure, AWS, GCP (no stored cloud credentials)
- Use `${{ vars.* }}` for non-sensitive configuration

**Repository secrets vs environment secrets:**
- Repository secrets are available to all workflows — use for non-environment-specific values
- Environment secrets (under `environment: production`) are only injected when the job runs against that environment — use for production credentials

```yaml
# OIDC pattern — only tenant/subscription IDs stored as secrets, no passwords
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}      # App registration client ID
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}      # Tenant ID
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
    # No AZURE_CLIENT_SECRET — uses OIDC token exchange
```

---

## Branch Protection Rules

Configure these on the main branch to enforce security gates before merge:

```yaml
# Via GitHub repository settings or Terraform:
resource "github_branch_protection" "main" {
  repository_id = github_repository.main.node_id
  pattern       = "main"

  required_status_checks {
    strict   = true    # Require branch to be up to date
    contexts = [
      "SAST (Semgrep)",
      "SAST (CodeQL)",
      "SCA (Snyk)",
      "Secrets Scan (Gitleaks)",
      "Container Scan (Trivy)",
      "IaC Scan (Checkov)",
    ]
  }

  required_pull_request_reviews {
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = true
    required_approving_review_count = 1
  }

  enforce_admins = true    # Admins cannot bypass checks
}
```

---

## Reusable Security Workflow Pattern

Extract scanning jobs into reusable workflows for consistent security across all repositories:

```yaml
# .github/workflows/security-scan.yml (in a central org repo)
on:
  workflow_call:
    inputs:
      image-ref:
        required: true
        type: string
      infra-directory:
        required: false
        type: string
        default: 'infra/'
    secrets:
      SNYK_TOKEN:
        required: true

jobs:
  sast:
    uses: ./.github/workflows/sast.yml
  sca:
    uses: ./.github/workflows/sca.yml
    secrets: inherit
  container-scan:
    uses: ./.github/workflows/container-scan.yml
    with:
      image-ref: ${{ inputs.image-ref }}
```

Call from any repository:
```yaml
security:
  uses: myorg/shared-workflows/.github/workflows/security-scan.yml@main
  with:
    image-ref: myapp:${{ github.sha }}
    infra-directory: infrastructure/
  secrets: inherit
```

---

## Security Policy as Code with OPA/Rego

Enforce security policies across the stack using OPA with Conftest:

```rego
# policy/kubernetes.rego
package kubernetes.security

deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.securityContext.readOnlyRootFilesystem
  msg := sprintf("Container '%s' must have readOnlyRootFilesystem: true", [container.name])
}

deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources.limits.memory
  msg := sprintf("Container '%s' must have memory limits set", [container.name])
}

deny[msg] {
  input.kind == "Deployment"
  input.spec.template.spec.containers[_].image
  endswith(input.spec.template.spec.containers[_].image, ":latest")
  msg := "Images must not use :latest tag — pin by digest or semver"
}
```

Run in CI:
```yaml
- name: Policy check with Conftest
  run: |
    helm template ./charts/myapp | conftest test - \
      --policy policy/ \
      --namespace kubernetes.security
```

---

## Dependency Management: Dependabot + Snyk + Renovate

**Renovate bot** (more configurable than Dependabot) for automated dependency updates:
```json
// renovate.json
{
  "extends": ["config:base", ":dependencyDashboard"],
  "packageRules": [
    {
      "matchUpdateTypes": ["patch"],
      "automerge": true    // Auto-merge patch updates
    },
    {
      "matchPackagePatterns": ["^Azure\\.", "^Microsoft\\."],
      "groupName": "Azure SDK packages"
    }
  ],
  "prConcurrentLimit": 5
}
```

---

## Pipeline Security Anti-Patterns to Avoid

1. **`soft_fail: true` on security scans** — defeats the purpose of gates. Only acceptable during initial rollout.

2. **Scanning only the PR diff** — use `fetch-depth: 0` for secrets scanning; scan the full image for container vulnerabilities, not just changed files.

3. **Skipping SARIF upload on failure** — always `if: always()` on SARIF uploads so findings appear in GitHub Security tab even when the job fails.

4. **Single SARIF for multiple scans** — upload separate SARIF files from each tool so findings are attributed correctly.

5. **Environment secrets as repository secrets** — production credentials should be environment-scoped, not available to all workflows.

6. **No exception process** — blanket `soft_fail: true` or skipping all checks is worse than no scanning. Build a documented, time-bound exception process with a required security review.

7. **Building untrusted pull requests with access to secrets** — use `pull_request_target` only when necessary and keep secrets out of untrusted PR contexts.

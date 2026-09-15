---
name: cybersecurity-implementation
description: "Concrete copy-paste security patterns for Azure/.NET 8/React/Blazor/Cosmos/PostgreSQL/Databricks. Use for Entra ID auth, MSAL.js, Microsoft.Identity.Web, .NET 8 middleware pipeline, rate limiting, BOLA prevention, DOMPurify/CSP, PostgreSQL RLS, Cosmos hierarchical partition keys, Databricks Unity Catalog, Claude Code managed-settings.json, PostToolUse Semgrep hook, Key Vault Bicep, Private Endpoints, AKS Workload Identity, or KQL security queries. Six security domains, three-tier maturity model. Use with security-first-scrum."
---

# Enterprise Cybersecurity Implementation Guide

Production-ready, copy-paste security implementation for: Microsoft Azure, .NET 8 Web API,
React, Blazor WASM, CosmosDB, PostgreSQL, Databricks, Claude Code, Cursor IDE.

Three-tier maturity model for each domain:
- **Foundational** — get secure fast; correct flow selection and baseline controls
- **Intermediate** — hardened for production; RBAC, rate limiting, resource authorization
- **Advanced** — defense-in-depth; zero-secrets, network isolation, threat detection

---

## DOMAIN 1: IDENTITY AND AUTHENTICATION (ENTRA ID, JWT, OIDC)

### Foundational — App Registrations and Correct Auth Flows

Create **separate Entra ID app registrations** for the API and each frontend (React SPA, Blazor
WASM). Use "Accounts in this organizational directory only" for single-tenant internal apps.

```bash
# Create API app registration
az ad app create --display-name "myapp-api" --sign-in-audience "AzureADMyOrg" \
  --identifier-uris "api://myapp-api"
# Create SPA app registration
az ad app create --display-name "myapp-spa" --sign-in-audience "AzureADMyOrg"
# Create service principal (Enterprise Application)
az ad sp create --id <APP_ID>
```

**Authentication flow selection is non-negotiable.** Wrong flows break security.

| Scenario | Required Flow | Never Use |
|---|---|---|
| React SPA user login | Authorization Code + PKCE | Implicit Grant (deprecated, disabled) |
| Blazor WASM user login | Authorization Code + PKCE | Implicit Grant |
| Service-to-service / daemons | Client Credentials | Shared secrets in config |
| API calling downstream API for user | On-Behalf-Of (OBO) | Storing user tokens in service |
| CLI tooling | Device Code | Embedded credentials |

**.NET 8 Web API — Microsoft.Identity.Web** (NuGet: `Microsoft.Identity.Web` v3.x/v4.x):

```csharp
// Program.cs
using Microsoft.Identity.Web;
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"));
builder.Services.AddAuthorization();
```

```json
// appsettings.json — non-secret values only; ClientSecret must NEVER appear here
{
  "AzureAd": {
    "Instance": "https://login.microsoftonline.com/",
    "TenantId": "your-tenant-id",
    "ClientId": "your-api-client-id",
    "Audience": "api://your-api-client-id"
  }
}
```

**React with MSAL.js** (npm: `@azure/msal-browser` v3.x, `@azure/msal-react` v2.x):

```typescript
// authConfig.ts
export const msalConfig: Configuration = {
  auth: {
    clientId: "your-spa-client-id",
    authority: "https://login.microsoftonline.com/your-tenant-id",
    redirectUri: "/",
  },
  cache: {
    cacheLocation: "sessionStorage", // NEVER localStorage — XSS-vulnerable
    storeAuthStateInCookie: false,
  },
};
export const apiScopes = { scopes: ["api://your-api-client-id/Api.Read"] };
```

```tsx
// index.tsx — Instantiate OUTSIDE component tree (never inside a component)
const msalInstance = new PublicClientApplication(msalConfig);
await msalInstance.initialize();
await msalInstance.handleRedirectPromise();
const accounts = msalInstance.getAllAccounts();
if (accounts.length > 0) msalInstance.setActiveAccount(accounts[0]);
root.render(<MsalProvider instance={msalInstance}><App /></MsalProvider>);
```

**Blazor WASM** (NuGet: `Microsoft.Authentication.WebAssembly.Msal` v8.x):

```csharp
// Program.cs
builder.Services.AddMsalAuthentication(options =>
{
    builder.Configuration.Bind("AzureAd", options.ProviderOptions.Authentication);
    options.ProviderOptions.DefaultAccessTokenScopes.Add(
        "api://your-api-client-id/Api.Read");
    options.ProviderOptions.LoginMode = "redirect";
});
```

**Critical anti-patterns to avoid:**
- Storing tokens in `localStorage` (XSS-vulnerable)
- Enabling implicit grant checkboxes in app registration
- Sharing a single app registration across environments
- Hardcoding client secrets in source code
- Creating `PublicClientApplication` inside React components (re-created on every render)

### Intermediate — JWT Validation, App Roles, Token Lifecycle

JWT validation in .NET must enforce issuer, audience, lifetime, and signing key — all handled
automatically by `AddMicrosoftIdentityWebApi`. If configuring manually: `ClockSkew = TimeSpan.Zero`
(the 5-minute default is too generous). Never hardcode signing keys — Microsoft rotates them via
the JWKS endpoint.

**App Roles in manifest:**
```json
{
  "appRoles": [
    {
      "allowedMemberTypes": ["User"],
      "displayName": "Admin",
      "id": "unique-guid-here",
      "isEnabled": true,
      "value": "Admin"
    }
  ]
}
```

**Map App Roles to authorization policies:**
```csharp
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("AdminOnly", policy => policy.RequireRole("Admin"))
    .AddPolicy("ReaderOrAdmin", policy => policy.RequireRole("Reader", "Admin"))
    .AddPolicy("DepartmentFinance", policy =>
        policy.RequireClaim("department", "finance"));
```

**Use App Roles over Group Claims.** Groups create an overage problem: users with more than 200
groups cause Entra ID to emit a `_claim_sources` reference instead of the groups array, requiring
a Graph API call. App Roles are portable and don't have this limitation.

**Token storage in SPAs:** MSAL.js keeps tokens in-memory by default. `sessionStorage` is the
most secure persistent option (per-tab isolation, auto-clears on tab close). **Refresh token
rotation is automatic** — SPAs receive one-time-use refresh tokens that rotate on each use.
Replaying a used token revokes the entire token family.

### Advanced — Managed Identities, Conditional Access, Zero-Secrets

**Managed Identities eliminate all secrets from your .NET API configuration.** Core NuGet:
`Azure.Identity` (v1.13.x).

```csharp
// Production-optimized credential selection
var credential = builder.Environment.IsDevelopment()
    ? new DefaultAzureCredential()
    : new ManagedIdentityCredential();  // Faster startup — skips environment probing

// CosmosDB with Managed Identity
var cosmosClient = new CosmosClient("https://your-account.documents.azure.com:443/", credential);

// PostgreSQL with periodic token refresh (tokens expire in 4-24 hours)
var dataSourceBuilder = new NpgsqlDataSourceBuilder(connStringWithoutPassword);
dataSourceBuilder.UsePeriodicPasswordProvider(async (_, ct) =>
{
    var token = await credential.GetTokenAsync(new TokenRequestContext(
        new[] { "https://ossrdbms-aad.database.windows.net/.default" }), ct);
    return token.Token;
}, TimeSpan.FromHours(4), TimeSpan.FromSeconds(10));
```

```bash
# Assign Cosmos DB Built-in Data Contributor role
az cosmosdb sql role assignment create \
  --account-name myCosmosAccount --resource-group myRG \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id "<managed-identity-object-id>" --scope "/"
```

**Conditional Access policies to deploy:**
1. Require MFA for all users (exclude break-glass accounts)
2. Block legacy authentication protocols (SMTP, IMAP, POP3 bypass Conditional Access)
3. Require compliant devices via Intune
4. Require MFA from non-trusted network locations

Always test with Report-only mode and the What If tool before enforcement.

---

## DOMAIN 2: API SECURITY (.NET 8 WEB API)

### Foundational — Middleware Pipeline ORDER (Critical), Validation, CORS

**Middleware ordering is the single most common security misconfiguration in .NET APIs.**
`UseAuthentication` must precede `UseAuthorization` — reversing them causes authentication to
silently fail and authorization to pass for all requests.

```csharp
var app = builder.Build();

if (app.Environment.IsDevelopment()) { app.UseSwagger(); app.UseSwaggerUI(); }
else { app.UseHsts(); }

// Security headers — first substantial middleware
app.Use(async (context, next) => {
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["X-Frame-Options"] = "DENY";
    context.Response.Headers["Referrer-Policy"] = "strict-origin-when-cross-origin";
    context.Response.Headers["Permissions-Policy"] =
        "accelerometer=(), camera=(), geolocation=(), microphone=()";
    await next();
});

app.UseHttpsRedirection();
app.UseSerilogRequestLogging();
app.UseRouting();
app.UseRateLimiter();        // Rate limit BEFORE auth to block brute force
app.UseCors("SpaPolicy");
app.UseAuthentication();    // WHO are you?
app.UseAuthorization();     // WHAT can you do?
app.MapControllers();
```

Remove Kestrel Server header: `builder.WebHost.ConfigureKestrel(o => o.AddServerHeader = false);`

**Input validation** with FluentValidation (NuGet: `FluentValidation` v11.x +
`FluentValidation.DependencyInjectionExtensions`). Note: `FluentValidation.AspNetCore` is
deprecated — use the base package:

```csharp
public class CreateUserRequestValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserRequestValidator()
    {
        RuleFor(x => x.Name).NotEmpty().MaximumLength(100)
            .Matches(@"^[a-zA-Z\s\-']+$").WithMessage("Name contains invalid characters.");
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.Age).InclusiveBetween(18, 120);
    }
}
// Program.cs
builder.Services.AddValidatorsFromAssemblyContaining<CreateUserRequestValidator>();
```

**CORS — exact allowed origins only:**
```csharp
var allowedOrigins = builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>()!;
builder.Services.AddCors(options =>
{
    options.AddPolicy("SpaPolicy", policy => policy
        .WithOrigins(allowedOrigins)  // NEVER AllowAnyOrigin() in production
        .AllowAnyHeader().AllowAnyMethod().AllowCredentials());
});
```

Trailing slash in origin URLs (`"https://app.example.com/"`) causes silent comparison failure.
Omit trailing slashes.

### Intermediate — Rate Limiting, BOLA via IAuthorizationHandler, Logging

**Built-in rate limiting in .NET 8** (no extra NuGet needed):

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.AddTokenBucketLimiter("Api", opt =>
    {
        opt.TokenLimit = 100;
        opt.ReplenishmentPeriod = TimeSpan.FromSeconds(10);
        opt.TokensPerPeriod = 20;
        opt.QueueLimit = 5;
    });
    // Per-user rate limiting (falls back to IP for unauthenticated)
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(
        httpContext => RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: httpContext.User.Identity?.Name
                ?? httpContext.Connection.RemoteIpAddress?.ToString() ?? "anon",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 60, Window = TimeSpan.FromMinutes(1)
            }));
});
```

Apply with `[EnableRateLimiting("Api")]` on controllers or `.RequireRateLimiting("Api")` on
minimal API routes.

**BOLA prevention via IAuthorizationHandler** (OWASP API1 — Broken Object Level Authorization):

```csharp
public class DocumentAuthorizationHandler
    : AuthorizationHandler<SameAuthorRequirement, Document>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        SameAuthorRequirement requirement, Document resource)
    {
        if (context.User.Identity?.Name == resource.AuthorId)
            context.Succeed(requirement);
        // Never call context.Succeed for unauthorized access — implicit failure is correct
        return Task.CompletedTask;
    }
}
```

**Serilog with Application Insights:**
```csharp
builder.Host.UseSerilog((context, services, config) => config
    .ReadFrom.Configuration(context.Configuration)
    .Enrich.FromLogContext()
    .WriteTo.Console()
    .WriteTo.ApplicationInsights(
        services.GetRequiredService<TelemetryConfiguration>(),
        TelemetryConverter.Traces));
```

Never log passwords, JWTs, API keys, connection strings, credit card numbers, or PII. Always log
failed auth, authorization denials, and suspicious input with structured fields.

### Advanced — Key Vault Config, Swagger Lockdown, Minimal API Security

**Zero-secrets configuration with Azure Key Vault:**
```csharp
var kvUri = new Uri($"https://{builder.Configuration["KeyVaultName"]}.vault.azure.net/");
builder.Configuration.AddAzureKeyVault(kvUri, new DefaultAzureCredential(),
    new AzureKeyVaultConfigurationOptions { ReloadInterval = TimeSpan.FromMinutes(5) });
```

Secrets auto-refresh without restarts when using `IOptionsMonitor<T>`.

**Swagger must never be exposed in production:**
```csharp
if (app.Environment.IsDevelopment()) { app.UseSwagger(); app.UseSwaggerUI(); }
// For Swagger JWT auth in development — use Http type, not ApiKey
options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
{
    Type = SecuritySchemeType.Http,
    Scheme = "Bearer",
    BearerFormat = "JWT"
});
```

**Minimal APIs — route group authorization:**
```csharp
var admin = app.MapGroup("/api/admin").RequireAuthorization("AdminOnly");
admin.MapGet("/users", () => Results.Ok());
admin.MapDelete("/users/{id}", (int id) => Results.NoContent());
// Explicit anonymous — document why
app.MapGet("/api/health", () => Results.Ok("healthy")).AllowAnonymous();
```

---

## DOMAIN 3: FRONTEND SECURITY (REACT AND BLAZOR WASM)

### Foundational — Token Management and XSS Prevention

**Never store tokens in `localStorage`** — any XSS vulnerability enables trivial theft via
`localStorage.getItem('token')`. Use `sessionStorage` (per-tab isolation, auto-clears on close).

**Axios interceptor for automatic token attachment and silent refresh:**
```typescript
// apiClient.ts
import axios from 'axios';
import { msalInstance } from './authConfig';
import { InteractionRequiredAuthError } from '@azure/msal-browser';

const apiClient = axios.create({ baseURL: 'https://api.example.com' });

apiClient.interceptors.request.use(async (config) => {
  const account = msalInstance.getActiveAccount();
  if (!account) throw new Error('No active account');
  try {
    const response = await msalInstance.acquireTokenSilent({
      scopes: ['api://your-api-client-id/.default'], account,
    });
    config.headers.Authorization = `Bearer ${response.accessToken}`;
  } catch (error) {
    if (error instanceof InteractionRequiredAuthError) {
      await msalInstance.acquireTokenRedirect({
        scopes: ['api://your-api-client-id/.default'],
      });
    }
  }
  return config;
});
```

**Four vectors that bypass React's auto-escaping protection:**
1. `dangerouslySetInnerHTML` without sanitization
2. `href` with `javascript:` protocol
3. Direct DOM manipulation via `ref.current.innerHTML`
4. `eval()` with user input

**DOMPurify SafeHTML wrapper** (npm: `dompurify`, `@types/dompurify`):
```tsx
import DOMPurify from 'dompurify';
export function SafeHTML({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'a'],
    FORBID_TAGS: ['script', 'style', 'iframe'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick'],
  });
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}
```

### Intermediate — Blazor WASM Constraints and Protected Routes

**Blazor WASM fundamental security constraint:** Everything runs client-side. All .NET assemblies
are downloadable and decompilable with ILSpy. All `[Authorize]` attributes and `AuthorizeView`
components are cosmetic — **the server API must re-validate every request**. Never put secrets,
sensitive business logic, or intellectual property in Blazor WASM code.

**Blazor WASM auth routing:**
```razor
<!-- App.razor -->
<CascadingAuthenticationState>
    <Router AppAssembly="@typeof(Program).Assembly">
        <Found Context="routeData">
            <AuthorizeRouteView RouteData="@routeData" DefaultLayout="@typeof(MainLayout)">
                <NotAuthorized>
                    @if (context.User.Identity?.IsAuthenticated != true)
                    { <RedirectToLogin /> }
                    else
                    { <p>You are not authorized.</p> }
                </NotAuthorized>
            </AuthorizeRouteView>
        </Found>
    </Router>
</CascadingAuthenticationState>
```

**React protected route with role checking:**
```tsx
function ProtectedRoute({ allowedRoles }: { allowedRoles?: string[] }) {
  const isAuthenticated = useIsAuthenticated();
  const { accounts } = useMsal();
  const location = useLocation();

  if (!isAuthenticated)
    return <Navigate to="/login" state={{ from: location }} replace />;
  if (allowedRoles?.length) {
    const userRoles = (accounts[0]?.idTokenClaims as any)?.roles ?? [];
    if (!allowedRoles.some(role => userRoles.includes(role)))
      return <Navigate to="/unauthorized" replace />;
  }
  return <Outlet />;
}
```

Both React and Blazor role-based UI rendering are UX features only. The API `[Authorize]` is the
real security boundary.

### Advanced — CSP Headers, Dependency Security, SRI

**Content Security Policy for React/Vite:**
```typescript
// vite.config.ts
export default defineConfig({
  build: { assetsInlineLimit: 0 }, // Prevent inline scripts that bypass CSP
  server: {
    headers: {
      'Content-Security-Policy': [
        "default-src 'self'",
        "script-src 'self'",
        "connect-src 'self' https://login.microsoftonline.com https://api.example.com",
        "img-src 'self' data: https:",
        "frame-ancestors 'none'",
      ].join('; '),
    },
  },
});
```

**Production CSP (served by .NET backend):**
```
default-src 'self';
script-src 'self' 'nonce-{SERVER_GENERATED}' 'strict-dynamic';
style-src 'self' 'nonce-{SERVER_GENERATED}';
connect-src 'self' https://login.microsoftonline.com https://graph.microsoft.com;
frame-ancestors 'none';
upgrade-insecure-requests;
```

**Dependency security automation:**
```xml
<!-- .csproj — NuGet audit on every build -->
<PropertyGroup>
    <NuGetAudit>true</NuGetAudit>
    <NuGetAuditMode>all</NuGetAuditMode>
    <NuGetAuditLevel>low</NuGetAuditLevel>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
</PropertyGroup>
```

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule: { interval: "weekly" }
  - package-ecosystem: "nuget"
    directory: "/backend"
    schedule: { interval: "weekly" }
  - package-ecosystem: "pip"
    directory: "/databricks"
    schedule: { interval: "weekly" }
```

---

## DOMAIN 4: DATA LAYER SECURITY (COSMOSDB, POSTGRESQL, DATABRICKS)

### Foundational — Managed Identity Access, Encryption Defaults

All three platforms encrypt data at rest with AES-256 by default and enforce TLS 1.2+ in
transit. The foundational security step is eliminating connection strings with keys.

**CosmosDB — assign Built-in Data Contributor role:**
```bash
az cosmosdb sql role assignment create \
  --account-name myCosmosAccount --resource-group myRG \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id "<managed-identity-principal-id>" --scope "/"
```

```csharp
var cosmosClient = new CosmosClient(
    "https://your-account.documents.azure.com:443/",
    new DefaultAzureCredential(),
    new CosmosClientOptions { ConnectionMode = ConnectionMode.Direct });
```

**Critical pitfall:** Azure control-plane roles like "Cosmos DB Account Contributor" do NOT
grant data-plane access. You must assign Cosmos DB's native data-plane RBAC roles separately.
Always include `readMetadata` permission or queries fail with 403.

**PostgreSQL — enable Entra ID auth, create Managed Identity principal:**
```sql
-- Run as Entra admin
SELECT * FROM pgaadauth_create_principal('<identity-name>', false, false);
GRANT ALL ON ALL TABLES IN SCHEMA public TO "<identity-name>";
```

**Databricks — Unity Catalog storage credentials with Managed Identity:**
```sql
CREATE STORAGE CREDENTIAL my_credential
WITH (AZURE_MANAGED_IDENTITY = '<managed-identity-resource-id>');
CREATE EXTERNAL LOCATION my_location
URL 'abfss://<container>@<storage-account>.dfs.core.windows.net/<path>'
WITH (STORAGE CREDENTIAL my_credential);
```

Databricks notebook secrets: `dbutils.secrets.get(scope="my-kv-scope", key="db-password")`.
Secret values are redacted in notebook output. Never hardcode credentials.

### Intermediate — PostgreSQL RLS Tenant Isolation, CosmosDB Partition Keys, Audit Logging

**PostgreSQL Row-Level Security — database-enforced multi-tenant isolation:**
```sql
CREATE TABLE tenant_data (
    id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    data TEXT
);
ALTER TABLE tenant_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_data FORCE ROW LEVEL SECURITY; -- Apply even to table owners

CREATE FUNCTION current_tenant_id() RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.tenant_id', true), '')::UUID;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE POLICY tenant_isolation ON tenant_data
    FOR ALL USING (tenant_id = current_tenant_id());
```

Set tenant context from .NET middleware before each request's DB operations:
```csharp
await using var cmd = conn.CreateCommand();
cmd.CommandText = "SET LOCAL app.tenant_id = @tenantId";
cmd.Parameters.AddWithValue("tenantId", tenantIdFromJwt);
await cmd.ExecuteNonQueryAsync();
```

**RLS is deny-by-default:** enabling it without policies blocks ALL access. Always index
`tenant_id` columns for performance.

**CosmosDB multi-tenant isolation** — hierarchical partition keys for large tenants:
```csharp
ContainerProperties properties = new(
    id: "events",
    partitionKeyPaths: new List<string> { "/tenantId", "/userId", "/sessionId" });
```

For many small tenants, use `tenantId` as the partition key (most cost-effective). For tenants
exceeding 20GB, use Hierarchical Partition Keys.

**pgAudit for PostgreSQL audit logging:**
```bash
az postgres flexible-server parameter set \
  --server-name myserver --resource-group myRG \
  --name pgaudit.log --value "WRITE,DDL"
```

Query audit logs: `AzureDiagnostics | where Message contains "AUDIT:" | where TimeGenerated > ago(1d)`

### Advanced — Customer-Managed Keys, Unity Catalog Column Security, Purview

**Disable key-based CosmosDB auth entirely to enforce RBAC:**
```bash
az cosmosdb update --name myaccount --resource-group myRG --disable-local-auth true
```

**Databricks Unity Catalog column-level security via masking functions:**
```sql
CREATE FUNCTION mask_email(email STRING) RETURNS STRING
RETURN CASE
  WHEN IS_ACCOUNT_GROUP_MEMBER('pii-readers') THEN email
  ELSE CONCAT('***', SUBSTRING(email, LOCATE('@', email)))
END;

ALTER TABLE customers ALTER COLUMN email SET MASK mask_email;
```

**Row filters:**
```sql
ALTER TABLE sales SET ROW FILTER filter_fn ON (region);
```

Use Unity Catalog for all data governance in Databricks. Never access data directly via storage
account keys — use service principals with Unity Catalog RBAC.

**Microsoft Purview** for cross-platform data classification: register CosmosDB (schema from
first 10 docs per container), PostgreSQL, and Unity Catalog (full metadata + lineage) in Purview
Data Map. Configure scanning schedules and apply sensitivity labels.

---

## DOMAIN 5: AI TOOL SECURITY (CLAUDE CODE AND CURSOR)

### Foundational — The Threat Model Every Team Must Understand

AI coding tools introduce five systemic risks:
1. **Data exfiltration** — code sent to external APIs may include secrets
2. **Prompt injection** via malicious context (doc strings, comments, file names)
3. **Model hallucination** of insecure patterns
4. **Intellectual property exposure**
5. **Compliance gaps** — 63% of breached organizations lacked AI tool governance

Research from Apiiro (September 2025): AI-generated code introduced **10,000+ new security
findings per month** — a 10x increase from December 2024. Veracode found only **55% of
AI-generated code was secure** across 100+ LLMs.

**Most common security anti-patterns AI tools generate:**
- **CWE-798 Hardcoded credentials:** `var connString = "Server=prod;Password=abc123";`
- **CWE-89 SQL injection:** `FromSqlRaw($"SELECT * FROM Users WHERE Id = {userId}")`
- **CWE-862 Missing authorization:** Controller actions without `[Authorize]`
- **CWE-79 XSS in React:** `dangerouslySetInnerHTML={{ __html: userData.bio }}`
- **CWE-502 Insecure deserialization:** `TypeNameHandling = TypeNameHandling.All`
- **CWE-327 Weak cryptography:** `MD5.Create()` for password hashing

Treat all AI-generated code as an untrusted pull request from a junior developer.

### Intermediate — Claude Code and Cursor Enterprise Configuration

**Claude Code settings hierarchy** (highest to lowest precedence):
1. Enterprise `managed-settings.json` (cannot be overridden by users)
2. CLI arguments
3. `.claude/settings.local.json`
4. `.claude/settings.json` (committed to repository)
5. User settings

**Enterprise-managed configuration — deploy this to every developer machine:**
```json
// Linux:   /etc/claude-code/managed-settings.json
// macOS:   /Library/Application Support/ClaudeCode/managed-settings.json
// Windows: %ALLUSERSPROFILE%\ClaudeCode\managed-settings.json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./appsettings.*.json)",
      "Read(~/.aws/**)",
      "Read(~/.ssh/**)",
      "Read(~/.azure/**)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Bash(nc:*)"
    ],
    "disableBypassPermissionsMode": "disable",
    "defaultMode": "ask"
  },
  "sandbox": { "enabled": true, "allowUnsandboxedCommands": false },
  "enableAllProjectMcpServers": false,
  "forceLoginMethod": "console",
  "forceLoginOrgUUID": "YOUR-ORG-UUID"
}
```

**Cursor privacy and file exclusions:**
- Enable Privacy Mode: Settings → General → Privacy Mode (enforces zero data retention)
- Create `.cursorignore` in every repository:
```
.env
.env.*
*.pem
*.key
*.pfx
appsettings.Production.json
appsettings.Staging.json
secrets/
.azure/
.aws/
.ssh/
local.settings.json
launchSettings.json
```

**Known limitation:** `.cursorignore` blocks the agent from reading files but does not prevent
it from suggesting code that references those files by name. CVE-2025-59944 demonstrated a
filename case bypass on Windows/macOS. Do not rely on `.cursorignore` as the sole control.

**Certifications:** Claude Code has SOC 2 Type II, ISO 27001:2022, and ISO/IEC 42001:2023.
Cursor has SOC 2 Type II. Both offer zero-retention agreements for enterprise/team plans. Code
is **not used for training** under commercial terms.

### Advanced — PostToolUse Semgrep Hook, Security-First Prompting, Org Policy

**PostToolUse Semgrep hook — wire this in every project's `.claude/settings.json`:**
```json
{
  "hooks": {
    "PostToolUse": {
      "Edit": "semgrep scan --config p/secrets --config p/owasp-top-ten --quiet ${CLAUDE_FILE_PATH}"
    }
  }
}
```

This runs Semgrep on every file edit automatically. If Semgrep finds an issue, fix it before
proceeding — never move to the next step with an open finding.

**Claude Code Security Review GitHub Action:**
```yaml
- uses: anthropics/claude-code-security-review@main
  with:
    comment-pr: true
    claude-api-key: ${{ secrets.CLAUDE_API_KEY }}
```

**Security-first prompting template:**
```
Create a .NET 8 Web API endpoint for user registration.
THREAT MODEL: Public-facing, potential credential stuffing.
SECURITY REQUIREMENTS:
  - Authentication: [Authorize(Policy = "WriterOrAdmin")]
  - Authorization: no user-owned data, standard RBAC
  - Input validation: FluentValidation with email, name, password complexity
  - Rate limiting: 5 requests/min per IP
  - Logging: log attempt with userId, never log password
  - Error messages: generic (no account enumeration)
```

**Organizational AI security policy elements:**
- Approved tool list (e.g., Claude Code + Cursor only, with enterprise configs deployed)
- Data classification rules: PHI/PCI/credentials never enter AI context
- Mandatory human security review for all AI-generated code before merging
- Immediate credential rotation if an AI tool reads a secrets file
- Annual AI security awareness training

---

## DOMAIN 6: AZURE INFRASTRUCTURE AND DEVSECOPS

### Foundational — Key Vault, Private Endpoints, Network Isolation

**Azure Key Vault — required Bicep configuration:**
```bicep
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    sku: { family: 'A', name: 'premium' }
    tenantId: tenant().tenantId
    enableRbacAuthorization: true       // Use RBAC, not legacy access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true         // Cannot be disabled once set — intentional
    publicNetworkAccess: 'Disabled'
    networkAcls: { defaultAction: 'Deny', bypass: 'AzureServices' }
  }
}
```

**Private Endpoints for Key Vault:**
```bicep
resource kvPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pe-keyvault'
  location: location
  properties: {
    subnet: { id: dataSubnetId }
    privateLinkServiceConnections: [{
      name: 'kv-connection'
      properties: {
        privateLinkServiceId: vault.id
        groupIds: ['vault']
      }
    }]
  }
}
```

**Required private DNS zones (always hardcode — never use suffixes expressions):**
- Key Vault: `privatelink.vaultcore.azure.net`
- Cosmos DB: `privatelink.documents.azure.com`
- PostgreSQL: `privatelink.postgres.database.azure.com`
- Databricks: `privatelink.azuredatabricks.net`
- Storage: `privatelink.blob.core.windows.net`

**Known Bicep bug:** `environment().suffixes.keyvaultDns` returns `.vault.azure.net` but the
correct private DNS zone is `privatelink.vaultcore.azure.net` — always hardcode.

**Note on Azure Blueprints:** Blueprints is deprecated (EOL July 2026). Replace with Deployment
Stacks: `az stack group create --name stack-myapp --deny-settings-mode denyWriteAndDelete`

### Intermediate — Defender for Cloud, KQL Detection Queries, App Insights

**Enable all Microsoft Defender for Cloud plans:**
```bash
az security pricing create --name CloudPosture --tier Standard
az security pricing create --name VirtualMachines --tier Standard
az security pricing create --name AppService --tier Standard
az security pricing create --name KeyVaults --tier Standard
az security pricing create --name CosmosDbs --tier Standard
az security pricing create --name Containers --tier Standard
az security pricing create --name Arm --tier Standard
```

**Application Insights — use connection string, not instrumentation key (deprecated):**
```bicep
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'ai-webapi'
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    DisableLocalAuth: true  // Force Managed Identity, not local auth keys
  }
}
```

**KQL detection queries for Log Analytics:**

```kql
// Brute force detection — more than 10 failed logins per hour per user/IP
SigninLogs
| where ResultType != "0"
| summarize FailedCount = count() by UserPrincipalName, IPAddress, bin(TimeGenerated, 1h)
| where FailedCount > 10

// Key Vault access anomalies — unauthorized or forbidden access attempts
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT"
| where ResultSignature in ("Forbidden", "Unauthorized")
| summarize Count = count() by CallerIPAddress, OperationName

// Sensitive role assignments — detect privilege escalation attempts
AzureActivity
| where OperationNameValue =~ "MICROSOFT.AUTHORIZATION/ROLEASSIGNMENTS/WRITE"
| project TimeGenerated, Caller, OperationNameValue, ResourceGroup

// API rate limit violations
AppRequests
| where ResultCode == "429"
| summarize Count = count() by ClientIP, bin(TimeGenerated, 5m)
| where Count > 50
```

### Advanced — Full DevSecOps Pipeline, Managed Identity Chain, AKS Workload Identity

**Complete DevSecOps pipeline — all gates required, no soft-fails:**
```yaml
# .github/workflows/devsecops.yml
name: DevSecOps Pipeline
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
permissions:
  security-events: write
  contents: read

jobs:
  sast-semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: 'p/security-audit p/owasp-top-ten p/csharp p/typescript'
          generateSarif: true
      - uses: github/codeql-action/upload-sarif@v3
        with: { sarif_file: semgrep.sarif }
        if: always()

  sast-codeql:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with: { languages: 'csharp, javascript' }
      - uses: github/codeql-action/analyze@v3

  sca-snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: snyk/actions/dotnet@master
        env: { SNYK_TOKEN: '${{ secrets.SNYK_TOKEN }}' }
        with: { args: '--severity-threshold=high' }

  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }  # full history required
      - uses: gitleaks/gitleaks-action@v2
        env: { GITHUB_TOKEN: '${{ secrets.GITHUB_TOKEN }}' }

  container-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t myapp:${{ github.sha }} .
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:${{ github.sha }}'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

  iac-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: bridgecrewio/checkov-action@master
        with: { directory: 'infra/', framework: bicep, soft_fail: false }

  deploy:
    needs: [sast-semgrep, sast-codeql, sca-snyk, secrets-scan, container-scan, iac-scan]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: echo "All security gates passed — deploying"
```

**Zero-secrets Managed Identity chain — full Bicep:**
```bicep
// User-assigned identity shared across services
resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-myapp'
  location: location
}

// Key Vault Secrets User (role ID: 4633458b-17de-408a-b874-0445c86b69e6)
resource kvRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: vault
  name: guid(vault.id, appIdentity.id, '4633458b-17de-408a-b874-0445c86b69e6')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Cosmos DB Built-in Data Contributor
resource cosmosRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, appIdentity.properties.principalId, 'contributor')
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: appIdentity.properties.principalId
    scope: cosmosAccount.id
  }
}

// Storage Blob Data Contributor (role ID: ba92f5b4-2d11-453d-a403-e96b0029c9fe)
resource storageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, appIdentity.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions',
      'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
```

**AKS Workload Identity** (Pod Identity is deprecated, EOL September 2025):

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile: { type: RuntimeDefault }
  containers:
  - name: api
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities: { drop: [ALL] }
```

---

## TWELVE HIGHEST-IMPACT ACTIONS (IN PRIORITY ORDER)

1. **Replace all connection-string-with-keys patterns with Managed Identity RBAC** — the single
   biggest attack surface reduction across the entire stack.
2. **Enforce Authorization Code + PKCE on all SPAs** while disabling implicit grant in app
   registrations.
3. **Deploy Private Endpoints** for every PaaS service (Key Vault, Cosmos DB, PostgreSQL,
   Databricks, Storage).
4. **Enable Microsoft Defender for Cloud** across all plans.
5. **Implement the DevSecOps pipeline** with quality gates that block on HIGH/CRITICAL findings.
6. **Deploy enterprise-managed settings** for Claude Code and Cursor with file deny rules.
7. **Add PostToolUse Semgrep hooks** to every repository's `.claude/settings.json`.
8. **Enable Key Vault RBAC, soft-delete, and purge protection** on every vault.
9. **Implement PostgreSQL RLS** for multi-tenant data isolation.
10. **Enable Unity Catalog** for all Databricks data governance with column masking on PII.
11. **Wire Gitleaks** with full git history scan (`fetch-depth: 0`) on every PR.
12. **Set `ClockSkew = TimeSpan.Zero`** and verify `UseAuthentication` precedes
    `UseAuthorization` in every .NET API.

The maturity tiers are not sequential gates — they represent increasing depth. A team can
implement Foundational across all six domains in the first sprint, then progressively deepen
into Intermediate and Advanced tiers over subsequent quarters.

Zero-secrets architecture through Managed Identity is the foundation everything else builds upon.
Without it, Key Vault references, Private Endpoints, and RBAC assignments are incomplete controls.

---
name: codebase-modernization
description: >
  Use this skill whenever you are working on an EXISTING codebase that needs to be modernized,
  migrated, or brought up to the Security-First Scrum standard. Trigger when asked to: fix
  security issues in legacy code, migrate authentication to MSAL/Entra ID, replace hardcoded
  secrets with Key Vault, fix SQL injection, add authorization to unprotected endpoints, extract
  business logic from controllers, add tests to untested code, install a DevSecOps pipeline,
  modernize infrastructure with Private Endpoints or Managed Identity, or perform any incremental
  security hardening of existing .NET / React / Blazor / Cosmos DB / PostgreSQL / Databricks
  code on Azure. This skill governs the migration path; the security-first-scrum skill governs
  the destination. The three laws still apply, but the sequencing and tactics are different:
  you are a surgeon operating on a live patient, not building from scratch.
---

# Security-First Scrum: Codebase Modernization

You are modernizing an existing codebase toward the Security-First Scrum standard. The rules are
different from greenfield work. Read this document in full before touching any file.

---

## PART 1: THREE LAWS (UNCHANGED — ALWAYS IN THIS ORDER)

**Law 1 — Security First.** Never introduce a new vulnerability while fixing an old one. Never
leave a surface more exposed than you found it.

**Law 2 — People First.** The humans own the migration strategy and the risk decisions. You
execute the technical steps they have scoped. Do not attempt autonomous infrastructure changes,
secret rotation, or scope expansion without confirmation.

**Law 3 — Incremental / Agile.** Every PR must leave the codebase in a better and working state.
No big-bang rewrites. No broken builds between steps.

---

## PART 2: MODERNIZATION PRIME DIRECTIVE

Before touching any file:

1. Run the Phase 0 assessment protocol. Understand what you are walking into.
2. Confirm the scope of this specific task with the human. Scope creep during migration breaks
   things.
3. Identify whether the change is security-critical (Phase 1-3), architectural (Phase 4-5), or
   operational (Phase 6-8). Do not mix phases in a single PR.
4. Verify existing tests pass before you start. You own the baseline. If they were already broken,
   surface that immediately — do not inherit a broken build silently.
5. Make your change. Re-run tests. The codebase must be passing when you are done.

**The iron rule of modernization:** every PR leaves the codebase more secure and working than
before. A PR that improves architecture but introduces a regression is not acceptable. A PR that
removes a vulnerability but breaks auth is not acceptable.

**Stop and surface to the human when:**
- You discover a vulnerability outside the scope of the current task (log it; do not fix it
  unilaterally)
- The existing code has no tests and adding the security control requires refactoring untested code
- A dependency is so outdated that upgrading it would require cascading changes beyond sprint scope
- You find hardcoded credentials — rotate them before doing anything else (Phase 1)

---

## PART 3: TRIAGE PRIORITY SYSTEM

When a codebase has multiple issues, address them in this order. Do not reorder based on what
seems more interesting or architectural.

| Priority | Category | Rationale |
|---|---|---|
| **P0 — Immediate** | Hardcoded secrets / credentials in source code | Active exposure. Every minute counts. |
| **P0 — Immediate** | Broken or missing authentication on production endpoints | Active exploitation surface. |
| **P1 — This Sprint** | SQL injection / non-parameterized queries | High CVSS; straightforward fix. |
| **P1 — This Sprint** | `localStorage` token storage in React | XSS + token theft = full account compromise. |
| **P1 — This Sprint** | Missing or permissive CORS (`AllowAnyOrigin`) | Cross-origin attack surface on production. |
| **P2 — Next Sprint** | Implicit Grant auth flow still in use | Deprecated; migration is planned work. |
| **P2 — Next Sprint** | Connection strings with keys (replace with Managed Identity) | High value; requires infra coordination. |
| **P2 — Next Sprint** | Missing rate limiting on public endpoints | Abuse surface; not currently exploited. |
| **P3 — Backlog** | Architecture violations (business logic in controllers, etc.) | Quality debt; not an active security risk. |
| **P3 — Backlog** | Missing test coverage on non-security paths | Quality debt; address incrementally. |
| **P3 — Backlog** | Missing XML doc comments / docstrings | Documentation debt. |

---

## PART 4: PHASE 0 — CODEBASE ASSESSMENT (RUN BEFORE TOUCHING ANYTHING)

Run this assessment on every codebase you are asked to modernize. Produce a written finding
summary before writing a single line of migration code.

### 4.1 Secrets Scan — Run First, No Exceptions

```bash
# Full history scan — not just HEAD
gitleaks detect --source . --log-opts "--all" --report-format json --report-path gitleaks-report.json
# Current working tree
gitleaks detect --source . --report-format json --report-path gitleaks-current.json
# npm / pip dependency secrets
trufflehog filesystem . --json > trufflehog-report.json
```

If secrets are found: Stop. Do not proceed with any other migration work. Report to the human
immediately. Credentials must be rotated before the codebase is touched further.

### 4.2 Dependency Vulnerability Scan

```bash
dotnet list package --vulnerable --include-transitive > dotnet-vulns.txt
npm audit --json > npm-audit.json
pip install safety && safety check --json > safety-report.json
pip install bandit && bandit -r src/ -f json -o bandit-report.json
```

Categorize: CRITICAL (this sprint), HIGH (next sprint), MEDIUM/LOW (backlog).

### 4.3 Authentication Surface Map

For every .NET controller and every React/Blazor route, record:
```
Endpoint / Route | Auth required? | Current mechanism | Auth flow | Token storage | Notes
```

Flag any endpoint that:
- Has no `[Authorize]` decorator and serves non-public data
- Uses Implicit Grant flow
- Stores tokens in `localStorage`
- Uses a shared app registration across environments
- Has hardcoded `ClientSecret` in configuration

### 4.4 Authorization / BOLA Check

For every endpoint that returns or modifies user-owned data:
```
Endpoint | Returns user-owned data? | Ownership check present? | Where? (controller/service/none)
```

### 4.5 Database Query Safety Audit

```bash
# .NET — find raw SQL with string interpolation
grep -rn "FromSqlRaw\|ExecuteSqlRaw\|FromSqlInterpolated" src/ --include="*.cs"
grep -rn '"\s*SELECT\|"\s*INSERT\|"\s*UPDATE\|"\s*DELETE' src/ --include="*.cs"
# Python
grep -rn 'execute.*f"SELECT\|execute.*%.*SELECT' src/ --include="*.py"
```

### 4.6 Secrets in Configuration Files

```bash
grep -rn "Password=\|pwd=\|AccountKey=\|SharedAccessKey=" . \
  --include="*.json" --include="*.yaml" --include="*.yml" --include="*.env" \
  --exclude-dir=node_modules --exclude-dir=.git
```

### 4.7 Architecture Layer Violations (.NET)

```bash
# Business logic / DB in controllers
grep -rn "DbContext\|CosmosClient\|NpgsqlConnection" src/ --include="*.cs" | grep -i "controller"
# Repository calls from controllers
grep -rn "IRepository\|Repository" src/ --include="*.cs" | grep -i "controller"
```

### 4.8 Frontend Security Audit

```bash
grep -rn "localStorage" src/ --include="*.ts" --include="*.tsx" | grep -i "token\|auth\|jwt"
grep -rn "dangerouslySetInnerHTML" src/ --include="*.tsx" --include="*.jsx"
grep -rn "AllowAnyOrigin\|origin.*\*" . --include="*.ts" --include="*.json"
```

### 4.9 Assessment Report Template

```markdown
## Codebase Assessment — [Date] — [Repo Name]

### P0 Findings (Immediate)
- [ ] [Finding] — [File:Line] — [Impact]

### P1 Findings (This Sprint)
### P2 Findings (Next Sprint)
### P3 Findings (Backlog)

### Existing Test Coverage
- Overall: X%
- Security test coverage: X% (estimate)
- Integration tests present: yes/no

### Architecture Health
- Layer violations found: X
- Missing interfaces: X
- Controllers with direct DB access: X
```

Hand this to the human before writing any migration code. They scope the sprints; you execute.

---

## PART 5: PHASE 1 — SECRETS AND CREDENTIALS (HIGHEST PRIORITY)

### 5.1 When You Find a Hardcoded Secret

1. Do not commit the file with the secret still present. Never.
2. Report to the human immediately — they must rotate it before you make the replacement commit.
3. After rotation is confirmed, replace with Key Vault reference pattern (§5.2).
4. After the replacement PR is merged, clean git history using `git filter-repo` (NOT
   `git filter-branch` — deprecated).

### 5.2 Replacing Connection Strings with Key Vault References

**Before (dangerous — never leave in place):**
```json
{
  "ConnectionStrings": {
    "CosmosDb": "AccountEndpoint=https://account.documents.azure.com:443/;AccountKey=ACTUAL_KEY;"
  }
}
```

**Step 1 — Add Key Vault to configuration bootstrap:**
```csharp
// Program.cs
var kvName = builder.Configuration["KeyVaultName"]; // non-secret; safe in appsettings
if (!string.IsNullOrEmpty(kvName))
{
    var kvUri = new Uri($"https://{kvName}.vault.azure.net/");
    builder.Configuration.AddAzureKeyVault(
        kvUri, new DefaultAzureCredential(),
        new AzureKeyVaultConfigurationOptions { ReloadInterval = TimeSpan.FromMinutes(5) });
}
```

**Step 2 — Replace Cosmos DB connection string with Managed Identity:**
```csharp
// BEFORE (delete this)
var cosmosClient = new CosmosClient(configuration["ConnectionStrings:CosmosDb"]);
// AFTER
var credential = builder.Environment.IsDevelopment()
    ? new DefaultAzureCredential()
    : new ManagedIdentityCredential();
services.AddSingleton(_ => new CosmosClient(
    configuration["CosmosDb:Endpoint"], credential,
    new CosmosClientOptions { ConnectionMode = ConnectionMode.Direct }));
```

**Step 3 — Replace PostgreSQL connection string with Managed Identity token:**
```csharp
// BEFORE (delete this)
services.AddNpgsqlDataSource(configuration["ConnectionStrings:PostgreSQL"]);
// AFTER
var connStringWithoutPassword = configuration["PostgreSQL:ConnectionStringNoPassword"];
services.AddSingleton(_ =>
{
    var credential = builder.Environment.IsDevelopment()
        ? new DefaultAzureCredential()
        : new ManagedIdentityCredential();
    var dataSourceBuilder = new NpgsqlDataSourceBuilder(connStringWithoutPassword);
    dataSourceBuilder.UsePeriodicPasswordProvider(async (_, ct) =>
    {
        var token = await credential.GetTokenAsync(new TokenRequestContext(
            new[] { "https://ossrdbms-aad.database.windows.net/.default" }), ct);
        return token.Token;
    }, TimeSpan.FromHours(4), TimeSpan.FromSeconds(10));
    return dataSourceBuilder.Build();
});
```

### 5.3 .gitignore — Verify Completeness

```
.env
.env.*
!.env.example
appsettings.Development.json
appsettings.Production.json
appsettings.Staging.json
local.settings.json
launchSettings.json
*.pem
*.key
*.pfx
secrets/
.azure/
.aws/
.ssh/
```

---

## PART 6: PHASE 2 — AUTHENTICATION AND AUTHORIZATION MIGRATION

### 6.1 Find Unprotected Controllers

```bash
grep -rn "public class.*Controller" src/ --include="*.cs" -l | while read f; do
  if ! grep -q "\[Authorize" "$f"; then
    echo "No [Authorize] found: $f"
  fi
done
grep -rn "\[AllowAnonymous\]" src/ --include="*.cs"  # each needs a documented reason
```

### 6.2 Migrating to Microsoft.Identity.Web

**Before (legacy JWT):**
```csharp
services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options => {
        options.TokenValidationParameters = new TokenValidationParameters {
            ValidIssuer = "https://sts.windows.net/YOUR-TENANT/",
            ValidAudience = "api://YOUR-APP-ID",
            // Common legacy mistake: ClockSkew left at default 5 minutes
        };
    });
```

**After (Microsoft.Identity.Web):**
```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"));
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("AdminOnly",     p => p.RequireRole("Admin"))
    .AddPolicy("ReaderOrAdmin", p => p.RequireRole("Reader", "Admin"))
    .AddPolicy("WriterOrAdmin", p => p.RequireRole("Writer", "Admin"));
```

Required packages:
```bash
dotnet add package Microsoft.Identity.Web
dotnet add package Azure.Identity
# Remove any hand-rolled JWT validation packages
```

### 6.3 Adding [Authorize] — Controller by Controller

Do this controller-by-controller, not as a mass change. Each controller = its own PR:

```csharp
[ApiController]
[Route("api/v1/[controller]")]
[Authorize]  // minimum: authenticated caller required
public class DocumentsController : ControllerBase { }

[HttpGet("{id}")]
[Authorize(Policy = "ReaderOrAdmin")]
public async Task<ActionResult<DocumentResponse>> GetByIdAsync(string id, CancellationToken ct) { }

[HttpGet("health")]
[AllowAnonymous] // REASON: Public health check — no data returned
public IActionResult Health() => Ok("healthy");
```

### 6.4 Adding BOLA Protection to Existing Endpoints

BOLA is the most common API vulnerability and is usually completely absent. Add it to the
service layer — not the controller:

```csharp
// BEFORE: No ownership check
public async Task<DocumentModel> GetDocumentAsync(string documentId, CancellationToken ct)
{
    return await _repository.FindByIdAsync(documentId, ct);
}

// AFTER: Ownership enforced before data is returned
public async Task<DocumentModel> GetDocumentAsync(
    string documentId, string requestingUserId, CancellationToken ct)
{
    var document = await _repository.FindByIdAsync(documentId, ct);
    if (document.OwnerId != requestingUserId)
        throw new ResourceOwnershipException(
            $"User {requestingUserId} does not own document {documentId}");
    return document;
}
```

Controller side — extract userId from JWT:
```csharp
var userId = User.GetObjectId()  // Microsoft.Identity.Web extension method
    ?? throw new UnauthorizedAccessException("UserId claim missing from token");
var document = await _documentService.GetDocumentAsync(id, userId, ct);
```

### 6.5 Migrating React from localStorage to sessionStorage

```typescript
// BEFORE — delete this
cache: { cacheLocation: "localStorage" }
// AFTER
cache: { cacheLocation: "sessionStorage", storeAuthStateInCookie: false }
```

### 6.6 Migrating from Implicit Grant to Authorization Code + PKCE

**What you do (code):** Verify MSAL.js v3 is installed.
```bash
npm install @azure/msal-browser@latest @azure/msal-react@latest
```

**What the human does (Azure portal):**
- App registration → Authentication → Remove checkboxes for "Access tokens" and "ID tokens"
  under Implicit grant.
- Verify redirect URIs are correct.

### 6.7 Middleware Pipeline Order — Fix If Wrong

This is the single most common .NET security misconfiguration:

```csharp
// CORRECT ORDER
app.UseHsts();
app.UseHttpsRedirection();
app.UseSerilogRequestLogging();
app.UseRouting();
app.UseRateLimiter();
app.UseCors("SpaPolicy");
app.UseAuthentication();  // WHO are you? — MUST come before UseAuthorization
app.UseAuthorization();   // WHAT can you do?
app.MapControllers();
```

If `UseAuthorization` appears before `UseAuthentication` in existing code: this is a P0 finding.
The middleware silently treats all requests as unauthenticated. Fix immediately.

---

## PART 7: PHASE 3 — INPUT VALIDATION AND QUERY SAFETY

### 7.1 Replacing String-Interpolated SQL Queries

**.NET / Npgsql:**
```csharp
// BEFORE — SQL injection vulnerable
var users = await _conn.QueryAsync<User>(
    $"SELECT * FROM users WHERE email = '{email}' AND tenant_id = '{tenantId}'");
// AFTER — parameterized
var users = await _conn.QueryAsync<User>(
    "SELECT * FROM users WHERE email = @email AND tenant_id = @tenantId",
    new { email, tenantId });
```

**.NET / Cosmos DB:**
```csharp
// BEFORE — string interpolation in Cosmos query
var query = new QueryDefinition(
    $"SELECT * FROM c WHERE c.userId = '{userId}' AND c.type = '{docType}'");
// AFTER — parameterized
var query = new QueryDefinition(
    "SELECT * FROM c WHERE c.userId = @userId AND c.type = @docType")
    .WithParameter("@userId", userId)
    .WithParameter("@docType", docType);
```

**EF Core:**
```csharp
// BEFORE — vulnerable
var results = _context.Users.FromSqlRaw($"SELECT * FROM Users WHERE Id = {userId}");
// AFTER — prefer LINQ (EF generates safe SQL)
var results = _context.Users.Where(u => u.Id == userId);
```

### 7.2 Adding FluentValidation

```bash
dotnet add package FluentValidation
dotnet add package FluentValidation.DependencyInjectionExtensions
# Do NOT install FluentValidation.AspNetCore — it is deprecated
```

```csharp
public class CreateUserRequestValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserRequestValidator()
    {
        RuleFor(x => x.Name).NotEmpty().MaximumLength(100)
            .Matches(@"^[\w\s\-'\.]+$").WithMessage("Name contains invalid characters.");
        RuleFor(x => x.Email).NotEmpty().EmailAddress().MaximumLength(254);
    }
}
builder.Services.AddValidatorsFromAssemblyContaining<CreateUserRequestValidator>();
```

### 7.3 Fixing dangerouslySetInnerHTML

```bash
grep -rn "dangerouslySetInnerHTML" src/ --include="*.tsx" --include="*.jsx"
```

For each hit with user-controlled content:
```tsx
// BEFORE — XSS vulnerability
<div dangerouslySetInnerHTML={{ __html: userProfile.bio }} />
// AFTER — DOMPurify sanitization
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{
  __html: DOMPurify.sanitize(userProfile.bio, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'a'],
    FORBID_TAGS: ['script', 'style', 'iframe'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick'],
  })
}} />
```

### 7.4 Tightening CORS

```csharp
// BEFORE — never acceptable in production
app.UseCors(builder => builder.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());
// AFTER — exact allowed origins from configuration
var allowedOrigins = builder.Configuration
    .GetSection("Cors:AllowedOrigins").Get<string[]>()
    ?? throw new InvalidOperationException("Cors:AllowedOrigins must be configured");
builder.Services.AddCors(options =>
{
    options.AddPolicy("SpaPolicy", policy => policy
        .WithOrigins(allowedOrigins)
        .AllowAnyHeader().AllowAnyMethod().AllowCredentials());
});
```

### 7.5 Adding Rate Limiting

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(
        httpContext => RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: httpContext.User.Identity?.Name
                ?? httpContext.Connection.RemoteIpAddress?.ToString() ?? "anon",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 60, Window = TimeSpan.FromMinutes(1), QueueLimit = 0,
            }));
});
// In middleware pipeline — MUST be after UseRouting, before UseAuthentication
app.UseRateLimiter();
```

---

## PART 8: PHASE 4 — ARCHITECTURE REFACTORING (P3 PRIORITY)

**Do not start Phase 4 if P0–P2 work is outstanding. Architecture refactoring carries the most
risk of regressions. Every change must be covered by tests before and after.**

### 8.1 Extracting Business Logic from Controllers

Use the extract → interface → test → delete approach (never all at once):

```csharp
// BEFORE: Controller doing direct DB work and business logic
[HttpPost]
public async Task<IActionResult> CreateOrder(CreateOrderRequest request)
{
    if (request.Quantity > 100) return BadRequest("Quantity exceeds limit");  // business logic
    var order = new Order { ... };
    await _dbContext.Orders.AddAsync(order);   // direct DB — wrong layer
    await _dbContext.SaveChangesAsync();
    return CreatedAtAction(...);
}

// AFTER STEP 1: Interface first
public interface IOrderService
{
    Task<OrderModel> CreateOrderAsync(
        CreateOrderRequest request, string requestingUserId, CancellationToken ct);
}

// AFTER STEP 2: Implement the service (write test first)
public class OrderService : IOrderService
{
    private readonly IOrderRepository _repository;
    public async Task<OrderModel> CreateOrderAsync(
        CreateOrderRequest request, string requestingUserId, CancellationToken ct)
    {
        if (request.Quantity > 100)
            throw new ValidationException("Quantity exceeds the maximum of 100.");
        var order = new Order { OwnerId = requestingUserId, ... };
        return await _repository.SaveAsync(order, ct);
    }
}

// AFTER STEP 3: Controller becomes thin
[HttpPost]
[Authorize(Policy = "WriterOrAdmin")]
public async Task<ActionResult<OrderResponse>> CreateAsync(
    CreateOrderRequest request, CancellationToken ct)
{
    var userId = User.GetObjectId()
        ?? throw new UnauthorizedAccessException("UserId missing from token");
    var order = await _orderService.CreateOrderAsync(request, userId, ct);
    return CreatedAtAction(nameof(GetByIdAsync), new { id = order.Id },
        _mapper.Map<OrderResponse>(order));
}
```

### 8.2 Extracting Repositories from Services

```csharp
// Interface in Infrastructure/Repositories/Interfaces/
public interface IOrderRepository
{
    Task<OrderModel> FindByIdAsync(string id, CancellationToken ct);
    Task<OrderModel> SaveAsync(OrderModel order, CancellationToken ct);
    Task DeleteAsync(string id, CancellationToken ct);
}

// Fake for unit tests (in Mocks/)
public class FakeOrderRepository : IOrderRepository
{
    private readonly Dictionary<string, OrderModel> _store = new();
    public Task<OrderModel> FindByIdAsync(string id, CancellationToken ct)
    {
        if (!_store.TryGetValue(id, out var order))
            throw new NotFoundException($"Order {id} not found.");
        return Task.FromResult(order);
    }
    public Task<OrderModel> SaveAsync(OrderModel order, CancellationToken ct)
    {
        _store[order.Id] = order; return Task.FromResult(order);
    }
    public Task DeleteAsync(string id, CancellationToken ct)
    {
        if (!_store.Remove(id)) throw new NotFoundException($"Order {id} not found.");
        return Task.CompletedTask;
    }
    public IReadOnlyList<OrderModel> GetAll() => _store.Values.ToList();
    public int Count => _store.Count;
    public void Clear() => _store.Clear();
}
```

### 8.3 Typed Exception Hierarchy

```csharp
// Domain layer
public abstract class AppException : Exception { ... }
public sealed class ValidationException : AppException { ... }
public sealed class NotFoundException : AppException { ... }
public sealed class AuthException : AppException { ... }          // never retry
public sealed class ResourceOwnershipException : AppException { ... } // never retry
public sealed class TransientException : AppException { ... }    // retry with backoff

// Global exception handler — maps to RFC 7807 ProblemDetails
public class GlobalExceptionHandler : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(HttpContext ctx, Exception ex, CancellationToken ct)
    {
        var (statusCode, title) = ex switch
        {
            ValidationException         => (400, "Validation failed"),
            NotFoundException           => (404, "Resource not found"),
            AuthException               => (401, "Authentication required"),
            ResourceOwnershipException  => (403, "Access denied"),
            TransientException          => (503, "Service temporarily unavailable"),
            _                           => (500, "An unexpected error occurred"),
        };
        // Never leak internal details to clients
        var problem = new ProblemDetails
        {
            Status = statusCode, Title = title,
            Extensions = { ["correlationId"] = ctx.TraceIdentifier }
        };
        _logger.LogError(ex, "Request failed: {StatusCode} {Title} (CorrelationId: {CorrelationId})",
            statusCode, title, ctx.TraceIdentifier);
        ctx.Response.StatusCode = statusCode;
        await ctx.Response.WriteAsJsonAsync(problem, ct);
        return true;
    }
}
```

---

## PART 9: PHASE 5 — TEST COVERAGE AND SECURITY TESTS

When inheriting a codebase with low coverage, do not try to achieve 80% in one sprint. Add
tests in this priority order:

1. Security tests first — auth bypass, BOLA, injection (even for code not being changed)
2. Tests for code you are about to change — write characterization tests before refactoring
3. Critical business logic — paths that, if broken, cause financial loss or data corruption
4. Error paths — 4xx and 5xx responses
5. Happy path coverage — fill in remaining gaps

### 9.1 Characterization Tests (Before Refactoring Untested Code)

```csharp
[Fact]
[Trait("Type", "Characterization")]
public async Task CreateOrder_ExistingBehavior_ReturnsCreatedWithCurrentLogic()
{
    // Documents what the code CURRENTLY does before you change it
    // TODO: [TICKET-123] Replace with proper TDD test after service extraction
}
```

### 9.2 Security Test Template for Existing Endpoints

```csharp
[Fact]
public async Task GetById_NoAuthToken_Returns401() { ... }
[Fact]
public async Task GetById_ExpiredToken_Returns401() { ... }
[Fact]
public async Task GetById_WrongRole_Returns403() { ... }
[Fact]
public async Task GetById_ValidTokenButNotOwner_Returns403() { /* BOLA test */ }
[Theory]
[InlineData("'; DROP TABLE orders; --")]
[InlineData("<script>alert('xss')</script>")]
[InlineData("../../../etc/passwd")]
public async Task CreateOrder_AdversarialInput_Returns400(string maliciousInput) { ... }
```

### 9.3 Coverage Gates — Introduce Incrementally

Do not set coverage gates to 80% on a codebase with 20% coverage. Set it at current + 5%,
ratchet up each sprint. The coverage gate should **never decrease**.

```xml
<!-- .runsettings — adjust minimum to current actual coverage -->
<CoverageThreshold>
  <LineCoverage minimum="35" />  <!-- start at actual; increase 5% each sprint -->
</CoverageThreshold>
```

---

## PART 10: PHASE 6 — LOGGING AND OBSERVABILITY

### 10.1 Migrating from Console.WriteLine to Structured Logging

```csharp
// BEFORE: unstructured, not searchable
Console.WriteLine($"Processing order {orderId} for user {userId}");
// AFTER: structured, searchable in Application Insights
_logger.LogInformation("Processing order {OrderId} for {UserId}", orderId, userId);
```

### 10.2 Adding Correlation ID Propagation

```csharp
public class CorrelationIdMiddleware
{
    private const string HeaderName = "x-correlation-id";
    public async Task InvokeAsync(HttpContext context)
    {
        var correlationId = context.Request.Headers[HeaderName].FirstOrDefault()
            ?? Guid.NewGuid().ToString("N");
        context.Response.Headers[HeaderName] = correlationId;
        using var scope = _logger.BeginScope(
            new Dictionary<string, object> { ["CorrelationId"] = correlationId });
        context.TraceIdentifier = correlationId;
        await _next(context);
    }
}
app.UseMiddleware<CorrelationIdMiddleware>(); // before UseRouting
```

### 10.3 Removing PII from Existing Logs

```bash
grep -rn "_logger\.\|Log\.\|Console\." src/ --include="*.cs" | \
  grep -i "email\|password\|token\|ssn\|credit\|phone\|address"
```

Replace actual values with anonymized identifiers:
```csharp
// BEFORE — logs actual email address
_logger.LogInformation("User {Email} logged in", user.Email);
// AFTER — logs only anonymized ID
_logger.LogInformation("User {UserId} logged in", user.Id);
```

---

## PART 11: PHASE 7 — DEVSECOPS PIPELINE INSTALLATION

Install the pipeline on every repository, even before other phases are complete. A pipeline
that catches some issues on day one is better than a perfect pipeline on day ninety.

### 11.1 Minimal Viable Security Pipeline (Install First)

```yaml
# .github/workflows/security.yml
name: Security Gates
on:
  push: { branches: [main, develop] }
  pull_request: { branches: [main] }
permissions:
  security-events: write
  contents: read

jobs:
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }  # full history required for Gitleaks
      - uses: gitleaks/gitleaks-action@v2
        env: { GITHUB_TOKEN: '${{ secrets.GITHUB_TOKEN }}' }

  sast-semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: 'p/secrets p/owasp-top-ten p/csharp p/typescript'
          generateSarif: true
      - uses: github/codeql-action/upload-sarif@v3
        with: { sarif_file: semgrep.sarif }
        if: always()
```

### 11.2 Adding Gates Progressively (One Job Per Sprint)

```yaml
# Sprint 2 — add when dependency audit is clean enough to gate on
  sca:
    uses: snyk/actions/dotnet@master
    with: { args: '--severity-threshold=high' }

# Sprint 2 — add when Docker images are in use
  container-scan:
    if: hashFiles('Dockerfile') != ''
    # trivy CRITICAL,HIGH exit-code 1

# Sprint 3 — add when IaC exists
  iac-scan:
    if: hashFiles('infra/**/*.bicep') != ''
    # checkov bicep soft_fail false

# Sprint 3 — add when coverage gate is established
  build-and-test:
    # dotnet test with coverage threshold
```

### 11.3 Pre-Commit Hook

```bash
pip install pre-commit
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks: [{ id: gitleaks }]
  - repo: https://github.com/returntocorp/semgrep
    rev: v1.45.0
    hooks:
      - id: semgrep
        args: ['--config', 'p/secrets', '--config', 'p/owasp-top-ten', '--error']
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks: [{ id: detect-private-key }, { id: detect-aws-credentials }]

# Each developer runs once after cloning:
pre-commit install
```

---

## PART 12: PHASE 8 — INFRASTRUCTURE MODERNIZATION

This phase requires coordination with the Azure admin. You produce the Bicep; the human reviews
and applies it. Do not provision infrastructure autonomously.

### 12.1 Key Vault Hardening

```bash
az keyvault show --name <vault-name> --query '{
  rbacEnabled: properties.enableRbacAuthorization,
  softDelete: properties.enableSoftDelete,
  purgeProtection: properties.enablePurgeProtection,
  publicAccess: properties.publicNetworkAccess
}'
```

```bicep
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  properties: {
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true      // IRREVERSIBLE — confirm with human before applying
    publicNetworkAccess: 'Disabled'
    networkAcls: { defaultAction: 'Deny', bypass: 'AzureServices' }
  }
}
```

### 12.2 Private Endpoint — Sequence Matters

**The sequence matters.** Disabling public network access before the Private Endpoint is
configured will break all connectivity. Always:

1. Add the Private Endpoint
2. Verify connectivity via the private endpoint
3. Then disable public network access

### 12.3 Managed Identity Role Assignment — Add Before Switching Code

Always assign the Managed Identity role **before** switching the connection code:

1. Assign the role in Azure
2. Verify the assignment propagates (can take 2-5 minutes)
3. Deploy the code change
4. Remove the old connection string from Key Vault (not before)

```bicep
// Cosmos DB Built-in Data Contributor assignment
resource cosmosRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, apiManagedIdentityPrincipalId, 'data-contributor')
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: apiManagedIdentityPrincipalId
    scope: cosmosAccount.id
  }
}
```

---

## PART 13: MIGRATION EXECUTION PROTOCOL (9 STEPS)

For every migration task, follow this sequence. The codebase must be passing after every step.

```
STEP 1 — BASELINE
  Run existing tests. Record the pass/fail count.
  If tests were already failing: report to human before proceeding.
  Run the Phase 0 assessment grep commands relevant to this component.

STEP 2 — SCOPE CONFIRMATION
  State exactly what you are changing in this PR.
  State what you are NOT changing.
  If you discover P0 findings outside scope: log them; do not fix unilaterally.

STEP 3 — CHARACTERIZATION (if refactoring untested code)
  Write characterization tests that capture current behavior before changing anything.
  Run them. They must pass before you proceed.

STEP 4 — MAKE THE CHANGE
  Apply the migration change (one logical change per PR).
  Do not mix phases in a single PR.

STEP 5 — SECURITY TEST
  Write the adversarial test that proves the attack is now blocked.
  Write the positive test that proves the legitimate path still works.
  Run both. Both must pass.

STEP 6 — QUALITY GATE
  Run: format check → lint → type check → full test suite.
  Coverage must not decrease from baseline recorded in Step 1.

STEP 7 — SEMGREP SCAN
  semgrep scan --config p/secrets --config p/owasp-top-ten <changed_files>
  Zero medium+ findings. Fix any before committing.

STEP 8 — COMMIT
  Conventional Commits format. Use 'security' type for security fixes.
  One logical change per commit.
  No secrets: verify with: git diff --cached | grep -i "password\|secret\|key"

STEP 9 — DOCUMENT THE FINDING
  Update the migration log: what was found, what was fixed, what remains outstanding.
```

### Commit Message Conventions for Migration Work

```
# Security fixes
security(api): add BOLA ownership check to document retrieval
security(auth): migrate JWT validation to Microsoft.Identity.Web
security(config): replace Cosmos DB connection string with Managed Identity
security(react): migrate MSAL token storage from localStorage to sessionStorage

# Architecture migration
refactor(service): extract order business logic from OrdersController
refactor(repo): introduce IOrderRepository and Fake implementation
refactor(domain): define typed exception hierarchy

# Pipeline installation
ci: add Gitleaks secrets scan to PR gate
ci: add Semgrep OWASP SAST to PR gate
```

---

## PART 14: THE STRANGLER FIG PATTERN

Do not rewrite existing code wholesale. Use the strangler fig:

- New code is written to the full Security-First Scrum standard.
- Old code is migrated one component at a time, each PR fully tested.
- The old implementation is removed only after the new one is verified in production.
- Feature flags decouple migration from release — the new auth flow can be deployed but not
  activated until validated.

Every migration PR has a clear before and after state. The old code is removed in the same PR
that confirms the new code works. Never leave both old and new implementation in the codebase
simultaneously with unclear which one is authoritative.

---

## PART 15: THINGS TO NEVER DO DURING MODERNIZATION

### Never — They Make the Codebase Less Safe

- Disable or soft-fail a security gate to unblock a migration PR. Fix the finding.
- Remove `[Authorize]` from an endpoint to make a test pass. Fix the test infrastructure.
- Commit a "temporary" hardcoded secret while working out Key Vault integration. There is no
  temporary credential in git history.
- Rewrite authentication from scratch without testing every endpoint in the system.
- Mix architectural refactoring (Phase 4) with security fixes (Phase 1-3) in the same PR.
- Use `AllowAnyOrigin()` temporarily with a plan to tighten later. "Later" does not happen.
- Switch to `ManagedIdentityCredential` before the role assignment is confirmed in Azure.
- Disable public network access on a PaaS resource before a Private Endpoint is configured.
- Delete old authentication code before the new flow is verified working in staging.
- Set coverage gates at 80% on a 20% codebase. Set at current + 5%.
- Fix a vulnerability in a different component than the one tasked. Log it. Surface it.

### Never — They Violate People First

- Make infrastructure changes (Bicep, role assignments, network rules) without human confirmation.
- Rotate credentials autonomously. Credential rotation has organizational consequences.
- Scope-creep silently. Surface immediately when the task is larger than expected.
- Leave the human with a broken build. Stop, restore last working state, report what you found.

---

## PART 16: MIGRATION ANTI-PATTERNS

**The "big bang" anti-pattern:** Attempting to migrate all authentication, fix all SQL injection,
restructure all layers, add the DevSecOps pipeline, and write all missing tests in a single
sprint. Produces a PR nobody can safely review.
*Correct approach: One phase per sprint. One component per PR.*

**The "fix it forward" anti-pattern:** Encountering a broken test and "fixing" it to make the
new code pass, without understanding why it was failing.
*Correct approach: Understand the failure. If your change is correct and the test was wrong,
update the test and document why.*

**The "security theater" anti-pattern:** Adding `[Authorize]` attributes while leaving the
middleware pipeline in the wrong order. The decorators exist; the authorization does nothing.
*Correct approach: Verify the middleware pipeline order before declaring auth migration complete.*

**The "abandoned strangler" anti-pattern:** Starting a component migration but not completing it
— leaving both old and new implementation with unclear authority.
*Correct approach: Remove old code in the same PR that verifies the new code works.*

**The "coverage inflation" anti-pattern:** Writing tests with no assertions to achieve coverage
numbers.
*Correct approach: Coverage is a signal. A test without meaningful assertions is worse than no
test — it creates false confidence.*

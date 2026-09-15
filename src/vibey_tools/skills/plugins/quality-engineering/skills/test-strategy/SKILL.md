---
name: test-strategy
description: Use when designing a test strategy, choosing a testing framework, setting up test architecture, balancing unit vs integration vs E2E tests, implementing contract testing between services, or assessing test suite health. Use whenever someone asks about how to test or what testing approach to take. Also triggers on test pyramid questions, microservice testing, Swiss Cheese model, SMURF, TDD vs BDD choices, test doubles (mock vs stub vs fake), or any question about test portfolio design.
domains:
  - testing
phases:
  - build
  - verify
technologies:
  - pytest
mandatory_sections:
  - Anti-Patterns
retrieval_version: 1
---

# Test Strategy

A comprehensive framework for designing test strategies, selecting the right testing approaches for different architectures, and building test suites that provide genuine confidence without becoming a maintenance burden.

**Core principle:** A test strategy is not a list of tools — it is an architectural decision about where to invest testing effort to maximize confidence per unit of maintenance cost.

---

## Test Shape Models: Match Your Architecture

The right test distribution is determined by your system architecture, not by dogma. Three models plus one risk framework:

### Test Pyramid (Cohn/Fowler)
```
        /\
       /E2\        ← Narrow: expensive, slow, flaky — use sparingly
      /----\
     / Int  \      ← Middle layer: module interactions
    /--------\
   / Unit     \    ← Wide base: fast, isolated, cheap
  /____________\
```

**Best for: monolithic applications** where unit-level isolation is cheap and highly informative.

- **Unit tests (60–70%):** Test single functions or classes in complete isolation. Fast (< 5 ms each), deterministic, no I/O.
- **Integration tests (20–30%):** Test module interactions, database queries, API layer behavior. Use testcontainers or emulators.
- **E2E tests (5–10%):** Test critical user journeys end-to-end. Reserve for highest-value paths only.

### Testing Trophy (Kent C. Dodds)
```
          /\
         /E2\
        /----\
       / Inte-\    ← LARGEST LAYER: integration tests dominate
      / gration\
     /----------\
    /  Unit      \
   /--------------\
  / Static Analysis\  ← Foundation: linting, type checking
 /___________________\
```

**Best for: API-centric and frontend-heavy applications.**

Key insight (Guillermo Rauch): "The more your tests resemble the way your software is used, the more confidence they can give you." For APIs, an integration test that calls through the HTTP layer with a real database gives far more confidence than 20 unit tests on isolated functions.

### Honeycomb Model (Spotify)
```
     ○ ○ ○ ○ ○    ← E2E: minimal, highest-value journeys only
  ○ ○ ○ ○ ○ ○ ○
 ○ ○ ○ INTEGRA- ○ ← Dominates: inter-service is the main risk
 ○ ○ TION ○ ○ ○ ○
  ○ ○ ○ ○ ○ ○ ○
     ○ ○ ○ ○ ○    ← Unit: only for isolated business logic
```

**Best for: microservices architectures.**

Unit tests for pure business logic (algorithms, transformations, domain rules). Integration tests for everything involving service boundaries — database queries, message queues, HTTP clients. E2E tests only for the most critical cross-service user journeys.

**Why Honeycomb:** In microservices, the complexity lives *between* services. A unit test of the order service tells you nothing about whether it integrates correctly with inventory. The inter-service integration is where bugs live.

### Swiss Cheese Model (James Reason, 1990)

The Swiss Cheese model is not a distribution — it is a **risk framework** for explaining why layered testing is necessary. Use this with stakeholders.

```
Static  Unit  Integration  Contract  E2E   Monitoring
  |       |       |           |       |        |
 [■■□■]  [■□■■]  [□■■■]     [■■□■]  [■□□■]   [■■■□]
  
Defects escape to production only when holes align across ALL layers.
```

Each layer has gaps (the "holes"):
- **Static analysis** catches syntax, type errors, security patterns — but not logic bugs
- **Unit tests** catch function-level logic — but not integration failures
- **Integration tests** catch component interaction bugs — but not cross-service contract violations
- **Contract tests** catch API compatibility — but not full user journey failures
- **E2E tests** catch journey-level failures — but are too slow/brittle to run on everything
- **Production monitoring** catches what everything else missed — but after users are affected

No single layer is sufficient. Defects escape when holes align. The goal is to ensure holes rarely align.

**Use this model in risk conversations:** "We don't have contract tests, which means our Swiss Cheese model has a full hole in that layer. Any provider API change will escape through to production."

---

## SMURF: Test Portfolio Health Evaluation

Google's SMURF framework (October 2024, Google Testing Blog) evaluates test portfolio health across five dimensions:

| Dimension | Evaluation Question | Healthy | Unhealthy |
|---|---|---|---|
| **Speed** | How fast is the suite? | Unit < 5 min; Full suite < 30 min | Any test blocking CI for > 1 hour |
| **Maintainability** | How easy to understand and change? | Test reads like documentation | Requires deep context to understand what's being tested |
| **Utilization** | How often are tests actually run? | All tests run on every PR | Significant tests only run on main or nightly |
| **Reliability** | How consistent are results? | < 2% flake rate per test | Retries regularly needed; "it passed on the retry" |
| **Fidelity** | How closely does the test simulate real usage? | Integration tests use real data formats and flows | Everything mocked; tests don't represent real behavior |

A test suite can score well on coverage while failing SMURF. A 90% coverage suite where half the tests are slow, flaky, and mock everything is worse than a 60% coverage suite where every test is fast, stable, and meaningful.

**Run a SMURF audit quarterly.** Each dimension can degrade independently without coverage numbers moving.

---

## TDD vs. BDD vs. ATDD: When to Use Each

### Test-Driven Development (TDD)
**When to use:** Building new code where the design is uncertain. TDD drives good design by making you write tests first — the resulting code must be testable by construction.

**Cycle:** Red → Green → Refactor
1. Write a failing test (Red) — must fail for the right reason
2. Write minimum code to pass (Green) — no more, no less
3. Refactor — improve structure without breaking tests

**London School (Mockist):** Mock all collaborators; test in strict isolation. Best for legacy code with unclear boundaries.
**Chicago School (Classicist):** Use real objects; mock only I/O boundaries. Best for new code with well-defined domain.

**Not a good fit for:** exploratory work where the requirements themselves are unclear; UI testing; performance testing.

### Behavior-Driven Development (BDD)
**When to use:** When you want test specifications that non-technical stakeholders can read and verify. BDD tests document behavior in business language (Gherkin: Given/When/Then).

```gherkin
Scenario: Successful password reset
  Given a user with email "user@example.com" exists
  And the user has not reset their password in the last 24 hours
  When the user requests a password reset link
  Then an email is sent to "user@example.com" within 60 seconds
  And the link expires after 1 hour
```

**Best fit:** APIs with complex business rules; features where the business logic is the source of truth; scenarios with multiple stakeholders who need to agree on behavior.

**Not a good fit for:** Low-level technical code (use TDD instead); scenarios where Gherkin would be artificially verbose.

### Acceptance Test-Driven Development (ATDD)
**When to use:** When you need the entire team — developer, tester, and business analyst — to agree on behavior *before* development begins.

**Three Amigos:** Before writing any code, three roles collaborate:
1. **Business Analyst / Product Owner** — what is the business rule?
2. **Developer** — how will this be implemented? What are the edge cases?
3. **Tester** — what could go wrong? What are the negative scenarios?

Together they write Gherkin scenarios that become the acceptance criteria and the test suite simultaneously.

**Key distinction from BDD:** ATDD is a *process* (collaboration before development); BDD is a *format* (Gherkin syntax). You can do BDD without ATDD (writing scenarios after the fact) or ATDD without Gherkin (using plain English acceptance criteria).

---

## Consumer-Driven Contract Testing

### When to Use Contract Testing
Use contract testing when you have **microservices with separate deployment cycles**. If services are always deployed together, you don't need contract tests. If a service can be deployed independently, you need to know its contracts are satisfied before deployment.

**The problem contract testing solves:** Service A consumes Service B's API. Service B adds a new required field. Service A deploys without knowing. Production breaks.

### The Pact Flow

```
CONSUMER SIDE                          PROVIDER SIDE
─────────────                          ─────────────
1. Write interaction test              4. Provider downloads pacts
   (expected request + response)           from Pact Broker
        ↓                                     ↓
2. Pact generates contract             5. Provider verifier runs
   (.json pact file)                       against real provider code
        ↓                                     ↓
3. Publish to Pact Broker              6. Publish verification results
        ↓                                     ↓
                    7. can-i-deploy checks compatibility
                       before any deployment to production
```

### Key Principles

**Consumer-driven contracts mean consumers set the rules.** The consumer defines what it needs from the provider. The provider must satisfy those needs. This inverts the traditional approach where providers define APIs and consumers adapt.

**Pact Broker is required for multi-team use.** The broker stores contracts, verification results, and enables the `can-i-deploy` gate.

**can-i-deploy is the deployment gate:**
```bash
# This command asks: "Can OrderService v1.2.3 be deployed to production?"
# It checks all consumer contracts are verified for this version
pact-broker can-i-deploy \
  --pacticipant OrderService \
  --version 1.2.3 \
  --to-environment production
# Returns: 0 (can deploy) or 1 (cannot deploy, contract violations exist)
```

### What Contract Tests Do NOT Cover
- Performance characteristics of the provider
- Business logic inside the provider
- Error scenarios beyond what the consumer test specifies
- Non-functional requirements

Contract tests verify **compatibility**, not **correctness**. You still need integration and E2E tests.

---

## Property-Based Testing with Hypothesis

### When to Use Property-Based Testing
Property-based testing (Hypothesis) finds edge cases that example-based tests miss. Use it for:

| Good fit | Poor fit |
|---|---|
| Pure functions (no side effects) | UI flows |
| Data transformations | Performance testing |
| Serialization / deserialization | Complex setup/teardown scenarios |
| Parsers and validators | Anything requiring real external services |
| Mathematical operations | |
| State machines | |
| Round-trip properties (encode → decode = original) | |

### How Hypothesis Works
1. Generates inputs based on your strategy specifications
2. Runs your test with hundreds/thousands of generated inputs
3. When it finds a failure, **shrinks** the input to the minimal failing case
4. Reports the minimal reproduction

Shrinking is what makes property-based testing practical: the actual failing input might be 10,000 characters, but Hypothesis shrinks it to `""` or `"a"` — the root cause.

### Common Properties to Test

```python
# Round-trip: encode then decode returns original
@given(st.text())
def test_json_round_trip(s):
    assert json.loads(json.dumps({"value": s}))["value"] == s

# Invariant: sorted list is always ordered
@given(st.lists(st.integers()))
def test_sort_preserves_all_elements(lst):
    sorted_lst = sorted(lst)
    assert len(sorted_lst) == len(lst)
    assert sorted(sorted_lst) == sorted_lst

# Commutativity: order doesn't matter
@given(st.integers(), st.integers())
def test_addition_is_commutative(a, b):
    assert a + b == b + a

# No crash guarantee: valid inputs should never raise unexpected exceptions
@given(st.text(min_size=1, max_size=255))
def test_username_validation_never_crashes(username):
    try:
        result = validate_username(username)
        assert isinstance(result, bool)  # always returns a bool
    except ValueError:
        pass  # ValueError is acceptable for invalid inputs
    # Any other exception is a bug
```

---

## Mutation Testing: Validating Your Test Suite

Mutation testing introduces code mutations (changes to operators, conditions, return values) and verifies your tests catch them. It answers the question: "Do my tests actually detect bugs, or do they just run code?"

**Mutation score = killed mutants / total non-equivalent mutants × 100**

A mutation score below 60% means your tests have significant gaps — regardless of coverage percentage. High coverage + low mutation score = tests are checking behavior happened, not that it happened *correctly*.

### Tool Selection
- **mutmut** — simplest to use; good default choice for most Python projects
- **cosmic-ray** — more configurable; supports parallel execution; better for large codebases

### When to Run Mutation Testing
Mutation testing is **too slow for CI gates** on large codebases. Use it as:
- **Pre-release audit** — run on business-critical modules before major releases
- **Test quality assessment** — run when a bug escaped your test suite to understand why
- **Onboarding benchmark** — establish baseline mutation scores for new modules

**Don't gate PRs on mutation score** (too slow). Do track mutation scores in your quality metrics dashboard and investigate declining trends.

---

## Test Doubles: Mock vs. Stub vs. Spy vs. Fake

Understanding the distinction prevents over-mocking (London school trap) and under-isolation (integration test creep).

| Double | What It Is | When to Use |
|---|---|---|
| **Stub** | Returns canned responses; doesn't verify calls | Providing test data; avoiding real I/O |
| **Mock** | Verifies calls were made; has expected behavior | Verifying interactions with collaborators |
| **Spy** | Wraps real object; records calls for later assertion | Verifying calls on a real object you can't replace |
| **Fake** | Working implementation simplified for testing | In-memory database; fake email service |
| **Dummy** | Placeholder that's never called | Satisfying required parameters that aren't used |

### Decision Guide

```
Is this crossing an I/O boundary? (network, disk, external service)
  → YES: Use a stub or fake. Always.
  → NO: Do you need to verify the interaction happened?
         → YES: Use a mock (carefully)
         → NO: Use the real object
```

**Don't mock what you don't own.** If you're mocking `requests.get()` directly, you're coupling your tests to an implementation detail. Instead: wrap the HTTP call in your own `HttpClient` class and mock *that*.

**Fake vs. Mock for databases:**
- For unit tests: use an in-memory fake (dictionary-backed repository)
- For integration tests: use a real database in testcontainers
- Never mock your ORM/database driver directly — tests become lies

---

## Anti-Patterns

### Testing Implementation, Not Behavior

**Bad:** Test that `UserService.__init__` calls `Repository.__init__` with specific parameters
**Good:** Test that creating a user through `UserService.create_user()` results in a user that can be retrieved

Tests should survive refactoring. If renaming an internal variable breaks a test, the test is testing the wrong thing.

### Brittle Tests

**Signs:** Tests break when unrelated code changes; tests depend on specific database row ordering; tests use hardcoded timestamps

**Fix:** Use domain-specific test data builders; avoid ordering dependencies; inject clocks and use `freezegun` for time-sensitive tests

### Slow Test Suites

**Signs:** Developers run tests "occasionally"; CI pipeline takes > 30 minutes; "I'll run tests later"

**Fix:** 
- Separate fast unit tests (run locally) from slow integration tests (run in CI)
- Parallelize with `pytest-xdist -n auto`
- Use `pytest -m "not slow"` for local development feedback loop
- Target: unit suite < 5 min, full suite < 30 min

### No Test Isolation

**Signs:** Tests pass in isolation, fail in sequence; tests leave data in databases; "works on my machine"

**Fix:**
- Each test owns its setup and teardown
- Use transaction rollback or container restart between tests (not manual cleanup)
- Never share mutable state between tests

### Coverage Anti-Patterns

**100% coverage target:** Causes trivial tests that don't verify behavior to be written. The coverage metric becomes gamed. Stop when you hit 100%, not when you've verified all behavior.

**Counting untested code as passing:** Missing a test for a critical path is not "acceptable coverage" — it's a risk.

**Fix:** Set a minimum floor (80% overall, 100% for critical paths). Track **coverage delta** on PRs to prevent regression. Focus investment on **behavior verification**, not percentage maximization.

---

## Test Data Management

### Factories vs. Fixtures vs. Test Containers

| Approach | When to Use | Example |
|---|---|---|
| **Hardcoded values** | Simple, obvious test data | `user = User(name="Alice")` |
| **Factory functions** | Reusable, customizable test data | `user_factory(role="admin")` |
| **factory_boy** | Complex objects with relationships | `UserFactory(orders__count=3)` |
| **Fixtures (pytest)** | Shared infrastructure (DB session, HTTP client) | `@pytest.fixture(scope="session")` |
| **testcontainers** | Real service dependencies | PostgreSQL, Redis, Kafka, Azurite |

### Factory Pattern

```python
# factories.py
import factory
from faker import Faker
from myapp.models import User, Order

fake = Faker()

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    id = factory.LazyFunction(lambda: str(uuid4()))
    email = factory.LazyFunction(fake.email)
    name = factory.LazyFunction(fake.name)
    role = "user"
    
    class Params:
        admin = factory.Trait(role="admin")

# Usage
user = UserFactory()                    # default user
admin = UserFactory(admin=True)         # admin user
custom = UserFactory(email="user@example.com")  # specific email
```

### Test Data Isolation Rule
Never share mutable test data between tests. Each test creates its own data. Tests that share data are tests that depend on execution order — the definition of a fragile test suite.

---

## Performance Testing Strategy

Performance testing is not a single test type — it is a progression:

| Test Type | Purpose | When to Run |
|---|---|---|
| **Baseline** | Establish normal performance under expected load | Before any load testing |
| **Load** | Verify system performs under expected traffic | Every release for critical services |
| **Stress** | Find the breaking point | Quarterly for capacity planning |
| **Soak/Endurance** | Find memory leaks, resource exhaustion | Before major releases |
| **Spike** | Verify recovery from sudden traffic increases | Before marketing campaigns |

**Locust for Python load testing:**
```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(0.5, 2.0)
    
    @task(3)  # runs 3x more often than weight 1 tasks
    def get_products(self):
        self.client.get("/api/products?page=1&size=20")
    
    @task(1)
    def create_order(self):
        self.client.post("/api/orders", json={
            "productId": "PROD-123",
            "quantity": 1
        })
```

**Defining pass/fail criteria** (required for CI integration):
```python
# locust pass/fail criteria
--headless
--users 100
--spawn-rate 10
--run-time 60s
--html report.html
# Exit codes: 0=pass, 1=fail (if Locust thresholds exceeded)
# Configure in locust.conf: stop-on-fail, exit-code-on-error
```

---

## Security Testing Integration

Security testing should be distributed across all layers, not isolated to a pentest phase:

| Layer | Security Test Type | Tool | Timing |
|---|---|---|---|
| **Static analysis** | SAST (source code vulnerabilities) | Bandit, Semgrep | Every PR |
| **Unit** | Input validation logic | pytest with adversarial inputs | Every PR |
| **Integration** | Auth enforcement, SQL injection | pytest with malicious payloads | Every PR |
| **Contract** | API security headers, auth requirements | Pact with security scenarios | Every PR |
| **E2E** | DAST (runtime vulnerability scanning) | OWASP ZAP baseline | Every build |
| **Pentest** | Manual exploitation, business logic | Internal quarterly, external annually | Scheduled |

**OWASP ZAP baseline scan in CI:**
```yaml
- task: CmdLine@2
  displayName: 'OWASP ZAP Baseline Scan'
  inputs:
    script: |
      docker run -t owasp/zap2docker-stable zap-baseline.py \
        -t https://staging.myapp.com \
        -J zap-report.json \
        -x zap-report.xml
```

The baseline scan catches common vulnerabilities (missing security headers, information disclosure) automatically. It will not catch business logic vulnerabilities or complex authentication bypass — that requires human testing.

---

## Assessing Test Suite Health: Diagnostic Questions

Use these questions to diagnose an existing test suite before recommending improvements:

**Coverage and Distribution**
- What is the current line coverage? Branch coverage? (Branch coverage reveals ~25% more untested paths)
- What is the distribution of unit vs. integration vs. E2E tests?
- Does the distribution match the architecture (pyramid for monolith, trophy for API, honeycomb for microservices)?

**Speed and Reliability**
- How long does the full test suite take to run?
- What is the flake rate? (Target < 2% per test; > 2% requires immediate attention)
- Are there tests that only run in CI, not locally?

**Confidence**
- When tests pass, do developers feel confident deploying?
- How many production bugs were caught by tests vs. escaped to production?
- Is there a mutation score for critical modules?

**Maintenance**
- When business logic changes, how many tests break that shouldn't?
- How long does it take to update tests after a refactor?
- Are there tests that test implementation rather than behavior?

**Integration and Contract**
- Do you have contract tests for all microservice boundaries?
- Do integration tests use real services (via testcontainers) or mocked responses?
- Are there any E2E tests that could be replaced with more reliable integration tests?

---

## Test Strategy Document: One-Page Template

For communicating test strategy to stakeholders:

```
TEST STRATEGY: [System Name]

ARCHITECTURE TYPE: [Monolith / API / Microservices / Frontend]
RECOMMENDED SHAPE: [Pyramid / Trophy / Honeycomb]

TEST DISTRIBUTION TARGET:
  Unit tests:           [X%] — [rationale]
  Integration tests:    [X%] — [rationale]
  Contract tests:       [X%] — [rationale, if microservices]
  E2E tests:            [X%] — [rationale]

QUALITY GATES:
  Coverage threshold:   [80%] overall, [100%] for [list critical paths]
  Flake rate:           < 2% per test
  Full suite runtime:   < [30 min]
  SAST scan:            0 Critical/High findings

RISK COVERAGE (Swiss Cheese):
  ✓ Static analysis (Ruff, mypy, Bandit)
  ✓ Unit tests
  ✓ Integration tests (testcontainers)
  ○ Contract tests [MISSING — see Q3 OKR]
  ✓ E2E tests (smoke tests for critical journeys)
  ✓ Production monitoring (Application Insights alerts)

CURRENT STATE:
  Coverage: [X%] | Flake rate: [X%] | Suite runtime: [Xm]
  Top risk: [e.g., no contract tests for InventoryService boundary]

IMPROVEMENT PRIORITY:
  1. [Highest-impact gap]
  2. [Second priority]
  3. [Third priority]
```

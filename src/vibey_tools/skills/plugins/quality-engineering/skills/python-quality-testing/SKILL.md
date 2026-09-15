---
name: python-quality-testing
description: Use when writing Python tests, setting up pytest, implementing TDD in Python, using Hypothesis for property-based testing, setting up mutation testing, configuring Ruff/mypy/Black, implementing contract testing with Pact, or building Python quality pipelines on Azure. Triggers on any Python testing or quality tooling question, including pytest fixtures, parametrize, conftest, coverage thresholds, testcontainers, Azurite, Cosmos DB emulator, or Azure DevOps pipeline YAML for Python.
domains:
  - testing
  - database
phases:
  - build
  - verify
languages:
  - python
technologies:
  - pytest
  - postgresql
mandatory_sections:
  - pytest: The Complete Reference
retrieval_version: 1
---

# Python Quality Testing

The definitive practitioner guide for Python quality engineering on Azure. Covers the full stack: test strategy theory, pytest ecosystem, static analysis, property-based testing, mutation testing, contract testing, Azure cloud-native testing, and CI/CD pipeline architecture.

**The 2026 Python quality stack:** pytest 9.x + Ruff + mypy + Hypothesis + Pact + mutmut + testcontainers + Azurite + Azure DevOps multi-stage pipelines.

---

## Test Shape Models: Choosing the Right Distribution

The right test distribution depends on your architecture. Three dominant models:

### Test Pyramid (Cohn, 2009 / Fowler, 2012)
- **Wide unit base** → thin integration middle → narrow E2E top
- Best for: **monolithic applications** where unit isolation is cheap and informative
- Unit tests: fast, isolated, test single functions/classes
- Integration tests: test module interactions, database queries, API contracts
- E2E tests: test full user journeys; expensive, slow, flaky — use sparingly

### Testing Trophy (Kent C. Dodds)
- **Static analysis** (foundation) → unit tests (small layer) → **integration tests (largest layer)** → E2E (narrow top)
- Best for: **API-centric and frontend-heavy applications**
- Key insight: "The more your tests resemble the way your software is used, the more confidence they can give you" (Guillermo Rauch)
- Integration tests give the most confidence per test written for APIs

### Honeycomb (Spotify)
- **Integration tests dominate** — inter-service complexity is the primary risk
- Best for: **microservices architectures**
- Unit tests for pure business logic; integration tests for everything involving service boundaries
- E2E tests minimal — too brittle and slow across many services

### Swiss Cheese Model (James Reason, 1990)
Each layer — static analysis, unit, integration, contract, E2E, production monitoring — has holes. Defects escape to production only when holes **align across all layers**. Use this model for risk conversations with stakeholders: "We need contract tests because our integration tests can't catch provider breaking changes."

---

## SMURF: Evaluating Test Portfolio Health

Google's SMURF framework (October 2024, Google Testing Blog) evaluates tests across five dimensions:

| Dimension | What It Measures | Good Sign | Bad Sign |
|---|---|---|---|
| **Speed** | How fast tests execute | Unit suite < 5 min; integration < 15 min | Any slow test blocking CI |
| **Maintainability** | Ease of understanding and updating | Tests read like documentation | Tests require context to understand |
| **Utilization** | Frequency tests are actually run | All tests run on every PR | Tests only run on main branch |
| **Reliability** | Consistency of results | < 2% flake rate per test | Retries needed to pass |
| **Fidelity** | How closely tests simulate real usage | Integration tests use real data formats | Tests mock everything away |

Run a SMURF audit quarterly. Each dimension can degrade independently.

---

## ISO/IEC 25010:2023 Quality Characteristics

The 2023 revision of the SQuaRE standard (ISO/IEC 25010) expanded from 8 to **9 product quality characteristics**. Testing strategy should cover all relevant characteristics:

| Characteristic | What It Covers | Test Approach |
|---|---|---|
| **Functional Suitability** | Completeness, correctness, appropriateness | Acceptance tests, BDD scenarios |
| **Performance Efficiency** | Time behavior, resource usage, capacity | Load testing (Locust), profiling |
| **Compatibility** | Co-existence, interoperability | Integration tests, contract tests |
| **Interaction Capability** | Usability (renamed from Usability) | UI tests, accessibility checks |
| **Reliability** | Maturity, availability, fault tolerance | Chaos engineering, FDRT measurement |
| **Security** | Confidentiality, integrity, authentication | SAST (Bandit), DAST, pen testing |
| **Maintainability** | Modularity, analyzability, testability | Mutation testing, cyclomatic complexity |
| **Flexibility** | Adaptability (renamed from Portability) | Multi-environment tests, testcontainers |
| **Safety** | *(new in 2023)* — operational constraint | Fault injection, boundary condition tests |

---

## Black-Box Test Design Techniques

Four foundational techniques defined in ISTQB CTFL v4.0 (2023) and ISO/IEC/IEEE 29119-4:2021. These are tool-agnostic and should inform pytest parametrize design.

### 1. Equivalence Partitioning (EP)
Divide input space into classes treated identically by the software. Write one test per partition.

```python
# Discount tiers: 0-99 items (no discount), 100-499 (10%), 500+ (20%)
@pytest.mark.parametrize("quantity,expected_discount", [
    (0, 0.0),       # below minimum — invalid partition
    (50, 0.0),      # no-discount partition
    (150, 0.10),    # 10% partition
    (600, 0.20),    # 20% partition
])
def test_discount_by_quantity(quantity, expected_discount):
    assert calculate_discount(quantity) == expected_discount
```

### 2. Boundary Value Analysis (BVA)
Test at and around partition boundaries. ISTQB distinguishes:
- **2-value BVA**: test at boundary and just inside the next partition
- **3-value BVA**: test just below, at, and just above each boundary

```python
@pytest.mark.parametrize("quantity,expected_discount", [
    (99, 0.0),    # just below first boundary
    (100, 0.10),  # at first boundary
    (101, 0.10),  # just above first boundary
    (499, 0.10),  # just below second boundary
    (500, 0.20),  # at second boundary
    (501, 0.20),  # just above second boundary
])
def test_discount_boundaries(quantity, expected_discount):
    assert calculate_discount(quantity) == expected_discount
```

### 3. Decision Table Testing
For complex business logic with multiple conditions, enumerate all condition combinations. Each column is a test case.

| Condition | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| Has loyalty card | Y | Y | N | N |
| Purchase > $100 | Y | N | Y | N |
| **Expected discount** | **15%** | **5%** | **10%** | **0%** |

Decision tables guarantee systematic coverage of logical branches.

### 4. State Transition Testing
Model the system as states, transitions, and events. Verify all transitions.

```python
# Order states: PENDING → CONFIRMED → SHIPPED → DELIVERED
# Each transition should have a test
@pytest.mark.parametrize("from_state,event,to_state", [
    ("PENDING", "confirm", "CONFIRMED"),
    ("CONFIRMED", "ship", "SHIPPED"),
    ("SHIPPED", "deliver", "DELIVERED"),
    ("PENDING", "cancel", "CANCELLED"),
    # Invalid transitions should raise
])
def test_order_state_transitions(from_state, event, to_state, order_factory):
    order = order_factory(state=from_state)
    order.apply_event(event)
    assert order.state == to_state
```

---

## pytest: The Complete Reference

pytest 9.x (requires Python ≥ 3.10) is the de facto Python testing standard.

### Fixtures

```python
# conftest.py — shared fixtures, auto-discovered by pytest
import pytest
from sqlalchemy import create_engine
from myapp.db import Base

@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped: one engine for entire test run."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")  # default scope
def db_session(db_engine):
    """Function-scoped: rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def user_factory(db_session):
    """Factory fixture: returns a callable."""
    def _make_user(**kwargs):
        defaults = {"email": "test@example.com", "role": "user"}
        user = User(**{**defaults, **kwargs})
        db_session.add(user)
        db_session.flush()
        return user
    return _make_user
```

**Fixture scopes:** `function` (default), `class`, `module`, `package`, `session`. Use `session` scope for expensive setup (database containers, HTTP clients). Use `function` scope for anything with mutable state.

### Parametrize (Cartesian Products)

```python
@pytest.mark.parametrize("user_role", ["admin", "editor", "viewer"])
@pytest.mark.parametrize("resource_type", ["document", "report", "dashboard"])
def test_access_control(user_role, resource_type, permission_service):
    # Creates 3 × 3 = 9 test cases automatically
    result = permission_service.can_access(user_role, resource_type)
    assert isinstance(result, bool)
```

### conftest.py Hierarchy

```
project/
├── conftest.py           # project-wide fixtures
├── tests/
│   ├── conftest.py       # test-directory-wide fixtures
│   ├── unit/
│   │   ├── conftest.py   # unit-test-specific fixtures
│   │   └── test_*.py
│   └── integration/
│       ├── conftest.py   # integration-test-specific fixtures
│       └── test_*.py
```

### Marks (Built-in and Custom)

```python
# Built-in marks
@pytest.mark.skip(reason="Known flake, tracked in JIRA-123")
@pytest.mark.xfail(reason="Bug in upstream library, expected failure")
@pytest.mark.slow  # custom mark

# pytest.ini or pyproject.toml — register custom marks
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m not slow')",
    "integration: marks tests requiring external services",
    "smoke: marks critical path smoke tests",
]

# Run only smoke tests in CI
# pytest -m smoke
# Run everything except slow tests locally
# pytest -m "not slow"
```

### Coverage with pytest-cov

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
branch = true          # always enable branch coverage
omit = ["*/migrations/*", "*/tests/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "@overload",
]
```

```bash
# Run tests with coverage
pytest --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=80
```

**Branch coverage uncovers ~25% more untested paths than line coverage.** Always enable it. Use coverage as a **floor**, not a goal — 100% coverage targets are gamed. Target: overall ≥ 80%, critical paths (auth, data access, payments) ≥ 100%.

---

## TDD: Red-Green-Refactor

Kent Beck's Test-Driven Development cycle applied in Python:

1. **Red** — write a failing test that expresses the desired behavior (the test should fail because the feature doesn't exist yet)
2. **Green** — write the minimum code needed to make the test pass (no more)
3. **Refactor** — improve the code's structure without changing its behavior (tests must still pass)

### London School vs. Chicago School

| | London School (Mockist) | Chicago School (Classicist) |
|---|---|---|
| **Focus** | Test object in complete isolation | Test behavior of a cluster of objects |
| **Approach** | Mock all collaborators | Use real objects; mock only I/O boundaries |
| **When to use** | Legacy code with unclear boundaries | New code with well-defined boundaries |
| **Risk** | Over-mocking couples tests to implementation | Integration issues found later |
| **Reference** | *GOOS* (Freeman & Pryce, 2009) | Kent Beck *TDD by Example* |

**Practical guidance:** Prefer Chicago school (real objects, mock only I/O) for new code. Mock only at infrastructure boundaries: HTTP clients, database sessions, file I/O, time, external APIs.

### autospec: The Gold Standard for Mocking

```python
from unittest.mock import patch, create_autospec
from myapp.services import EmailService, UserService

# BAD: bare Mock doesn't validate method signatures
with patch.object(EmailService, 'send') as mock_send:
    mock_send.return_value = True
    # This won't fail even if send() signature changes

# GOOD: autospec validates signatures match real object
with patch.object(EmailService, 'send', autospec=True) as mock_send:
    mock_send.return_value = True
    # This WILL fail if send() signature changes in EmailService
```

**Always prefer `autospec=True`.** It ensures mock signatures match real objects, catching API drift.

**Patching rule:** Patch where the object is **looked up**, not where it is **defined**.
```python
# myapp/orders.py imports and uses: from myapp.services import EmailService
# Correct patch location:
with patch('myapp.orders.EmailService'):  # where it's used
    pass
# NOT: patch('myapp.services.EmailService')  # where it's defined
```

---

## BDD with pytest-bdd

```gherkin
# features/checkout.feature
Feature: Shopping cart checkout

  Scenario: Successful checkout with valid payment
    Given a shopping cart with 2 items totaling $45.00
    And the customer has a valid payment method on file
    When the customer completes checkout
    Then the order is created with status "CONFIRMED"
    And the customer receives a confirmation email
```

```python
# tests/test_checkout.py
from pytest_bdd import given, when, then, scenario

@scenario('features/checkout.feature', 'Successful checkout with valid payment')
def test_checkout_success():
    pass

@given("a shopping cart with 2 items totaling $45.00")
def cart_with_items(cart_factory):
    return cart_factory(items=2, total=Decimal("45.00"))

@when("the customer completes checkout")
def complete_checkout(cart, payment_service):
    return checkout_service.process(cart, payment_service)

@then('the order is created with status "CONFIRMED"')
def verify_order_status(checkout_result):
    assert checkout_result.order.status == "CONFIRMED"
```

**Three Amigos for ATDD:** Developer + Tester + Business Analyst define Gherkin scenarios before any code is written. This is **Acceptance Test-Driven Development** — the spec is the test.

---

## Contract Testing with Pact

Consumer-driven contract testing prevents microservice integration breakage. The consumer defines expected interactions; the provider proves it can satisfy them.

### The Pact Flow

```
1. Consumer test creates interaction expectations
       ↓
2. Pact generates a .json contract file
       ↓
3. Contract published to Pact Broker
       ↓
4. Provider verification tests run against the Broker
       ↓
5. can-i-deploy gates deployment on contract compatibility
```

### Consumer Side (pact-python, Rust-backed via Pact FFI, v4 spec)

```python
# tests/consumer/test_order_client.py
import pytest
from pact import Consumer, Provider

@pytest.fixture(scope="session")
def pact():
    pact = Consumer('OrderService').has_pact_with(
        Provider('InventoryService'),
        host_name='localhost',
        port=1234,
        pact_dir='./pacts'
    )
    pact.start_service()
    yield pact
    pact.stop_service()

def test_get_product_stock(pact):
    expected = {"productId": "PROD-123", "quantity": 42, "available": True}
    
    (pact
     .given("product PROD-123 has 42 units in stock")
     .upon_receiving("a request for product stock")
     .with_request("GET", "/inventory/PROD-123")
     .will_respond_with(200, body=expected))
    
    with pact:
        result = inventory_client.get_stock("PROD-123")
        assert result.available is True
        assert result.quantity == 42
```

### Provider Verification

```python
# tests/provider/test_inventory_provider.py
import pytest
from pact import Verifier

def test_provider_pacts():
    verifier = Verifier(
        provider='InventoryService',
        provider_base_url='http://localhost:8080'
    )
    output, _ = verifier.verify_with_broker(
        broker_url='https://pact.myorg.com',
        publish_verification_results=True,
        provider_version='1.2.3'
    )
    assert output == 0  # 0 = all pacts verified
```

**Use `can-i-deploy` in CI/CD** to gate deployments on contract compatibility:
```bash
pact-broker can-i-deploy \
  --pacticipant OrderService \
  --version $GIT_SHA \
  --to-environment production
```

---

## Property-Based Testing with Hypothesis

Hypothesis (David MacIver, JOSS 2019) finds edge cases that example-based tests miss by generating thousands of random inputs and shrinking failures to minimal examples.

### Basic Usage

```python
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

@given(
    price=st.decimals(min_value=0, max_value=10000, places=2),
    quantity=st.integers(min_value=1, max_value=1000)
)
def test_order_total_always_positive(price, quantity):
    """No matter what valid price and quantity, total is always positive."""
    order = Order(price=price, quantity=quantity)
    assert order.total() > 0

@given(st.text(min_size=1, max_size=255))
def test_product_name_round_trips_through_db(name, db_session):
    """Any valid name saved to DB should come back identical."""
    product = Product(name=name)
    db_session.add(product)
    db_session.flush()
    retrieved = db_session.get(Product, product.id)
    assert retrieved.name == name
```

### Stateful Testing (RuleBasedStateMachine)

```python
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

class ShoppingCartMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.cart = ShoppingCart()
        self.model_items = {}  # simple model to verify against
    
    @initialize(product_id=st.uuids(), price=st.decimals(min_value=0.01, max_value=999.99, places=2))
    def setup_product(self, product_id, price):
        self.product_catalog = {str(product_id): price}
    
    @rule(product_id=st.uuids(), quantity=st.integers(min_value=1, max_value=10))
    def add_item(self, product_id, quantity):
        pid = str(product_id)
        if pid in self.product_catalog:
            self.cart.add_item(pid, quantity)
            self.model_items[pid] = self.model_items.get(pid, 0) + quantity
    
    @invariant()
    def cart_total_matches_model(self):
        expected = sum(
            self.product_catalog[pid] * qty
            for pid, qty in self.model_items.items()
            if pid in self.product_catalog
        )
        assert self.cart.total() == expected

TestShoppingCart = ShoppingCartMachine.TestCase
```

### When to Use Hypothesis
- **Pure functions** — math operations, data transformations, serialization/deserialization
- **Parsers and validators** — should never crash on valid input; should reject invalid input consistently
- **Round-trip properties** — encode/decode, serialize/deserialize, save/retrieve
- **Ordering and sorting** — verify invariants hold across random inputs
- **State machines** — model-based testing of complex stateful systems

**Hypothesis's shrinking** is what makes it valuable: when it finds a failing input, it automatically reduces it to the minimal case that still fails. The failure `price=0.00001` shrinks to `price=0` if that's the actual bug.

---

## Mutation Testing

Mutation testing validates your test suite by introducing code mutations and checking whether your tests catch them.

**Mutation score = (killed mutants / total non-equivalent mutants) × 100**

A mutation score below 60% indicates a weak test suite regardless of coverage percentage.

### mutmut (Simplest)

```bash
# Install
pip install mutmut

# Run on a specific module
mutmut run --paths-to-mutate src/myapp/orders.py

# View results
mutmut results
mutmut show 5  # show specific surviving mutant

# HTML report
mutmut html
```

### cosmic-ray (More Configurable)

```toml
# cosmic-ray.toml
[cosmic-ray]
module-path = "src/myapp/orders.py"
timeout = 10.0

[cosmic-ray.distributor]
name = "local"

[[cosmic-ray.interceptors]]
name = "pragma"  # skip # pragma: no mutate lines
```

```bash
cosmic-ray init cosmic-ray.toml session.sqlite
cosmic-ray exec cosmic-ray.toml session.sqlite
cosmic-ray report session.sqlite
```

### Mutation Testing as an Audit Tool
Run mutation testing **as an audit, not a CI gate**. Running on every commit is too slow. Use it:
- Before a major release to validate critical module test quality
- When onboarding a new module to establish a baseline
- When investigating why a bug escaped your test suite

Target 80%+ mutation score for business-critical code.

---

## Static Analysis: The Ruff-Led Stack

### Ruff (Replaces Flake8 + Black + isort + pyupgrade + dozens of plugins)

Ruff (Astral) is **10–100× faster** than Flake8, written in Rust. It reimplements 800+ rules from Flake8, pycodestyle, isort, pydocstyle, and more. Adopted by FastAPI, Pandas, Airflow, SciPy, and Pydantic.

```toml
# pyproject.toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "F",     # pyflakes
    "I",     # isort
    "N",     # pep8-naming
    "UP",    # pyupgrade
    "S",     # bandit (security)
    "B",     # bugbear
    "C4",    # flake8-comprehensions
    "SIM",   # flake8-simplify
    "TCH",   # type-checking imports
]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.format]
quote-style = "double"

[tool.ruff.lint.isort]
known-first-party = ["myapp"]
```

```bash
ruff check .              # lint
ruff check . --fix        # auto-fix safe issues
ruff format .             # format (Black-compatible)
ruff format . --check     # check formatting without modifying
```

### mypy (Strict Mode)

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
# Strict mode enables:
# disallow_untyped_defs = true
# disallow_any_generics = true
# warn_return_any = true
# warn_unused_ignores = true
# no_implicit_reexport = true
# strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false  # relax for tests
```

**Protocol for structural typing** (preferred over ABC in most cases):

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Repository(Protocol):
    def get(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> str: ...
    def delete(self, id: str) -> None: ...

# Works with any object that has get/save/delete methods
# No inheritance required — duck typing with type safety
```

---

## Azure Cloud-Native Testing

### Azurite (Local Azure Storage Emulator)

```python
# conftest.py
import pytest
import subprocess
import time
from azure.storage.blob import BlobServiceClient

AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KNKQi38OHD2g==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    "QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
    "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
)

@pytest.fixture(scope="session")
def azurite():
    """Start Azurite for the test session."""
    proc = subprocess.Popen(["azurite", "--silent"])
    time.sleep(2)  # wait for startup
    yield
    proc.terminate()

@pytest.fixture
def blob_client(azurite):
    client = BlobServiceClient.from_connection_string(AZURITE_CONNECTION_STRING)
    container = client.create_container("test-container")
    yield client
    client.delete_container("test-container")
```

Or use testcontainers:
```python
from testcontainers.azurite import AzuriteContainer

@pytest.fixture(scope="session")
def azurite_container():
    with AzuriteContainer() as azurite:
        yield azurite
```

### Cosmos DB Linux Emulator (vNext)

```python
# conftest.py
import pytest
from testcontainers.core.container import DockerContainer
from azure.cosmos import CosmosClient

COSMOS_EMULATOR_IMAGE = "mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview"
COSMOS_ACCOUNT_KEY = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw=="

@pytest.fixture(scope="session")
def cosmos_container():
    container = (
        DockerContainer(COSMOS_EMULATOR_IMAGE)
        .with_exposed_ports(8081, 8080)
        .with_env("AZURE_COSMOS_EMULATOR_PARTITION_COUNT", "3")
        .with_env("AZURE_COSMOS_EMULATOR_ENABLE_DATA_PERSISTENCE", "false")
    )
    with container:
        # Wait for health endpoint
        import time; time.sleep(15)
        yield container

@pytest.fixture(scope="session")
def cosmos_client(cosmos_container):
    port = cosmos_container.get_exposed_port(8081)
    client = CosmosClient(
        url=f"https://localhost:{port}",
        credential=COSMOS_ACCOUNT_KEY,
        connection_verify=False  # emulator uses self-signed cert
    )
    yield client
```

### testcontainers-python (PostgreSQL, Redis, Kafka, etc.)

```python
# conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from myapp.db import Base

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def db_engine(postgres_container):
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
```

---

## Azure DevOps Pipeline for Python

### Multi-Stage Pipeline Structure

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include: [main]
  paths:
    exclude: ['*.md', 'docs/*']

stages:
  - stage: Build
    jobs:
      - job: BuildAndLint
        pool:
          vmImage: ubuntu-latest
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
          
          - script: |
              pip install uv
              uv pip install --system -e ".[dev]"
            displayName: 'Install dependencies'
          
          - script: ruff check . && ruff format . --check
            displayName: 'Lint and format check (Ruff)'
          
          - script: mypy src/
            displayName: 'Type check (mypy)'

  - stage: Test
    dependsOn: Build
    jobs:
      - job: UnitTests
        steps:
          - script: |
              pytest tests/unit/ \
                --junitxml=junit/unit-results.xml \
                --cov=src --cov-report=xml \
                --cov-fail-under=80 -v
            displayName: 'Unit tests'
          
          - task: PublishTestResults@2
            condition: always()
            inputs:
              testResultsFormat: 'JUnit'
              testResultsFiles: '**/unit-results.xml'
              failTaskOnFailedTests: true
          
          - task: PublishCodeCoverageResults@2
            inputs:
              summaryFileLocation: '**/coverage.xml'
      
      - job: IntegrationTests
        steps:
          - script: npm install -g azurite && azurite --silent &
            displayName: 'Start Azurite'
          
          - script: |
              pytest tests/integration/ \
                --junitxml=junit/integration-results.xml -v
            displayName: 'Integration tests'
  
  - stage: Security
    dependsOn: Build
    jobs:
      - job: SecurityScan
        steps:
          - task: MicrosoftSecurityDevOps@1
            inputs:
              categories: 'code,dependencies'
              break: true  # fail pipeline on high severity
          
          - script: |
              pip install bandit
              bandit -r src/ -f json -o bandit-report.json -ll
            displayName: 'Bandit SAST'

  - stage: Deploy
    dependsOn: [Test, Security]
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployStaging
        environment: staging
        strategy:
          runOnce:
            deploy:
              steps:
                - script: echo "Deploy to staging"
```

### Parallel Test Execution

```yaml
# Split large test suite across 5 agents
strategy:
  parallel: 5
steps:
  - script: |
      pip install pytest-split
      pytest tests/ \
        --splits=$(System.TotalJobsInPhase) \
        --group=$(System.JobPositionInPhase) \
        --junitxml=junit/test-results-$(System.JobPositionInPhase).xml
```

### GitHub Actions Equivalent

```yaml
# .github/workflows/quality.yml
jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check . && ruff format . --check
      - run: mypy src/
      - run: pytest --cov=src --cov-report=xml --cov-fail-under=80
      - uses: codecov/codecov-action@v4
```

---

## Coverage Targets and Thresholds

| Code Category | Target | Rationale |
|---|---|---|
| Overall codebase | ≥ 80% | CI failure threshold |
| Critical paths (auth, payments, data access) | 100% | No uncovered path acceptable |
| New code on PRs | ≥ 80% delta | Prevent coverage regression |
| Generated code (migrations, DTOs) | Exempt | Not meaningful to test |

**Google's guidance:** 60% acceptable, 75% commendable, 90% exemplary. Set CI threshold at 80%.

**Coverage is a floor, not a goal.** A test that exercises a line without asserting anything increments coverage but adds no value. Focus test investment on behavior verification, not percentage maximization.

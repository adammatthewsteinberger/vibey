from vibey.domain.deployment import (
    VerificationContract,
    VerificationDimension,
    evaluate_verification_contract,
)


def test_verification_contract_all_dimensions_passed() -> None:
    contract = VerificationContract(
        health_endpoint="/healthz",
        smoke_tests=("curl https://app/healthz", "curl https://app/api/ping"),
        bake_window_seconds=30,
    )

    result = evaluate_verification_contract(
        contract,
        convergence_succeeded=True,
        health_status_code=200,
        smoke_commands_passed=True,
        bake_window_errors_count=0,
    )
    assert result.passed is True
    assert result.failed_dimension is None
    assert result.failure_reason is None
    assert result.dimension_results == {
        "convergence": True,
        "health": True,
        "smoke": True,
        "bake_window": True,
    }


def test_verification_contract_convergence_failure() -> None:
    contract = VerificationContract("/health", ("curl /health",), 30)
    result = evaluate_verification_contract(
        contract,
        convergence_succeeded=False,
        health_status_code=200,
        smoke_commands_passed=True,
        bake_window_errors_count=0,
    )
    assert result.passed is False
    assert result.failed_dimension == VerificationDimension.CONVERGENCE
    assert "convergence" in (result.failure_reason or "").lower()


def test_verification_contract_health_failure() -> None:
    contract = VerificationContract("/health", ("curl /health",), 30)
    result = evaluate_verification_contract(
        contract,
        convergence_succeeded=True,
        health_status_code=503,
        smoke_commands_passed=True,
        bake_window_errors_count=0,
    )
    assert result.passed is False
    assert result.failed_dimension == VerificationDimension.HEALTH
    assert "503" in (result.failure_reason or "")


def test_verification_contract_smoke_failure() -> None:
    contract = VerificationContract("/health", ("curl /health",), 30)
    result = evaluate_verification_contract(
        contract,
        convergence_succeeded=True,
        health_status_code=200,
        smoke_commands_passed=False,
        bake_window_errors_count=0,
    )
    assert result.passed is False
    assert result.failed_dimension == VerificationDimension.SMOKE
    assert "smoke" in (result.failure_reason or "").lower()


def test_verification_contract_bake_window_failure() -> None:
    contract = VerificationContract("/health", ("curl /health",), 30)
    result = evaluate_verification_contract(
        contract,
        convergence_succeeded=True,
        health_status_code=200,
        smoke_commands_passed=True,
        bake_window_errors_count=2,
    )
    assert result.passed is False
    assert result.failed_dimension == VerificationDimension.BAKE_WINDOW
    assert "bake window" in (result.failure_reason or "").lower()

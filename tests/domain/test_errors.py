from vibey.domain.errors import VibeyError


def test_vibey_error_is_an_exception() -> None:
    assert issubclass(VibeyError, Exception)

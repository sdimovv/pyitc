from pyitc import exceptions


def test_unknown_error() -> None:
    """Test instantiating an unknown error exception"""
    assert exceptions.UnknownError(123).status == 123
    assert exceptions.UnknownError(123).status.description == "Unknown status"
    assert str(exceptions.UnknownError(123)) == "Unknown status (123)."

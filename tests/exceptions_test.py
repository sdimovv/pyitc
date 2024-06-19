# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
from pyitc import exceptions


def test_unknown_error() -> None:
    """Test instantiating an unknown error exception"""
    assert exceptions.UnknownError(123).status == 123
    assert exceptions.UnknownError(123).status.description == "Unknown status"
    assert str(exceptions.UnknownError(123)) == "Unknown status (123)."

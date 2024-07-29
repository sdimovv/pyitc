# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
"""Utilities."""

from enum import IntEnum

from ._internals import _lib


class StampComparisonResult(IntEnum):
    """The ITC Stamp comparison result returned from the C API."""

    LESS_THAN = _lib.ITC_STAMP_COMPARISON_LESS_THAN
    GREATER_THAN = _lib.ITC_STAMP_COMPARISON_GREATER_THAN
    EQUAL = _lib.ITC_STAMP_COMPARISON_EQUAL
    CONCURRENT = _lib.ITC_STAMP_COMPARISON_CONCURRENT

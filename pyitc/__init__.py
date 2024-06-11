from types import MappingProxyType
from typing import Dict

from pyitc.pyitc import Stamp

from . import extended_api
from ._internals import _lib

__all__ = [
    'SUPPORTED_FEATURES',
    'extended_api',
    'Stamp'
]

SUPPORTED_FEATURES: Dict[str, bool] = MappingProxyType({
    'EXTENDED_API': bool(_lib.ITC_CONFIG_ENABLE_EXTENDED_API),
    '64_BIT_EVENT_COUNTERS': bool(_lib.ITC_CONFIG_USE_64BIT_EVENT_COUNTERS),
})
"""A mapping describing the supported features by the underlying C library"""

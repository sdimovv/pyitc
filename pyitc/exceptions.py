from enum import Enum
from typing import Union

from ._internals import _lib


class ItcStatus(int, Enum):
    """ITC Status codes returned by the C API"""

    SUCCESS = (_lib.ITC_STATUS_SUCCESS,
               "Operation succeeded")
    FAILURE = (_lib.ITC_STATUS_FAILURE,
               "Operation failed with unknown error")
    INVALID_PARAM = (_lib.ITC_STATUS_INVALID_PARAM,
                     "Operation failed due to invalid input parameter")
    INSUFFICIENT_RESOURCES = (_lib.ITC_STATUS_INSUFFICIENT_RESOURCES,
                              "Operation failed due to insufficient resources")
    OVERLAPPING_ID_INTERVAL = (_lib.ITC_STATUS_OVERLAPPING_ID_INTERVAL,
                               "Operation failed due to the detection of ITC ID interval overlap")
    CORRUPT_ID = (_lib.ITC_STATUS_CORRUPT_ID,
                  "Operation failed due to the ITC ID being corrupted")
    CORRUPT_EVENT = (_lib.ITC_STATUS_CORRUPT_EVENT,
                     "Operation failed due to the ITC Event being corrupted")
    CORRUPT_STAMP = (_lib.ITC_STATUS_CORRUPT_STAMP,
                     "Operation failed due to the ITC Stamp being corrupted")
    EVENT_COUNTER_OVERFLOW = (_lib.ITC_STATUS_EVENT_COUNTER_OVERFLOW,
                              "Operation failed due to the ITC Event counter overflowing")
    EVENT_COUNTER_UNDERFLOW = (_lib.ITC_STATUS_EVENT_COUNTER_UNDERFLOW,
                               "Operation failed due to the ITC Event counter underflowing")
    UNSUPPORTED_EVENT_COUNTER_SIZE = (_lib.ITC_STATUS_EVENT_UNSUPPORTED_COUNTER_SIZE,
                                      "Operation failed due to the serialised ITC Event counter being too big")
    INCOMPATIBLE_LIB_VERSION = (_lib.ITC_STATUS_SERDES_INCOMPATIBLE_LIB_VERSION,
                                "Operation failed due to the serialised ITC data being from an older or newer libitc version")

    UNKNOWN = (-1, "Unknown status")

    _description_: str

    @property
    def description(self) -> str:
        return self._description_

    def __new__(cls, value: int, description: str) -> "ItcStatus":
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj._description_ = description
        return obj

    @classmethod
    def _missing_(cls, value: int) -> "ItcStatus":
        # Return an `UNKNOWN` exception type but keep use the actual status
        unknown_enum_val = int.__new__(cls, value)
        unknown_enum_val._name_ = ItcStatus.UNKNOWN.name
        unknown_enum_val._value_ = value
        unknown_enum_val._description_ = ItcStatus.UNKNOWN.description
        return unknown_enum_val

    def __str__(self) -> str:
        return f"{self.description} ({self.value})."


class ItcError(Exception):
    """The base for all ITC exceptions"""

class InactiveIdError(ItcError):
    """The ID is inactive"""

    def __init__(self) -> None:
        super().__init__(
            "This ID is inactive. This is likely because it was previously "
            "used in a destructive operation (such as summing)"
        )

class InactiveEventError(ItcError):
    """The Event is inactive"""

    def __init__(self) -> None:
        super().__init__(
            "This Event is inactive. This is likely because it was previously "
            "used in a destructive operation (such as joining)"
        )

class ItcCApiError(ItcError):
    """The base for all C API ITC exceptions"""

    STATUS = ItcStatus.UNKNOWN

    def __init__(self) -> None:
        super().__init__(ItcStatus(self.STATUS))

    @property
    def status(self) -> ItcStatus:
        return self.args[0]

class UnkownError(ItcCApiError):
    """Unknown ITC error"""

    def __init__(self, status: Union[int, ItcStatus, None] = None) -> None:
        self.STATUS = ItcStatus(status or self.STATUS)
        super().__init__()

class FailureError(ItcCApiError):
    """Operation failed with unknown error"""

    STATUS: ItcStatus = ItcStatus.FAILURE

class InvalidParamError(ItcCApiError):
    """Operation failed due to invalid input parameter"""

    STATUS: ItcStatus = ItcStatus.INVALID_PARAM

class InsufficientResourcesError(ItcCApiError):
    """Operation failed due to insufficient resources"""

    STATUS: ItcStatus = ItcStatus.INSUFFICIENT_RESOURCES

class OverlappingIdIntervalError(ItcCApiError):
    """Operation failed due to the detection of ITC ID interval overlap"""

    STATUS: ItcStatus = ItcStatus.OVERLAPPING_ID_INTERVAL

class CorruptIdError(ItcCApiError):
    """Operation failed due to the ITC ID being corrupted"""

    STATUS: ItcStatus = ItcStatus.CORRUPT_ID

class CorruptEventError(ItcCApiError):
    """Operation failed due to the ITC Event being corrupted"""

    STATUS: ItcStatus = ItcStatus.CORRUPT_EVENT

class CorruptStampError(ItcCApiError):
    """Operation failed due to the ITC Stamp being corrupted"""

    STATUS: ItcStatus = ItcStatus.CORRUPT_STAMP

class EventCounterOverflowError(ItcCApiError):
    """Operation failed due to the ITC Event counter overflowing"""

    STATUS: ItcStatus = ItcStatus.EVENT_COUNTER_OVERFLOW

class EventCounterUnderflowError(ItcCApiError):
    """Operation failed due to the ITC Event counter underflowing"""

    STATUS: ItcStatus = ItcStatus.EVENT_COUNTER_UNDERFLOW

class UnsupportedEventCounterSizeError(ItcCApiError):
    """Operation failed due to the serialised ITC Event counter being too big"""

    STATUS: ItcStatus = ItcStatus.UNSUPPORTED_EVENT_COUNTER_SIZE

class IncompatibleLibVersionError(ItcCApiError):
    """Operation failed due to the serialised ITC data being from an older or newer libitc version"""

    STATUS: ItcStatus = ItcStatus.INCOMPATIBLE_LIB_VERSION

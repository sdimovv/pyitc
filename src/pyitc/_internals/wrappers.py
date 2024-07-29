# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import suppress
from sys import version_info
from typing import TYPE_CHECKING, Any, Callable

from pyitc.exceptions import ItcCApiError, ItcStatus, UnknownError
from pyitc.util import StampComparisonResult

from . import _ffi, _lib

if version_info < (3, 11):  # pragma: no cover
    from typing_extensions import Self
else:  # pragma: no cover
    from typing import Self

if TYPE_CHECKING:  # pragma: no cover
    from cffi.backend_ctypes import CTypesData  # type: ignore[import-untyped]


class ItcWrapper(ABC):
    """The base class of an ITC ID, Event or Stamp."""

    @abstractmethod
    def clone(self: Self) -> ItcWrapper:
        """Deep clone object."""

    @abstractmethod
    def is_valid(self: Self) -> bool:
        """Check the object is in a valid state."""

    @abstractmethod
    def serialise(self: Self) -> bytes:
        """Serialise the ID/Event/Stamp."""

    @classmethod
    @abstractmethod
    def deserialise(cls: type[Self], buffer: bytes | bytearray) -> ItcWrapper:
        """Deserialise an ID/Event/Stamp."""

    @abstractmethod
    def __str__(self: Self) -> str:
        """Serialise an ID/Event/Stamp to string."""

    @abstractmethod
    def _new_c_type(self: Self) -> CTypesData:
        """Allocate a new ITC/Event/Stamp."""

    @abstractmethod
    def _del_c_type(self: Self, c_type: CTypesData) -> None:
        """Free the ITC/Event/Stamp stored in `self._c_type`."""

    def __init__(self: Self, _c_type: CTypesData | None = None) -> None:
        super().__init__()
        if _c_type:
            self.__internal_c_type = _c_type
        else:
            self.__internal_c_type = self._new_c_type()

    def __del__(self: Self) -> None:
        """Deallocate the object."""
        with suppress(AttributeError):
            del self._c_type

    def __repr__(self: Self) -> str:
        """Repr the object."""
        return f"<{self.__class__.__name__} = {self!s}>"

    def __deepcopy__(self: Self, *args: Any) -> ItcWrapper:  # noqa: ANN401
        return self.clone()

    @property
    def _c_type(self: Self) -> CTypesData:
        """Get the underlying CFFI cdata object."""
        return self.__internal_c_type

    @_c_type.deleter
    def _c_type(self: Self) -> None:
        """Deallocate the underlying CFFI cdata object."""
        if is_handle_valid(self.__internal_c_type):
            self._del_c_type(self.__internal_c_type)


def _handle_c_return_status(status: int | ItcStatus) -> None:
    """Check the status and raise the appropriate :class:`ItcCApiError`."""
    if status == ItcStatus.SUCCESS:
        return

    exc_candidates = [x for x in ItcCApiError.__subclasses__() if status == x.STATUS]

    if not exc_candidates:  # pragma: no cover
        raise UnknownError(status)

    raise exc_candidates[0]


def _new_id_pp_handle() -> CTypesData:
    """Allocate a new ITC ID handle.

    This handle will be automatically freed when no longer referenced.
    """
    return _ffi.new("ITC_Id_t **")


def _new_event_pp_handle() -> CTypesData:
    """Allocate a new ITC Event handle.

    This handle will be automatically freed when no longer referenced.
    """
    return _ffi.new("ITC_Event_t **")


def _new_stamp_pp_handle() -> CTypesData:
    """Allocate a new ITC Stamp handle.

    This handle will be automatically freed when no longer referenced.
    """
    return _ffi.new("ITC_Stamp_t **")


def _call_serialisation_func(
    func: Callable[[CTypesData, CTypesData, CTypesData], int],
    pp_handle: CTypesData,
    initial_array_size: int = 64,
    max_array_size: int = 4 * 1024,
) -> bytes:
    """Call an ITC serialisation function.

    :param func: The function to call. It is assumed it takes the passed in
    handle as first argument, followed by the array and array size args
    :type func: Callable
    :param pp_handle: The ITC handle
    :type p_handle: CTypesData
    :param initial_array_size: The initial size of the C array to be passed to
    the serialisation function. This size will be doubled each time if the call
    fails with :class:`ItcStatus.INSUFFICIENT_RESOURCES`, and a new call
    attempt will be made until the call either succeeds or `max_array_size` is
    reached.
    :type initial_array_size: int
    :param max_array_size: The max allowed size of the C array before giving up
    :type max_array_size: int
    :returns: The buffer holding the serialised data
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    if initial_array_size < 1:  # pragma: no cover
        msg = "initial_array_size must be >= 1"
        raise ValueError(msg)
    if max_array_size < 1:  # pragma: no cover
        msg = "max_array_size must be >= 1"
        raise ValueError(msg)

    c_array_size = initial_array_size
    c_array: CTypesData
    p_c_array_size = _ffi.new("uint32_t *")

    status = ItcStatus.INSUFFICIENT_RESOURCES
    while status == ItcStatus.INSUFFICIENT_RESOURCES and c_array_size <= max_array_size:
        c_array = _ffi.new("uint8_t[]", c_array_size)
        p_c_array_size[0] = len(c_array)
        status = func(pp_handle[0], c_array, p_c_array_size)  # type: ignore[assignment]
        # If the call fails with insufficient resources, try again with a
        # bigger buffer
        c_array_size = min(c_array_size * 2, max_array_size)

    _handle_c_return_status(status)

    return bytes(_ffi.buffer(c_array)[: p_c_array_size[0]])


def _call_deserialisation_func(
    new_pp_handle_func: Callable[[], CTypesData],
    func: Callable[[CTypesData, CTypesData, CTypesData], int],
    buffer: bytes | bytearray,
) -> CTypesData:
    """Call an ITC deserialisation function.

    :param new_pp_handle_func: Method returning an uninitalised handle
    of the desired ITC type.
    :type new_pp_handle_func: Callable
    :param func: The function to call. It is assumed it takes the buffer
    as the first arg, followed by the buffer size and finally the handle
    :type func: Callable
    :param buffer: The buffer containing the serialised data
    :type buffer: Union[bytes, bytearray]
    :returns: The handle to the deserialised ITC type
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = new_pp_handle_func()
    c_buffer = _ffi.from_buffer("uint8_t[]", buffer, require_writable=False)
    c_buffer_size = len(c_buffer)
    _handle_c_return_status(func(c_buffer, c_buffer_size, pp_handle))
    return pp_handle


def is_handle_valid(pp_handle: CTypesData) -> bool:
    """Validate an ID/Event/Stamp handle.

    :param pp_handle: The handle to validate
    :type pp_handle: CTypesData
    :returns: True if valid, otherwise False
    :rtype: CTypesData
    """
    return pp_handle and pp_handle != _ffi.NULL and pp_handle[0] != _ffi.NULL


def new_id(*, seed: bool) -> CTypesData:
    """Allocate a new ITC ID.

    The ID must be deallocated with :meth:`free_id` when no longer needed.

    :param seed: True for seed ID, otherwise False
    :type seed: bool
    :returns: The ITC ID handle
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_id_pp_handle()

    if seed:
        _handle_c_return_status(_lib.ITC_Id_newSeed(pp_handle))
    else:
        _handle_c_return_status(_lib.ITC_Id_newNull(pp_handle))

    return pp_handle


def free_id(pp_handle: CTypesData) -> None:
    """Free an ITC ID.

    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    try:
        _handle_c_return_status(_lib.ITC_Id_destroy(pp_handle))
    finally:
        # Sanitise the pointers
        pp_handle[0] = _ffi.NULL
        pp_handle = _ffi.NULL


def clone_id(pp_handle: CTypesData) -> CTypesData:
    """Clone (copy) an ITC ID.

    The cloned ID must be deallocated with :meth:`free_id` when no longer needed.

    :param pp_handle: The handle of the source ID
    :type pp_handle: CTypesData
    :returns: The handle of the cloned ITC ID
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_cloned_handle = _new_id_pp_handle()
    _handle_c_return_status(_lib.ITC_Id_clone(pp_handle[0], pp_cloned_handle))
    return pp_cloned_handle


def split_id(pp_handle: CTypesData) -> CTypesData:
    """Split an ITC ID into two non-overlapping (distinct) intervals.

    Both IDs must be deallocated with :meth:`free_id` when no longer needed.

    :param pp_handle: The handle of the source ID.
        This handle will be modified in place and become the first half of the
        split ID
    :type pp_handle: CTypesData
    :returns: The handle of the other half of the split ITC ID
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_other_handle = _new_id_pp_handle()

    try:
        _handle_c_return_status(_lib.ITC_Id_split(pp_handle, pp_other_handle))
    except Exception:  # pragma: no cover
        # The other handle cannot be returned. Destroy it
        if is_handle_valid(pp_other_handle):
            free_id(pp_other_handle)

        raise

    return pp_other_handle


def sum_id(pp_handle: CTypesData, pp_other_handle: CTypesData) -> None:
    """Sum two ITC ID intervals.

    The summed ID must be deallocated with :meth:`free_id` when no longer needed.

    :param pp_handle: The handle of the first source ID
        This handle will be modified in place and become the summed ID
    :type pp_handle: CTypesData
    :param pp_other_handle: The handle of the second source ID.
        This handle will be deallocated
    :type pp_other_handle: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    _handle_c_return_status(_lib.ITC_Id_sum(pp_handle, pp_other_handle))


def serialise_id(pp_handle: CTypesData) -> bytes:
    """Serialise the given ITC ID.

    :returns: The buffer with the serialised ID
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    return _call_serialisation_func(_lib.ITC_SerDes_serialiseId, pp_handle)


def serialise_id_to_string(pp_handle: CTypesData) -> bytes:
    """Serialise the given ITC ID to ASCII string.

    :returns: The buffer with the serialised ID
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    return _call_serialisation_func(_lib.ITC_SerDes_serialiseIdToString, pp_handle)


def deserialise_id(buffer: bytes | bytearray) -> CTypesData:
    """Deserialise an ITC ID.

    The deserialised ID must be deallocated with :meth:`free_id` when no longer needed.

    :param buffer: The buffer containing the serialised ID
    :type buffer: Union[bytes, bytearray]
    :returns: The handle to the deserialised ID
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    return _call_deserialisation_func(
        _new_id_pp_handle, _lib.ITC_SerDes_deserialiseId, buffer
    )


def is_id_valid(pp_handle: CTypesData) -> bool:
    """Check whether the given ITC ID is valid.

    :param pp_handle: The handle of the ID to validate
    :type pp_handle: CTypesData
    :returns: True if the ID is valid, False otherwise
    :rtype: bool
    """
    is_valid = False

    if is_handle_valid(pp_handle):
        is_valid = _lib.ITC_Id_validate(pp_handle[0]) == ItcStatus.SUCCESS

    return is_valid


def new_event() -> CTypesData:
    """Allocate a new ITC Event.

    The Event must be deallocated with :meth:`free_event` when no longer needed.

    :returns: The ITC Event handle
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_event_pp_handle()
    _handle_c_return_status(_lib.ITC_Event_new(pp_handle))
    return pp_handle


def free_event(pp_handle: CTypesData) -> None:
    """Free an ITC Event.

    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    try:
        _handle_c_return_status(_lib.ITC_Event_destroy(pp_handle))
    finally:
        # Sanitise the pointers
        pp_handle[0] = _ffi.NULL
        pp_handle = _ffi.NULL


def clone_event(pp_handle: CTypesData) -> CTypesData:
    """Clone (copy) an ITC Event.

    The cloned Event must be deallocated with :meth:`free_event` when no longer needed.

    :param pp_handle: The handle of the source Event
    :type pp_handle: CTypesData
    :returns: The handle of the cloned ITC Event
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_cloned_handle = _new_event_pp_handle()
    _handle_c_return_status(_lib.ITC_Event_clone(pp_handle[0], pp_cloned_handle))
    return pp_cloned_handle


def serialise_event(pp_handle: CTypesData) -> bytes:
    """Serialise the given ITC Event.

    :returns: The buffer with the serialised Event
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    return _call_serialisation_func(_lib.ITC_SerDes_serialiseEvent, pp_handle)


def serialise_event_to_string(pp_handle: CTypesData) -> bytes:
    """Serialise the given ITC Event to ASCII string.

    :returns: The buffer with the serialised Event
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    return _call_serialisation_func(
        _lib.ITC_SerDes_serialiseEventToString, pp_handle, initial_array_size=128
    )


def deserialise_event(buffer: bytes | bytearray) -> CTypesData:
    """Deerialise an ITC Event.

    The deserialised ID must be deallocated with :meth:`free_id` when no longer needed.

    :param buffer: The buffer containing the serialised Event
    :type buffer: Union[bytes, bytearray]
    :returns: The handle to the deserialised Event
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    return _call_deserialisation_func(
        _new_event_pp_handle, _lib.ITC_SerDes_deserialiseEvent, buffer
    )


def is_event_valid(pp_handle: CTypesData) -> bool:
    """Check whether the given ITC Event is valid.

    :param pp_handle: The handle of the Event to validate
    :type pp_handle: CTypesData
    :returns: True if the Event is valid, False otherwise
    :rtype: bool
    """
    is_valid = False

    if is_handle_valid(pp_handle):
        is_valid = _lib.ITC_Event_validate(pp_handle[0]) == ItcStatus.SUCCESS

    return is_valid


def new_stamp() -> CTypesData:
    """Allocate a new ITC seed Stamp.

    The Stamp must be deallocated with :meth:`free_stamp` when no longer needed.

    :returns: The ITC seed Stamp handle
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_stamp_pp_handle()
    _handle_c_return_status(_lib.ITC_Stamp_newSeed(pp_handle))
    return pp_handle


def new_stamp_from_id(pp_id_handle: CTypesData) -> CTypesData:
    """Allocate a new ITC seed Stamp from an existing ID.

    The Stamp must be deallocated with :meth:`free_stamp` when no longer needed.

    :param pp_id_handle: The handle of the ID
    :type pp_id_handle: CTypesData
    :returns: The ITC seed Stamp handle
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_stamp_pp_handle()
    _handle_c_return_status(_lib.ITC_Stamp_newFromId(pp_id_handle[0], pp_handle))
    return pp_handle


def new_stamp_from_id_and_event(
    pp_id_handle: CTypesData, pp_event_handle: CTypesData
) -> CTypesData:
    """Allocate a new ITC seed Stamp from an existing ID and Event.

    The Stamp must be deallocated with :meth:`free_stamp` when no longer needed.

    :param pp_id_handle: The handle of the ID
    :type pp_id_handle: CTypesData
    :param pp_event_handle: The handle of the Event
    :type pp_event_handle: CTypesData
    :returns: The ITC seed Stamp handle
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_stamp_pp_handle()
    _handle_c_return_status(
        _lib.ITC_Stamp_newFromIdAndEvent(pp_id_handle[0], pp_event_handle[0], pp_handle)
    )
    return pp_handle


def new_peek_stamp(pp_src_handle: CTypesData) -> CTypesData:
    """Allocate a new ITC peek Stamp from a regular Stamp.

    The Stamp must be deallocated with :meth:`free_stamp` when no longer needed.

    :param pp_src_handle: The handle of the source Stamp, which Event component will
        be cloned. The source Stamp will remain unmodified.
    :type pp_src_handle: CTypesData
    :returns: The ITC peek Stamp handle
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_stamp_pp_handle()
    _handle_c_return_status(_lib.ITC_Stamp_newPeek(pp_src_handle[0], pp_handle))
    return pp_handle


def free_stamp(pp_handle: CTypesData) -> None:
    """Free an ITC Stamp.

    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    try:
        _handle_c_return_status(_lib.ITC_Stamp_destroy(pp_handle))
    finally:
        # Sanitise the pointers
        pp_handle[0] = _ffi.NULL
        pp_handle = _ffi.NULL


def clone_stamp(pp_handle: CTypesData) -> CTypesData:
    """Clone (copy) an ITC Stamp.

    The cloned Stamp must be deallocated with :meth:`free_stamp` when no longer needed.

    :param pp_handle: The handle of the source Stamp
    :type pp_handle: CTypesData
    :returns: The handle of the cloned ITC Stamp
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_cloned_handle = _new_stamp_pp_handle()
    _handle_c_return_status(_lib.ITC_Stamp_clone(pp_handle[0], pp_cloned_handle))
    return pp_cloned_handle


def fork_stamp(pp_handle: CTypesData) -> CTypesData:
    """Fork (split) an ITC Stamp into two non-overlapping (distinct) intervals.

    Both Stamps must be deallocated with :meth:`free_stamp` when no longer needed.

    :param pp_handle: The handle of the source Stamp.
        This handle will be modified in place and become the first half of the
        forked Stamp
    :type pp_handle: CTypesData
    :returns: The handle of the other half of the forked ITC Stamp
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_other_handle = _new_stamp_pp_handle()

    try:
        _handle_c_return_status(_lib.ITC_Stamp_fork(pp_handle, pp_other_handle))
    except Exception:  # pragma: no cover
        # The other handle cannot be returned. Destroy it
        if is_handle_valid(pp_other_handle):
            free_stamp(pp_other_handle)

        raise

    return pp_other_handle


def inflate_stamp(pp_handle: CTypesData) -> None:
    """Add an Event (inflate) the given ITC Stamp.

    :param pp_handle: The handle of the source Stamp. The Stamp will be modified
        in place.
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    _handle_c_return_status(_lib.ITC_Stamp_event(pp_handle[0]))


def join_stamp(pp_handle: CTypesData, pp_other_handle: CTypesData) -> None:
    """Join two ITC Stamp, merging their ID intervals and causal history.

    The joined Stamp must be deallocated with :meth:`free_stamp` when no longer needed.

    :param pp_handle: The handle of the first source Stamp
        This handle will be modified in place and become the joined Stamp
    :type pp_handle: CTypesData
    :param pp_other_handle: The handle of the second source Stamp.
        This handle will be deallocated
    :type pp_other_handle: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    _handle_c_return_status(_lib.ITC_Stamp_join(pp_handle, pp_other_handle))


def compare_stamps(
    pp_handle: CTypesData, pp_other_handle: CTypesData
) -> StampComparisonResult:
    """Compare two Stamps.

    :param pp_handle: The handle of the first source Stamp
    :type pp_handle: CTypesData
    :param pp_other_handle: The handle of the second source Stamp.
    :type pp_other_handle: CTypesData
    :returns: The result of the comparsion `pp_handle <> pp_other_handle`.
        I.e if `pp_handle < pp_other_handle`, then `StampComparisonResult.LESS_THAN`
        is returned.
    :rtype: StampComparisonResult
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    p_comparison_result = _ffi.new("ITC_Stamp_Comparison_t *")

    _handle_c_return_status(
        _lib.ITC_Stamp_compare(pp_handle[0], pp_other_handle[0], p_comparison_result)
    )

    return StampComparisonResult(p_comparison_result[0])


def serialise_stamp(pp_handle: CTypesData) -> bytes:
    """Serialise the given ITC Stamp.

    :returns: The buffer with the serialised Stamp
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    return _call_serialisation_func(
        _lib.ITC_SerDes_serialiseStamp,
        pp_handle,
    )


def serialise_stamp_to_string(pp_handle: CTypesData) -> bytes:
    """Serialise the given ITC Stamp to ASCII string.

    :returns: The buffer with the serialised Stamp
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    return _call_serialisation_func(
        _lib.ITC_SerDes_serialiseStampToString, pp_handle, initial_array_size=128
    )


def deserialise_stamp(buffer: bytes | bytearray) -> CTypesData:
    """Deserialise an ITC Stamp.

    The deserialised Stamp must be deallocated with :meth:`free_stamp` when
    no longer needed.

    :param buffer: The buffer containing the serialised Stamp
    :type buffer: Union[bytes, bytearray]
    :returns: The handle to the deserialised Stamp
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    return _call_deserialisation_func(
        _new_stamp_pp_handle, _lib.ITC_SerDes_deserialiseStamp, buffer
    )


def is_stamp_valid(pp_handle: CTypesData) -> bool:
    """Check whether the given ITC Stamp is valid.

    :param pp_handle: The handle of the Stamp to validate
    :type pp_handle: CTypesData
    :returns: True if the Stamp is valid, False otherwise
    :rtype: bool
    """
    is_valid = False

    if is_handle_valid(pp_handle):
        is_valid = _lib.ITC_Stamp_validate(pp_handle[0]) == ItcStatus.SUCCESS

    return is_valid


def get_id_component_of_stamp(pp_handle: CTypesData) -> CTypesData:
    """Get a copy of the ID component of a Stamp.

    :param pp_handle: The handle of the source Stamp.
    :type pp_handle: CTypesData
    :returns: The handle of the ID
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_id_handle = _new_id_pp_handle()
    _handle_c_return_status(_lib.ITC_Stamp_getId(pp_handle[0], pp_id_handle))
    return pp_id_handle


def set_id_copmponent_of_stamp(
    pp_stamp_handle: CTypesData, pp_id_handle: CTypesData
) -> None:
    """Set the ID component of a Stamp.

    :param pp_handle: The handle of the Stamp.
    :type pp_handle: CTypesData
    :param pp_id_handle: The new ID component handle. A copy of it will be set
    as the new ID component of the Stamp.
    :type pp_id_handle: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    _handle_c_return_status(_lib.ITC_Stamp_setId(pp_stamp_handle[0], pp_id_handle[0]))


def get_event_component_of_stamp(pp_handle: CTypesData) -> CTypesData:
    """Get a copy of the Event component of a Stamp.

    :param pp_handle: The handle of the source Stamp.
    :type pp_handle: CTypesData
    :returns: The handle of the Event
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_event_handle = _new_event_pp_handle()
    _handle_c_return_status(_lib.ITC_Stamp_getEvent(pp_handle[0], pp_event_handle))
    return pp_event_handle


def set_event_copmponent_of_stamp(
    pp_stamp_handle: CTypesData, pp_event_handle: CTypesData
) -> None:
    """Set the Event component of a Stamp.

    :param pp_handle: The handle of the Stamp.
    :type pp_handle: CTypesData
    :param pp_event_handle: The new Event component handle. A copy of it will be
    set as the new Event component of the Stamp.
    :type pp_event_handle: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    _handle_c_return_status(
        _lib.ITC_Stamp_setEvent(pp_stamp_handle[0], pp_event_handle[0])
    )

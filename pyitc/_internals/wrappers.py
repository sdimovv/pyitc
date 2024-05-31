from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Union

from cffi.backend_ctypes import CTypesData

from ..exceptions import ItcCApiError, ItcStatus, UnkownError
from . import _ffi, _lib


class StampComparisonResult(IntEnum):
    """The ITC Stamp comparison result returned from the C API"""
    LESS_THAN = _lib.ITC_STAMP_COMPARISON_LESS_THAN
    GREATER_THAN = _lib.ITC_STAMP_COMPARISON_GREATER_THAN
    EQUAL = _lib.ITC_STAMP_COMPARISON_EQUAL
    CONCURRENT = _lib.ITC_STAMP_COMPARISON_CONCURRENT

class ItcWrapper(ABC):
    """The base class of an ITC ID, Event or Stamp"""

    @abstractmethod
    def clone(self) -> "ItcWrapper":
        """Deep clone object"""
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """Check the object is in a valid state"""
        pass

    @abstractmethod
    def serialise(self) -> bytes:
        """Serialise the ID/Event/Stamp"""
        pass

    @classmethod
    @abstractmethod
    def deserialise(cls, buffer: Union[bytes, bytearray]) -> "ItcWrapper":
        """Deserialise an ID/Event/Stamp"""
        pass

    @abstractmethod
    def _new_c_type(self) -> CTypesData:
        """Allocate a new ITC/Event/Stamp"""
        pass

    @abstractmethod
    def _del_c_type(self, c_type) -> None:
        """Free the ITC/Event/Stamp stored in `self._c_type`"""
        pass

    def __init__(self) -> None:
        """Initialise a new ITC ID/Event/Stamp"""
        super().__init__()
        self.__internal_c_type: CTypesData = self._new_c_type()

    def __del__(self) -> None:
        """Deallocate the object"""
        del self._c_type

    @property
    def _c_type(self) -> CTypesData:
        """Get the underlying CFFI cdata object"""
        return self.__internal_c_type

    @_c_type.deleter
    def _c_type(self) -> None:
        """Delete the underlying CFFI cdata object"""
        if is_handle_valid(self.__internal_c_type):
            self._del_c_type(self.__internal_c_type)

    @_c_type.setter
    def _c_type(self, c_type) -> None:
        """Set the underlying CFFI cdata object"""
        del self._c_type
        self.__internal_c_type = c_type


def _handle_c_return_status(status: Union[int, ItcStatus]) -> None:
    """Checks the given status an raises the appropriate :class:`ItcCApiError`"""
    if status == ItcStatus.SUCCESS:
        return

    exc_candidates = [x for x in ItcCApiError.__subclasses__() if x.STATUS == status]

    if not exc_candidates:
        raise UnkownError(status)

    raise exc_candidates[0]()

def _new_id_pp_handle() -> CTypesData:
    """Allocate a new ITC ID handle

    This handle will be automatically freed when no longer referenced.
    """
    return _ffi.new("ITC_Id_t **")

def _new_event_pp_handle() -> CTypesData:
    """Allocate a new ITC Event handle

    This handle will be automatically freed when no longer referenced.
    """
    return _ffi.new("ITC_Event_t **")

def _new_stamp_pp_handle() -> CTypesData:
    """Allocate a new ITC Stamp handle

    This handle will be automatically freed when no longer referenced.
    """
    return _ffi.new("ITC_Stamp_t **")


def is_handle_valid(pp_handle) -> bool:
    """Validate an ID/Event/Stamp handle

    :param pp_handle: The handle to validate
    :type pp_handle: CTypesData
    :returns: True if valid, otherwise False
    :rtype: CTypesData
    """
    return pp_handle and pp_handle != _ffi.NULL and pp_handle[0] != _ffi.NULL

def new_id(seed: bool) -> CTypesData:
    """Allocate a new ITC ID

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

def free_id(pp_handle) -> None:
    """Free an ITC ID

    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    try:
        _handle_c_return_status(_lib.ITC_Id_destroy(pp_handle))
    finally:
        # Sanitise the pointers
        pp_handle[0] = _ffi.NULL
        pp_handle = _ffi.NULL

def clone_id(pp_handle: CTypesData) -> CTypesData:
    """Clone (copy) an ITC ID

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
    """Split an ITC ID into two non-overlapping (distinct) intervals

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
    except Exception:
        # The other handle cannot be returned. Destroy it
        if is_handle_valid(pp_other_handle):
            free_id(pp_other_handle)

        raise

    return pp_other_handle

def sum_id(pp_handle: CTypesData, pp_other_handle: CTypesData) -> None:
    """Sum two ITC ID intervals

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
    """Serialise the given ITC ID

    :returns: The buffer with the serialised ID
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    array_size = 64
    array: bytearray
    p_c_buffer_size = _ffi.new("uint32_t *")

    status = ItcStatus.INSUFFICIENT_RESOURCES
    while status == ItcStatus.INSUFFICIENT_RESOURCES:
        array = bytearray(array_size)
        c_buffer = _ffi.from_buffer("uint8_t[]", array, require_writable=True)
        p_c_buffer_size[0] = len(c_buffer)
        status = _lib.ITC_SerDes_serialiseId(pp_handle[0], c_buffer, p_c_buffer_size)
        # If the call fails with insufficient resources, try again with a
        # bigger buffer
        array_size *= 2

    _handle_c_return_status(status)

    return bytes(array[:p_c_buffer_size[0]])

def deserialise_id(buffer: Union[bytes, bytearray]) -> CTypesData:
    """Deserialise an ITC ID

    The deserialised ID must be deallocated with :meth:`free_id` when no longer needed.

    :param buffer: The buffer containing the serialised ID
    :type buffer: Union[bytes, bytearray]
    :returns: The handle to the deserialised ID
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_id_pp_handle()
    c_buffer = _ffi.from_buffer("uint8_t[]", buffer, require_writable=False)
    c_buffer_size = len(c_buffer)
    _handle_c_return_status(
        _lib.ITC_SerDes_deserialiseId(c_buffer, c_buffer_size, pp_handle))
    return pp_handle

def is_id_valid(pp_handle: CTypesData) -> bool:
    """Check whether the given ITC ID is valid

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
    """Allocate a new ITC Event

    The Event must be deallocated with :meth:`free_event` when no longer needed.

    :returns: The ITC Event handle
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_event_pp_handle()
    _handle_c_return_status(_lib.ITC_Event_new(pp_handle))
    return pp_handle

def free_event(pp_handle) -> None:
    """Free an ITC Event

    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    try:
        _handle_c_return_status(_lib.ITC_Event_destroy(pp_handle))
    finally:
        # Sanitise the pointers
        pp_handle[0] = _ffi.NULL
        pp_handle = _ffi.NULL

def clone_event(pp_handle: CTypesData) -> CTypesData:
    """Clone (copy) an ITC Event

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
    """Serialise the given ITC Event

    :returns: The buffer with the serialised Event
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    array_size = 64
    array: bytearray
    p_c_buffer_size = _ffi.new("uint32_t *")

    status = ItcStatus.INSUFFICIENT_RESOURCES
    while status == ItcStatus.INSUFFICIENT_RESOURCES:
        array = bytearray(array_size)
        c_buffer = _ffi.from_buffer("uint8_t[]", array, require_writable=True)
        p_c_buffer_size[0] = len(c_buffer)
        status = _lib.ITC_SerDes_serialiseEvent(pp_handle[0], c_buffer, p_c_buffer_size)
        # If the call fails with insufficient resources, try again with a
        # bigger buffer
        array_size *= 2

    _handle_c_return_status(status)

    return bytes(array[:p_c_buffer_size[0]])

def deserialise_event(buffer: Union[bytes, bytearray]) -> CTypesData:
    """Deerialise an ITC Event

    The deserialised ID must be deallocated with :meth:`free_id` when no longer needed.

    :param buffer: The buffer containing the serialised Event
    :type buffer: Union[bytes, bytearray]
    :returns: The handle to the deserialised Event
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_event_pp_handle()
    c_buffer = _ffi.from_buffer("uint8_t[]", buffer, require_writable=False)
    c_buffer_size = len(c_buffer)
    _handle_c_return_status(
        _lib.ITC_SerDes_deserialiseEvent(c_buffer, c_buffer_size, pp_handle))
    return pp_handle

def is_event_valid(pp_handle: CTypesData) -> bool:
    """Check whether the given ITC Event is valid

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
    """Allocate a new ITC seed Stamp

    The Stamp must be deallocated with :meth:`free_stamp` when no longer needed.

    :returns: The ITC seed Stamp handle
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_stamp_pp_handle()
    _handle_c_return_status(_lib.ITC_Stamp_newSeed(pp_handle))
    return pp_handle

def new_peek_stamp(pp_src_handle: CTypesData) -> CTypesData:
    """Allocate a new ITC peek Stamp from a regular Stamp

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

def free_stamp(pp_handle) -> None:
    """Free an ITC Stamp

    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    try:
        _handle_c_return_status(_lib.ITC_Stamp_destroy(pp_handle))
    finally:
        # Sanitise the pointers
        pp_handle[0] = _ffi.NULL
        pp_handle = _ffi.NULL

def clone_stamp(pp_handle: CTypesData) -> CTypesData:
    """Clone (copy) an ITC Stamp

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
    """Fork (split) an ITC Stamp into two non-overlapping (distinct) intervals

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
    except Exception:
        # The other handle cannot be returned. Destroy it
        if is_handle_valid(pp_other_handle):
            free_stamp(pp_other_handle)

        raise

    return pp_other_handle

def inflate_stamp(pp_handle: CTypesData) -> None:
    """Add an Event (inflate) the given ITC Stamp

    :param pp_handle: The handle of the source Stamp. The Stamp will be modified
        in place.
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    _handle_c_return_status(_lib.ITC_Stamp_event(pp_handle[0]))

def join_stamp(pp_handle: CTypesData, pp_other_handle: CTypesData) -> None:
    """Join two ITC Stamp, merging their ID intervals and causal history

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

def compare_stamps(pp_handle: CTypesData, pp_other_handle: CTypesData) -> StampComparisonResult:
    """Compare two Stamps

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
        _lib.ITC_Stamp_compare(
            pp_handle[0],
            pp_other_handle[0],
            p_comparison_result
        )
    )

    return StampComparisonResult(p_comparison_result[0])

def serialise_stamp(pp_handle: CTypesData) -> bytes:
    """Serialise the given ITC Stamp

    :returns: The buffer with the serialised Stamp
    :rtype: bytes
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    array_size = 64
    array: bytearray
    p_c_buffer_size = _ffi.new("uint32_t *")

    status = ItcStatus.INSUFFICIENT_RESOURCES
    while status == ItcStatus.INSUFFICIENT_RESOURCES:
        array = bytearray(array_size)
        c_buffer = _ffi.from_buffer("uint8_t[]", array, require_writable=True)
        p_c_buffer_size[0] = len(c_buffer)
        status = _lib.ITC_SerDes_serialiseStamp(pp_handle[0], c_buffer, p_c_buffer_size)
        # If the call fails with insufficient resources, try again with a
        # bigger buffer
        array_size *= 2

    _handle_c_return_status(status)

    return bytes(array[:p_c_buffer_size[0]])

def deserialise_stamp(buffer: Union[bytes, bytearray]) -> CTypesData:
    """Deserialise an ITC Stamp

    The deserialised Stamp must be deallocated with :meth:`free_stamp` when no longer needed.

    :param buffer: The buffer containing the serialised Stamp
    :type buffer: Union[bytes, bytearray]
    :returns: The handle to the deserialised Stamp
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_handle = _new_stamp_pp_handle()
    c_buffer = _ffi.from_buffer("uint8_t[]", buffer, require_writable=False)
    c_buffer_size = len(c_buffer)
    _handle_c_return_status(
        _lib.ITC_SerDes_deserialiseStamp(c_buffer, c_buffer_size, pp_handle))
    return pp_handle

def is_stamp_valid(pp_handle: CTypesData) -> bool:
    """Check whether the given ITC Stamp is valid

    :param pp_handle: The handle of the Stamp to validate
    :type pp_handle: CTypesData
    :returns: True if the Stamp is valid, False otherwise
    :rtype: bool
    """
    is_valid = False

    if is_handle_valid(pp_handle):
        is_valid = _lib.ITC_Stamp_validate(pp_handle[0]) == ItcStatus.SUCCESS

    return is_valid

def copy_id_component_of_stamp(pp_handle: CTypesData) -> CTypesData:
    """Get a copy of the ID component of a Stamp

    :param pp_handle: The handle of the source Stamp.
    :returns: The handle of the ID
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_id_handle = _new_id_pp_handle()
    _handle_c_return_status(_lib.ITC_Stamp_getId(pp_handle[0], pp_id_handle))
    return pp_id_handle

def copy_event_component_of_stamp(pp_handle: CTypesData) -> CTypesData:
    """Get a copy of the Event component of a Stamp

    :param pp_handle: The handle of the source Stamp.
    :returns: The handle of the Event
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_event_handle = _new_event_pp_handle()
    _handle_c_return_status(_lib.ITC_Stamp_getEvent(pp_handle[0], pp_event_handle))
    return pp_event_handle

# def set_id_in_stamp(p_stamp_handle: CTypesData, p_id_handle: CTypesData) -> CTypesData:
#     """Set the ID component of a Stamp

#     :param pp_handle: The handle of the source Stamp.
#     :returns: The handle of the ID
#     :rtype: CTypesData
#     :raises ItcCApiError: If something goes wrong while inside the C API
#     """
#     pp_id_handle = _new_id_pp_handle()
#     _handle_c_return_status(_lib.ITC_Stamp_getId(pp_handle[0], pp_id_handle))
#     return pp_id_handle

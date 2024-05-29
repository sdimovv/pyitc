from abc import ABC, abstractmethod
from typing import Union

from cffi.backend_ctypes import CTypesData

from ..exceptions import ItcCApiError, ItcStatus, UnkownError
from . import _ffi, _lib


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


def is_handle_valid(pp_handle) -> bool:
    """Validate an ID/Event/Stamp handle

    :param pp_handle: The handle to validate
    :type pp_handle: CTypesData
    :returns: True if valid, otherwise False
    :rtype: CTypesData
    """
    return pp_handle and pp_handle != _ffi.NULL and pp_handle[0] != _ffi.NULL

def new_id(seed: bool = False) -> CTypesData:
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

    The ID must be deallocated with :meth:`free_id` when no longer needed.

    :param pp_handle: The handle of the source ID
    :type pp_handle: CTypesData
    :returns: The handle of the cloned ITC ID
    :rtype: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    pp_cloned_ptr = _new_id_pp_handle()
    _handle_c_return_status(_lib.ITC_Id_clone(pp_handle[0], pp_cloned_ptr))
    return pp_cloned_ptr

def split_id(pp_handle: CTypesData) -> CTypesData:
    """Split an ITC ID into two non-overlapping (distinct) intervals

    The IDs must be deallocated with :meth:`free_id` when no longer needed.

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
    """Sum two ITC IDs into one

    The ID must be deallocated with :meth:`free_id` when no longer needed.

    :param pp_handle: The handle of the first source ID
        This handle will be modified in place and become the summed ID
    :type pp_handle: CTypesData
    :param pp_other_handle: The handle of the second source ID.
        This handle will be deallocated
    :type pp_other_handle: CTypesData
    :raises ItcCApiError: If something goes wrong while inside the C API
    """
    _handle_c_return_status(_lib.ITC_Id_sum(pp_handle, pp_other_handle))

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

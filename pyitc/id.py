from abc import ABC, abstractmethod

from cffi.backend_ctypes import CTypesData

from ._internals import _wrappers
from .exceptions import InactiveIdError


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
        super().__del__()

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

class Id(ItcWrapper):
    """The Interval Tree Clock's ID"""

    def __init__(self, seed: bool = True) -> None:
        """Create a new ID"""
        self._seed = seed
        super().__init__()

    def is_valid(self) -> bool:
        """Validate the ID"""
        try:
            return _wrappers.is_id_valid(self._c_type)
        except InactiveIdError:
            return False

    def clone(self) -> "Id":
        """Clone the ID

        :raises ItcError: If something goes wrong during the cloning
        """
        cloned_c_type = _wrappers.clone_id(self._c_type)
        id = Id(seed=False)
        id._c_type = cloned_c_type
        return id

    def split(self) -> "Id":
        """Split the ID

        :raises ItcError: If something goes wrong during the split
        """
        other_c_type = _wrappers.split_id(self._c_type)
        id = Id(seed=False)
        id._c_type = other_c_type
        return id

    def sum(self, id: "Id") -> None:
        """Sum the ID

        :param id: The ID to be summed with
        :type id: Id
        :raises TypeError: If :param:`id` is not of type :class:`Id`
        :raises ValueError: If :param:`id` the IDs are of the same instance
        :raises ItcError: If something goes wrong during the sumation
        """
        if not isinstance(id, Id):
            raise TypeError(f"Expected instance of Id(), got id={type(id)}")
        if self._c_type == id._c_type:
            raise ValueError("An ID cannot be summed with itself")

        _wrappers.sum_id(self._c_type, id._c_type)

    def _new_c_type(self) -> CTypesData:
        """Create a new ITC ID. Only used during initialisation"""
        c_type = _wrappers.new_id(self._seed)
        del self._seed
        return c_type

    def _del_c_type(self, c_type) -> None:
        """Delete the underlying CFFI cdata object"""
        try:
            _wrappers.free_id(self._c_type)
        except InactiveIdError:
            pass

    @ItcWrapper._c_type.getter
    def _c_type(self) -> CTypesData:
        """Get the underlying CFFI cdata object"""
        if not _wrappers.is_handle_valid(super()._c_type):
            raise InactiveIdError()
        return super()._c_type

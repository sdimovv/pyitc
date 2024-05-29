from abc import ABC, abstractmethod

from cffi.backend_ctypes import CTypesData

from ._internals import _wrappers
from .exceptions import InactiveIdError


class ItcWrapper(ABC):

    @abstractmethod
    def clone(self) -> "ItcWrapper":
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        pass

    @abstractmethod
    def _new_c_type(self) -> CTypesData:
        pass

    @abstractmethod
    def _del_c_type(self, c_type) -> None:
        pass

    def __init__(self) -> None:
        self.__internal_c_type = self._new_c_type()

    @property
    def _c_type(self) -> CTypesData:
        return self.__internal_c_type

    @_c_type.deleter
    def _c_type(self) -> None:
        self._del_c_type(self.__internal_c_type)

    @_c_type.setter
    def _c_type(self, c_type) -> None:
        del self._c_type
        self.__internal_c_type = c_type


class Id:
    def __init__(self, seed=True) -> None:
        self.__internal_c_type = _wrappers.new_id(bool(seed))

    def __del__(self):
        del self._c_type

    @property
    def _c_type(self):
        if not _wrappers.is_handle_valid(self.__internal_c_type):
            raise InactiveIdError()

        return self.__internal_c_type

    @_c_type.setter
    def _c_type(self, c_type):
        del self._c_type
        self.__internal_c_type = c_type

    @_c_type.deleter
    def _c_type(self):
        if _wrappers.is_handle_valid(self.__internal_c_type):
            _wrappers.free_id(self.__internal_c_type)

    def clone(self) -> "Id":
        cloned_c_type = _wrappers.clone_id(self._c_type)
        id = Id(seed=False)
        id._c_type = cloned_c_type
        return id

    def split(self) -> "Id":
        other_c_type = _wrappers.split_id(self._c_type)
        id = Id(seed=False)
        id._c_type = other_c_type
        return id

    def sum(self, id: "Id") -> None:
        if not isinstance(id, Id):
            raise TypeError(f"Expected instance of Id(), got id={type(id)}")
        if self._c_type == id._c_type:
            raise ValueError("An ID cannot be summed with itself")

        _wrappers.sum_id(self._c_type, id._c_type)

    def is_valid(self) -> bool:
        try:
            return _wrappers.is_id_valid(self._c_type)
        except InactiveIdError:
            return False

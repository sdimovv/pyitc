
from cffi.backend_ctypes import CTypesData

from pyitc._internals._wrappers import ItcWrapper

from ._internals import _wrappers
from .exceptions import InactiveIdError


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

        :returns: The cloned ID
        :rtype: Id
        :raises ItcError: If something goes wrong during the cloning
        """
        cloned_c_type = _wrappers.clone_id(self._c_type)
        id = Id(seed=False)
        id._c_type = cloned_c_type
        return id

    def split(self) -> "Id":
        """Split the ID into two distinct (non-overlapping) intervals

        After splitting this ID becomes the first half of the interval.

        :returns: The second half of the split ID
        :rtype: Id
        :raises ItcError: If something goes wrong during the split
        """
        other_c_type = _wrappers.split_id(self._c_type)
        id = Id(seed=False)
        id._c_type = other_c_type
        return id

    def sum(self, other_id: "Id") -> None:
        """Sum the ID interval

        After the sumation, this ID becomes the owner of the summed interval,
        while `other_id` becomes invalid and cannot be used anymore.

        :param other_id: The ID to be summed with
        :type other_id: Id
        :raises TypeError: If :param:`id` is not of type :class:`Id`
        :raises ValueError: If :param:`id` the IDs are of the same instance
        :raises ItcError: If something goes wrong during the sumation
        """
        if not isinstance(other_id, Id):
            raise TypeError(f"Expected instance of Id(), got id={type(other_id)}")
        if self._c_type == other_id._c_type:
            raise ValueError("An ID cannot be summed with itself")

        _wrappers.sum_id(self._c_type, other_id._c_type)

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

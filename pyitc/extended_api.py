
from typing import Union

from cffi.backend_ctypes import CTypesData

from ._internals import _wrappers
from .exceptions import InactiveEventError, InactiveIdError


class Id(_wrappers.ItcWrapper):
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
        id = Id()
        id._c_type = cloned_c_type
        return id

    def serialise(self) -> bytes:
        """Serialise the ID

        :returns: A buffer with the serialised ID in it.
        :rtype: bytes
        :raises ItcError: If something goes wrong during the serialisation
        """
        return _wrappers.serialise_id(self._c_type)

    @classmethod
    def deserialise(cls, buffer: Union[bytes, bytearray]) -> "Id":
        """Deserialise an ID

        :param buffer: The buffer containing the serialised ID
        :type buffer: Union[bytes, bytearray]
        :returns: The deserialised ID
        :rtype: Id
        :raises ItcError: If something goes wrong during the deserialisation
        """
        if not isinstance(buffer, (bytes, bytearray)):
            raise TypeError(
                "Expected instance of Union[bytes, bytearray], "
                f"got buffer={type(buffer)}")

        id = Id()
        id._c_type = _wrappers.deserialise_id(bytes(buffer))
        return id

    def split(self) -> "Id":
        """Split the ID into two distinct (non-overlapping) intervals

        After splitting this ID becomes the first half of the interval.

        :returns: The second half of the split ID
        :rtype: Id
        :raises ItcError: If something goes wrong during the split
        """
        other_c_type = _wrappers.split_id(self._c_type)
        id = Id()
        id._c_type = other_c_type
        return id

    def sum(self, *other_id: "Id") -> None:
        """Sum ID interval(s)

        After the sumation, this ID becomes the owner of the summed interval(s),
        while `other_id` becomes invalid and cannot be used anymore.

        :param other_id: The ID to be summed with
        :type other_id: Id
        :raises TypeError: If :param:`other_id` is not of type :class:`Id`
        :raises ValueError: If both IDs are of the same instance
        :raises ItcError: If something goes wrong during the sumation
        """
        for id in other_id:
            if not isinstance(id, Id):
                raise TypeError(f"Expected instance of Id, got id={type(id)}")
            if self._c_type == id._c_type:
                raise ValueError("An Id cannot be joined with itself")

        for id in other_id:
            _wrappers.sum_id(self._c_type, id._c_type)

    def _new_c_type(self) -> CTypesData:
        """Create a new ITC ID. Only used during initialisation"""
        c_type = _wrappers.new_id(self._seed)
        del self._seed
        return c_type

    def _del_c_type(self, c_type) -> None:
        """Delete the underlying CFFI cdata object"""
        _wrappers.free_id(c_type)

    @_wrappers.ItcWrapper._c_type.getter
    def _c_type(self) -> CTypesData:
        """Get the underlying CFFI cdata object"""
        if not _wrappers.is_handle_valid(super()._c_type):
            raise InactiveIdError()
        return super()._c_type

class Event(_wrappers.ItcWrapper):
    """The Interval Tree Clock's Event"""

    def is_valid(self) -> bool:
        """Validate the Event"""
        try:
            return _wrappers.is_event_valid(self._c_type)
        except InactiveEventError:
            return False

    def clone(self) -> "Event":
        """Clone the Event

        :returns: The cloned Event
        :rtype: Event
        :raises ItcError: If something goes wrong during the cloning
        """
        cloned_c_type = _wrappers.clone_event(self._c_type)
        event = Event()
        event._c_type = cloned_c_type
        return event

    def serialise(self) -> bytes:
        """Serialise the Event

        :returns: A buffer with the serialised Event in it.
        :rtype: bytes
        :raises ItcError: If something goes wrong during the serialisation
        """
        return _wrappers.serialise_event(self._c_type)

    @classmethod
    def deserialise(cls, buffer: Union[bytes, bytearray]) -> "Event":
        """Deserialise an Event

        :param buffer: The buffer containing the serialised Event
        :type buffer: Union[bytes, bytearray]
        :returns: The deserialised Event
        :rtype: Event
        :raises ItcError: If something goes wrong during the deserialisation
        """
        if not isinstance(buffer, (bytes, bytearray)):
            raise TypeError(
                "Expected instance of Union[bytes, bytearray], "
                f"got buffer={type(buffer)}")

        event = Event()
        event._c_type = _wrappers.deserialise_event(bytes(buffer))
        return event

    def _new_c_type(self) -> CTypesData:
        """Create a new ITC Event. Only used during initialisation"""
        return _wrappers.new_event()

    def _del_c_type(self, c_type) -> None:
        """Delete the underlying CFFI cdata object"""
        _wrappers.free_event(c_type)

    @_wrappers.ItcWrapper._c_type.getter
    def _c_type(self) -> CTypesData:
        """Get the underlying CFFI cdata object"""
        if not _wrappers.is_handle_valid(super()._c_type):
            raise InactiveEventError()
        return super()._c_type

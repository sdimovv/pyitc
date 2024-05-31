from typing import Union

from cffi.backend_ctypes import CTypesData as _CTypesData

from . import extended_api
from ._internals import wrappers as _wrappers
from .exceptions import InactiveStampError


class Stamp(_wrappers.ItcWrapper):
    """The Interval Tree Clock's Stamp"""

    def is_valid(self) -> bool:
        """Validate the Stamp"""
        try:
            return _wrappers.is_stamp_valid(self._c_type)
        except InactiveStampError:
            return False

    def clone(self) -> "Stamp":
        """Clone the Stamp

        :returns: The cloned Stamp
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the cloning
        """
        cloned_c_type = _wrappers.clone_stamp(self._c_type)
        stamp = Stamp()
        stamp._c_type = cloned_c_type
        return stamp

    def serialise(self) -> bytes:
        """Serialise the Stamp

        :returns: A buffer with the serialised Stamp in it.
        :rtype: bytes
        :raises ItcError: If something goes wrong during the serialisation
        """
        return _wrappers.serialise_stamp(self._c_type)

    @classmethod
    def deserialise(cls, buffer: Union[bytes, bytearray]) -> "Stamp":
        """Deserialise an Stamp

        :param buffer: The buffer containing the serialised Stamp
        :type buffer: Union[bytes, bytearray]
        :returns: The deserialised Stamp
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the deserialisation
        """
        if not isinstance(buffer, (bytes, bytearray)):
            raise TypeError(
                "Expected instance of Union[bytes, bytearray], "
                f"got buffer={type(buffer)}")

        stamp = Stamp()
        stamp._c_type = _wrappers.deserialise_stamp(bytes(buffer))
        return stamp

    @property
    def id_component(self) -> extended_api.Event:
        """Get a copy of the ID component"""
        id = extended_api.Id()
        id._c_type = _wrappers.copy_id_component_of_stamp(self._c_type)
        return id

    @property
    def event_component(self) -> extended_api.Event:
        """Get a copy of the Event component"""
        event = extended_api.Event()
        event._c_type = _wrappers.copy_event_component_of_stamp(self._c_type)
        return event

    def peek(self) -> "Stamp":
        """Create a peek Stamp (Stamp with NULL ID) from the current Stamp

        :returns: The peek Stamp
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the peeking
        """
        other_c_type = _wrappers.new_peek_stamp(self._c_type)
        stamp = Stamp()
        stamp._c_type = other_c_type
        return stamp

    def fork(self) -> "Stamp":
        """Fork (split) the Stamp into two distinct (non-overlapping) intervals
        with the same causal history

        After forking this Stamp owns the first half of the forked interval.

        :returns: A Stamp that owns the second half of the forked interval
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the forking
        """
        other_c_type = _wrappers.fork_stamp(self._c_type)
        stamp = Stamp()
        stamp._c_type = other_c_type
        return stamp

    def event(self) -> None:
        """Add an event to the Stamp (inflate it)

        :raises ItcError: If something goes wrong during the inflation
        """
        _wrappers.inflate_stamp(self._c_type)

    def join(self, *other_stamp: "Stamp") -> None:
        """Join Stamp interval(s)

        After joining, this Stamp becomes the owner of the joined interval(s),
        while `other_stamp` becomes invalid and cannot be used anymore.

        :param other_stamp: The Stamp to be joined with
        :type other_stamp: Stamp
        :raises TypeError: If :param:`other_stamp` is not of type :class:`Stamp`
        :raises ValueError: If both Stamps are of the same instance
        :raises ItcError: If something goes wrong during the joining
        """
        for stamp in other_stamp:
            if not isinstance(stamp, Stamp):
                raise TypeError(
                    f"Expected instance of Stamp, got stamp={type(stamp)}")
            if self._c_type == stamp._c_type:
                raise ValueError("A Stamp cannot be joined with itself")

        for stamp in other_stamp:
            _wrappers.join_stamp(self._c_type, stamp._c_type)

    def __lt__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp):
            return NotImplemented

        return (
            _wrappers.compare_stamps(self._c_type, other._c_type) ==
                _wrappers.StampComparisonResult.LESS_THAN
        )

    def __le__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp):
            return NotImplemented

        return bool(
            _wrappers.compare_stamps(self._c_type, other._c_type) &
                (_wrappers.StampComparisonResult.GREATER_THAN |
                 _wrappers.StampComparisonResult.EQUAL)
        )

    def __gt__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp):
            return NotImplemented

        return (
            _wrappers.compare_stamps(self._c_type, other._c_type) ==
                _wrappers.StampComparisonResult.GREATER_THAN
        )

    def __ge__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp):
            return NotImplemented

        return bool(
            _wrappers.compare_stamps(self._c_type, other._c_type) &
                (_wrappers.StampComparisonResult.LESS_THAN |
                 _wrappers.StampComparisonResult.EQUAL)
        )

    def __eq__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp):
            return NotImplemented

        return (
            _wrappers.compare_stamps(self._c_type, other._c_type) ==
                _wrappers.StampComparisonResult.EQUAL
        )

    def __ne__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp):
            return NotImplemented

        return bool(
            _wrappers.compare_stamps(self._c_type, other._c_type) &
                (_wrappers.StampComparisonResult.CONCURRENT |
                  _wrappers.StampComparisonResult.LESS_THAN |
                  _wrappers.StampComparisonResult.GREATER_THAN)
        )

    def _new_c_type(self) -> _CTypesData:
        """Create a new ITC Stamp. Only used during initialisation"""
        return _wrappers.new_stamp()

    def _del_c_type(self, c_type) -> None:
        """Delete the underlying CFFI cdata object"""
        _wrappers.free_stamp(c_type)

    @_wrappers.ItcWrapper._c_type.getter
    def _c_type(self) -> _CTypesData:
        """Get the underlying CFFI cdata object"""
        if not _wrappers.is_handle_valid(super()._c_type):
            raise InactiveStampError()
        return super()._c_type

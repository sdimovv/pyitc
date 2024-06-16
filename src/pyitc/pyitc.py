from typing import Any, Optional, Union

from cffi.backend_ctypes import CTypesData as _CTypesData

from . import extended_api
from ._internals import wrappers as _wrappers
from .exceptions import InactiveStampError, ItcError


class Stamp(_wrappers.ItcWrapper):
    """The Interval Tree Clock's Stamp"""

    def __init__(
            self,
            id: Optional[extended_api.Id] = None,
            event: Optional[extended_api.Event] = None,
            **kwargs: Any) -> None:
        """Create a new Stamp"""
        if id and not isinstance(id, extended_api.Id):
            raise TypeError(
                f"Expected instance of Id, got id={type(id)}")
        if event and not isinstance(event, extended_api.Event):
            raise TypeError(
                f"Expected instance of Event, got event={type(event)}")

        self._id = id
        self._event = event
        super().__init__(**kwargs)
        del self._id
        del self._event

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
        return Stamp(_c_type=_wrappers.clone_stamp(self._c_type))

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

        return Stamp(_c_type=_wrappers.deserialise_stamp(bytes(buffer)))

    @property
    def id_component(self) -> extended_api.Id:
        """Get a copy of the ID component"""
        return extended_api.Id(
            _c_type=_wrappers.get_id_component_of_stamp(self._c_type))

    @id_component.setter
    def id_component(self, id: extended_api.Id) -> None:
        """Replace the ID component of the Stamp with a copy of the input Id"""
        if not isinstance(id, extended_api.Id):
            raise TypeError(f"Expected instance of Id, got id={type(id)}")

        _wrappers.set_id_copmponent_of_stamp(self._c_type, id._c_type)

    @property
    def event_component(self) -> extended_api.Event:
        """Get a copy of the Event component"""
        return extended_api.Event(
            _c_type=_wrappers.get_event_component_of_stamp(self._c_type))

    @event_component.setter
    def event_component(self, event: extended_api.Event) -> None:
        """Replace the Event component of the Stamp with a copy of the input Event"""
        if not isinstance(event, extended_api.Event):
            raise TypeError(
                f"Expected instance of Event, got event={type(event)}")

        _wrappers.set_event_copmponent_of_stamp(self._c_type, event._c_type)

    def peek(self) -> "Stamp":
        """Create a peek Stamp (Stamp with NULL ID) from the current Stamp

        :returns: The peek Stamp
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the peeking
        """
        return Stamp(_c_type=_wrappers.new_peek_stamp(self._c_type))

    def fork(self) -> "Stamp":
        """Fork (split) the Stamp into two distinct (non-overlapping) intervals
        with the same causal history

        After forking this Stamp owns the first half of the forked interval.

        :returns: A Stamp that owns the second half of the forked interval
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the forking
        """
        return Stamp(_c_type=_wrappers.fork_stamp(self._c_type))

    def event(self, count: int = 1) -> "Stamp":
        """Add an event to the Stamp (inflate it)

        :returns: self
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the inflation
        """
        if count < 1:
            raise ValueError("count must be >= 1")

        for _ in range(count):
            _wrappers.inflate_stamp(self._c_type)

        return self

    def join(self, *other_stamp: "Stamp") -> "Stamp":
        """Join Stamp interval(s)

        After joining, this Stamp becomes the owner of the joined interval(s),
        while `other_stamp` becomes invalid and cannot be used anymore.

        :param other_stamp: The Stamp to be joined with
        :type other_stamp: Stamp
        :returns: self
        :rtype: Stamp
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

        return self

    def __str__(self) -> str:
        """Serialise a Stamp to string"""
        try:
            return _wrappers.serialise_stamp_to_string(self._c_type) \
                .decode('ascii').rstrip('\0')
        except ItcError:
            return "???"

    def __lt__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp): # pragma: no cover
            return NotImplemented

        return (
            _wrappers.compare_stamps(self._c_type, other._c_type) ==
                _wrappers.StampComparisonResult.LESS_THAN
        )

    def __le__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp): # pragma: no cover
            return NotImplemented

        return bool(
            _wrappers.compare_stamps(self._c_type, other._c_type) &
                (_wrappers.StampComparisonResult.LESS_THAN |
                 _wrappers.StampComparisonResult.EQUAL)
        )

    def __gt__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp): # pragma: no cover
            return NotImplemented

        return (
            _wrappers.compare_stamps(self._c_type, other._c_type) ==
                _wrappers.StampComparisonResult.GREATER_THAN
        )

    def __ge__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp): # pragma: no cover
            return NotImplemented

        return bool(
            _wrappers.compare_stamps(self._c_type, other._c_type) &
                (_wrappers.StampComparisonResult.GREATER_THAN |
                 _wrappers.StampComparisonResult.EQUAL)
        )

    def __eq__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp): # pragma: no cover
            return NotImplemented

        return (
            _wrappers.compare_stamps(self._c_type, other._c_type) ==
                _wrappers.StampComparisonResult.EQUAL
        )

    def __ne__(self, other: "Stamp") -> bool:
        if not isinstance(other, Stamp): # pragma: no cover
            return NotImplemented

        return bool(
            _wrappers.compare_stamps(self._c_type, other._c_type) &
                (_wrappers.StampComparisonResult.CONCURRENT |
                  _wrappers.StampComparisonResult.LESS_THAN |
                  _wrappers.StampComparisonResult.GREATER_THAN)
        )

    def _new_c_type(self) -> _CTypesData:
        """Create a new ITC Stamp. Only used during initialisation"""
        if self._id and self._event:
            return _wrappers.new_stamp_from_id_and_event(
                self._id._c_type, self._event._c_type)

        if self._id:
            return _wrappers.new_stamp_from_id(self._id._c_type)

        if self._event:
            id = _wrappers.new_id(seed=True)
            stamp = _wrappers.new_stamp_from_id_and_event(
                id, self._event._c_type)
            _wrappers.free_id(id)
            return stamp

        return _wrappers.new_stamp()

    def _del_c_type(self, c_type: _CTypesData) -> None:
        """Delete the underlying CFFI cdata object"""
        _wrappers.free_stamp(c_type)

    @_wrappers.ItcWrapper._c_type.getter
    def _c_type(self) -> _CTypesData:
        """Get the underlying CFFI cdata object"""
        if not _wrappers.is_handle_valid(super()._c_type):
            raise InactiveStampError()
        return super()._c_type

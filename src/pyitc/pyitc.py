# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
"""The main ITC implementation."""

from __future__ import annotations

from sys import version_info
from typing import TYPE_CHECKING, Any

from . import extended_api
from ._internals import wrappers as _wrappers
from .exceptions import InactiveStampError, ItcError

if version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

if TYPE_CHECKING:  # pragma: no cover
    from cffi.backend_ctypes import (  # type: ignore[import-untyped]
        CTypesData as _CTypesData,
    )


class Stamp(_wrappers.ItcWrapper):
    """The Interval Tree Clock's Stamp."""

    def __init__(
        self: Self,
        id: extended_api.Id | None = None,  # noqa: A002
        event: extended_api.Event | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialise a Stamp, optionally with a custom Id and/or Event trees."""
        if id and not isinstance(id, extended_api.Id):
            msg = f"Expected instance of Id, got id={type(id)}"
            raise TypeError(msg)
        if event and not isinstance(event, extended_api.Event):
            msg = f"Expected instance of Event, got event={type(event)}"
            raise TypeError(msg)

        self._id = id
        self._event = event
        super().__init__(**kwargs)
        del self._id
        del self._event

    def is_valid(self: Self) -> bool:
        """Validate the Stamp."""
        try:
            return _wrappers.is_stamp_valid(self._c_type)
        except InactiveStampError:
            return False

    def clone(self: Self) -> Stamp:
        """Clone the Stamp.

        :returns: The cloned Stamp
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the cloning
        """
        return Stamp(_c_type=_wrappers.clone_stamp(self._c_type))

    def serialise(self: Self) -> bytes:
        """Serialise the Stamp.

        :returns: A buffer with the serialised Stamp in it.
        :rtype: bytes
        :raises ItcError: If something goes wrong during the serialisation
        """
        return _wrappers.serialise_stamp(self._c_type)

    @classmethod
    def deserialise(cls: type[Self], buffer: bytes | bytearray) -> Stamp:
        """Deserialise an Stamp.

        :param buffer: The buffer containing the serialised Stamp
        :type buffer: Union[bytes, bytearray]
        :returns: The deserialised Stamp
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the deserialisation
        """
        if not isinstance(buffer, (bytes, bytearray)):
            msg = (
                "Expected instance of Union[bytes, bytearray], "
                f"got buffer={type(buffer)}"
            )
            raise TypeError(msg)

        return Stamp(_c_type=_wrappers.deserialise_stamp(bytes(buffer)))

    @property
    def id_component(self: Self) -> extended_api.Id:
        """Get a copy of the ID component."""
        return extended_api.Id(
            _c_type=_wrappers.get_id_component_of_stamp(self._c_type)
        )

    @id_component.setter
    def id_component(self: Self, id_: extended_api.Id) -> None:
        """Replace the ID component of the Stamp with a copy of the input Id."""
        if not isinstance(id_, extended_api.Id):
            msg = f"Expected instance of Id, got id={type(id_)}"
            raise TypeError(msg)

        _wrappers.set_id_copmponent_of_stamp(self._c_type, id_._c_type)  # noqa: SLF001

    @property
    def event_component(self: Self) -> extended_api.Event:
        """Get a copy of the Event component."""
        return extended_api.Event(
            _c_type=_wrappers.get_event_component_of_stamp(self._c_type)
        )

    @event_component.setter
    def event_component(self: Self, event: extended_api.Event) -> None:
        """Replace the Event component of the Stamp with a copy of the input Event."""
        if not isinstance(event, extended_api.Event):
            msg = f"Expected instance of Event, got event={type(event)}"
            raise TypeError(msg)

        _wrappers.set_event_copmponent_of_stamp(self._c_type, event._c_type)  # noqa: SLF001

    def peek(self: Self) -> Stamp:
        """Create a peek Stamp (Stamp with NULL ID) from the current Stamp.

        :returns: The peek Stamp
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the peeking
        """
        return Stamp(_c_type=_wrappers.new_peek_stamp(self._c_type))

    def fork(self: Self) -> Stamp:
        """Fork the Stamp into two intervals with the same causal history.

        Fork (split) the Stamp into two distinct (non-overlapping) intervals
        with the same causal history.

        After forking this Stamp owns the first half of the forked interval.

        :returns: A Stamp that owns the second half of the forked interval
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the forking
        """
        return Stamp(_c_type=_wrappers.fork_stamp(self._c_type))

    def event(self: Self, count: int = 1) -> Self:
        """Add an event to the Stamp (inflate it).

        :returns: self
        :rtype: Stamp
        :raises ItcError: If something goes wrong during the inflation
        """
        if count < 1:
            msg = "Count must be >= 1"
            raise ValueError(msg)

        for _ in range(count):
            _wrappers.inflate_stamp(self._c_type)

        return self

    def join(self: Self, *other_stamp: Stamp) -> Self:
        """Join Stamp interval(s).

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
                msg = f"Expected instance of Stamp, got stamp={type(stamp)}"
                raise TypeError(msg)
            if self._c_type == stamp._c_type:  # noqa: SLF001
                msg = "A Stamp cannot be joined with itself"
                raise ValueError(msg)

        for stamp in other_stamp:
            _wrappers.join_stamp(self._c_type, stamp._c_type)  # noqa: SLF001

        return self

    def __str__(self: Self) -> str:
        """Serialise a Stamp to string."""
        try:
            return (
                _wrappers.serialise_stamp_to_string(self._c_type)
                .decode("ascii")
                .rstrip("\0")
            )
        except ItcError:
            return "???"

    def __lt__(self: Self, other: object) -> bool:
        """Check if the Stamp is less than or equal to another Stamp."""
        if not isinstance(other, Stamp):  # pragma: no cover
            return NotImplemented

        return (
            _wrappers.compare_stamps(self._c_type, other._c_type)
            == _wrappers.StampComparisonResult.LESS_THAN
        )

    def __le__(self: Self, other: object) -> bool:
        """Check if the Stamp is less than another Stamp."""
        if not isinstance(other, Stamp):  # pragma: no cover
            return NotImplemented

        return bool(
            _wrappers.compare_stamps(self._c_type, other._c_type)
            & (
                _wrappers.StampComparisonResult.LESS_THAN
                | _wrappers.StampComparisonResult.EQUAL
            )
        )

    def __gt__(self: Self, other: object) -> bool:
        """Check if the Stamp is greater than another Stamp."""
        if not isinstance(other, Stamp):  # pragma: no cover
            return NotImplemented

        return (
            _wrappers.compare_stamps(self._c_type, other._c_type)
            == _wrappers.StampComparisonResult.GREATER_THAN
        )

    def __ge__(self: Self, other: object) -> bool:
        """Check if the Stamp is greater than or equal to another Stamp."""
        if not isinstance(other, Stamp):  # pragma: no cover
            return NotImplemented

        return bool(
            _wrappers.compare_stamps(self._c_type, other._c_type)
            & (
                _wrappers.StampComparisonResult.GREATER_THAN
                | _wrappers.StampComparisonResult.EQUAL
            )
        )

    def __eq__(self: Self, other: object) -> bool:
        """Check if the Stamp is equal to another Stamp."""
        if not isinstance(other, Stamp):  # pragma: no cover
            return NotImplemented

        return (
            _wrappers.compare_stamps(self._c_type, other._c_type)
            == _wrappers.StampComparisonResult.EQUAL
        )

    def __ne__(self: Self, other: object) -> bool:
        """Check if the Stamp is not equal to another Stamp."""
        if not isinstance(other, Stamp):  # pragma: no cover
            return NotImplemented

        return bool(
            _wrappers.compare_stamps(self._c_type, other._c_type)
            & (
                _wrappers.StampComparisonResult.CONCURRENT
                | _wrappers.StampComparisonResult.LESS_THAN
                | _wrappers.StampComparisonResult.GREATER_THAN
            )
        )

    def _new_c_type(self: Self) -> _CTypesData:
        """Create a new ITC Stamp. Only used during initialisation."""
        if self._id and self._event:
            return _wrappers.new_stamp_from_id_and_event(
                self._id._c_type,  # noqa: SLF001
                self._event._c_type,  # noqa: SLF001
            )

        if self._id:
            return _wrappers.new_stamp_from_id(self._id._c_type)  # noqa: SLF001

        if self._event:
            id_ = _wrappers.new_id(seed=True)
            stamp = _wrappers.new_stamp_from_id_and_event(id_, self._event._c_type)  # noqa: SLF001
            _wrappers.free_id(id_)
            return stamp

        return _wrappers.new_stamp()

    def _del_c_type(self: Self, c_type: _CTypesData) -> None:
        """Delete the underlying CFFI cdata object."""
        _wrappers.free_stamp(c_type)

    @_wrappers.ItcWrapper._c_type.getter  # type: ignore[attr-defined] # noqa: SLF001
    def _c_type(self: Self) -> _CTypesData:
        """Get the underlying CFFI cdata object."""
        if not _wrappers.is_handle_valid(super()._c_type):
            raise InactiveStampError
        return super()._c_type

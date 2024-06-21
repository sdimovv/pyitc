# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
"""Extended API for more advanced use cases (not part of the original ITC spec)."""

from __future__ import annotations

from sys import version_info
from typing import TYPE_CHECKING, Any

from ._internals import wrappers as _wrappers
from .exceptions import InactiveEventError, InactiveIdError, ItcError

if version_info < (3, 11):  # pragma: no cover
    from typing_extensions import Self
else:  # pragma: no cover
    from typing import Self

if TYPE_CHECKING:  # pragma: no cover
    from cffi.backend_ctypes import (  # type: ignore[import-untyped]
        CTypesData as _CTypesData,
    )


class Id(_wrappers.ItcWrapper):
    """The Interval Tree Clock's ID."""

    def __init__(self: Self, *, seed: bool = True, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialise a seed or null ID."""
        self._seed = seed
        super().__init__(**kwargs)
        del self._seed

    def is_valid(self: Self) -> bool:
        """Validate the ID."""
        try:
            return _wrappers.is_id_valid(self._c_type)
        except InactiveIdError:
            return False

    def clone(self: Self) -> Id:
        """Clone the ID.

        :returns: The cloned ID
        :rtype: Id
        :raises ItcError: If something goes wrong during the cloning
        """
        return Id(_c_type=_wrappers.clone_id(self._c_type))

    def serialise(self: Self) -> bytes:
        """Serialise the ID.

        :returns: A buffer with the serialised ID in it.
        :rtype: bytes
        :raises ItcError: If something goes wrong during the serialisation
        """
        return _wrappers.serialise_id(self._c_type)

    @classmethod
    def deserialise(cls: type[Self], buffer: bytes | bytearray) -> Id:
        """Deserialise an ID.

        :param buffer: The buffer containing the serialised ID
        :type buffer: Union[bytes, bytearray]
        :returns: The deserialised ID
        :rtype: Id
        :raises ItcError: If something goes wrong during the deserialisation
        """
        if not isinstance(buffer, (bytes, bytearray)):
            msg = (
                "Expected instance of Union[bytes, bytearray], "
                f"got buffer={type(buffer)}"
            )
            raise TypeError(msg)

        return Id(_c_type=_wrappers.deserialise_id(bytes(buffer)))

    def split(self: Self) -> Id:
        """Split the ID into two distinct (non-overlapping) intervals.

        After splitting this ID becomes the first half of the interval.

        :returns: The second half of the split ID
        :rtype: Id
        :raises ItcError: If something goes wrong during the split
        """
        return Id(_c_type=_wrappers.split_id(self._c_type))

    def sum(self: Self, *other_id: Id) -> Self:
        """Sum ID interval(s).

        After the sumation, this ID becomes the owner of the summed interval(s),
        while `other_id` becomes invalid and cannot be used anymore.

        :param other_id: The ID to be summed with
        :type other_id: Id
        :returns: self
        :rtype: Id
        :raises TypeError: If :param:`other_id` is not of type :class:`Id`
        :raises ValueError: If both IDs are of the same instance
        :raises ItcError: If something goes wrong during the sumation
        """
        for id_ in other_id:
            if not isinstance(id_, Id):
                msg = f"Expected instance of Id, got id={type(id_)}"
                raise TypeError(msg)
            if self._c_type == id_._c_type:  # noqa: SLF001
                msg = "An Id cannot be summed with itself"
                raise ValueError(msg)

        for id_ in other_id:
            _wrappers.sum_id(self._c_type, id_._c_type)  # noqa: SLF001

        return self

    def __str__(self: Self) -> str:
        """Serialise an ID to string."""
        try:
            return (
                _wrappers.serialise_id_to_string(self._c_type)
                .decode("ascii")
                .rstrip("\0")
            )
        except ItcError:
            return "???"

    def _new_c_type(self: Self) -> _CTypesData:
        """Create a new ITC ID. Only used during initialisation."""
        return _wrappers.new_id(seed=self._seed)

    def _del_c_type(self: Self, c_type: _CTypesData) -> None:
        """Delete the underlying CFFI cdata object."""
        _wrappers.free_id(c_type)

    @_wrappers.ItcWrapper._c_type.getter  # type: ignore[attr-defined] # noqa: SLF001
    def _c_type(self: Self) -> _CTypesData:
        """Get the underlying CFFI cdata object."""
        if not _wrappers.is_handle_valid(super()._c_type):
            raise InactiveIdError
        return super()._c_type


class Event(_wrappers.ItcWrapper):
    """The Interval Tree Clock's Event."""

    def is_valid(self: Self) -> bool:
        """Validate the Event."""
        try:
            return _wrappers.is_event_valid(self._c_type)
        except InactiveEventError:
            return False

    def clone(self: Self) -> Event:
        """Clone the Event.

        :returns: The cloned Event
        :rtype: Event
        :raises ItcError: If something goes wrong during the cloning
        """
        return Event(_c_type=_wrappers.clone_event(self._c_type))

    def serialise(self: Self) -> bytes:
        """Serialise the Event.

        :returns: A buffer with the serialised Event in it.
        :rtype: bytes
        :raises ItcError: If something goes wrong during the serialisation
        """
        return _wrappers.serialise_event(self._c_type)

    @classmethod
    def deserialise(cls: type[Self], buffer: bytes | bytearray) -> Event:
        """Deserialise an Event.

        :param buffer: The buffer containing the serialised Event
        :type buffer: Union[bytes, bytearray]
        :returns: The deserialised Event
        :rtype: Event
        :raises ItcError: If something goes wrong during the deserialisation
        """
        if not isinstance(buffer, (bytes, bytearray)):
            msg = (
                "Expected instance of Union[bytes, bytearray], "
                f"got buffer={type(buffer)}"
            )
            raise TypeError(msg)

        return Event(_c_type=_wrappers.deserialise_event(bytes(buffer)))

    def __str__(self: Self) -> str:
        """Serialise an Event to string."""
        try:
            return (
                _wrappers.serialise_event_to_string(self._c_type)
                .decode("ascii")
                .rstrip("\0")
            )
        except ItcError:
            return "???"

    def _new_c_type(self: Self) -> _CTypesData:
        """Create a new ITC Event. Only used during initialisation."""
        return _wrappers.new_event()

    def _del_c_type(self: Self, c_type: _CTypesData) -> None:
        """Delete the underlying CFFI cdata object."""
        _wrappers.free_event(c_type)

    @_wrappers.ItcWrapper._c_type.getter  # type: ignore[attr-defined] # noqa: SLF001
    def _c_type(self: Self) -> _CTypesData:
        """Get the underlying CFFI cdata object."""
        if not _wrappers.is_handle_valid(super()._c_type):
            raise InactiveEventError
        return super()._c_type

# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
"""Tests for the Stamp class."""

import pytest

from pyitc import Stamp
from pyitc.exceptions import InactiveStampError, ItcStatus, OverlappingIdIntervalError
from pyitc.extended_api import Event, Id


def test_create_stamp() -> None:
    """Test creating a new Stamp."""
    assert str(Stamp()) == "{1; 0}"


def test_create_stamp_from_id() -> None:
    """Test creating a new Stamp from Id."""
    assert str(Stamp(Id(seed=False))) == "{0; 0}"
    assert str(Stamp(id=Id(seed=False))) == "{0; 0}"

    with pytest.raises(TypeError):
        Stamp(id=Event())  # type: ignore[arg-type]


def test_create_stamp_from_event() -> None:
    """Test creating a new stamp from Event."""
    assert str(Stamp(None, Event())) == "{1; 0}"
    assert str(Stamp(event=Event())) == "{1; 0}"
    assert str(Stamp(event=Stamp().event().event_component)) == "{1; 1}"

    with pytest.raises(TypeError):
        Stamp(event=Id())  # type: ignore[arg-type]


def test_create_stamp_from_id_and_event() -> None:
    """Test creating a new stamp from ID and Event."""
    assert str(Stamp(Id(seed=False), event=Stamp().event().event_component)) == "{0; 1}"

    with pytest.raises(TypeError):
        Stamp(id=Event(), event=Id())  # type: ignore[arg-type]


def test_no_temp_attributes() -> None:
    """Test temporary Stamp attributes have been cleaned up."""
    assert not hasattr(Stamp(), "_id")
    assert not hasattr(Stamp(), "_event")


def test_id_component() -> None:
    """Test operations over the ID component of a Stamp."""
    obj: Stamp = Stamp()
    id_comp: Id = obj.id_component
    assert isinstance(id_comp, Id)
    assert id_comp.is_valid()
    assert str(id_comp) == "1"

    obj.id_component = Id(seed=False)
    assert id_comp.is_valid()
    assert str(obj.id_component) == "0"

    with pytest.raises(TypeError):
        obj.id_component = Event()  # type: ignore[assignment]


def test_event_component() -> None:
    """Test operations over the Event component of a Stamp."""
    obj: Stamp = Stamp()
    event_comp: Event = obj.event_component
    assert isinstance(event_comp, Event)
    assert event_comp.is_valid()
    assert str(event_comp) == "0"

    obj.event_component = Stamp().event().event_component
    assert event_comp.is_valid()
    assert str(obj.event_component) == "1"

    with pytest.raises(TypeError):
        obj.event_component = Id()  # type: ignore[assignment]


def test_peek() -> None:
    """Test getting a peek Stamp."""
    obj: Stamp = Stamp()
    peek: Stamp = obj.peek()
    assert str(peek) == "{0; 0}"
    assert peek.is_valid()
    assert id(peek._c_type) != id(obj._c_type)  # noqa: SLF001


def test_fork() -> None:
    """Test forking a Stamp."""
    obj: Stamp = Stamp()
    obj2: Stamp = obj.fork()
    assert str(obj) == "{(1, 0); 0}"
    assert obj.is_valid()
    assert str(obj2) == "{(0, 1); 0}"
    assert obj2.is_valid()


def test_event() -> None:
    """Test inflating a Stamp."""
    obj: Stamp = Stamp()
    assert str(obj) == "{1; 0}"
    assert obj.is_valid()
    obj.event()
    assert str(obj) == "{1; 1}"
    assert obj.is_valid()
    obj.event(10)
    assert str(obj) == "{1; 11}"
    assert obj.is_valid()
    obj.event(count=1)
    assert str(obj) == "{1; 12}"
    assert obj.is_valid()

    with pytest.raises(ValueError, match=r"Count must be >= 1"):
        obj.event(0)
    with pytest.raises(ValueError, match=r"Count must be >= 1"):
        obj.event(-1)
    assert obj.is_valid()


def test_join() -> None:
    """Test joining two Stamps together."""
    obj: Stamp = Stamp()
    obj2: Stamp = obj.fork()

    obj.event()
    obj2.event()
    obj.join(obj2)

    assert not obj2.is_valid()
    assert obj.is_valid()
    assert str(obj) == "{1; 1}"
    with pytest.raises(InactiveStampError):
        obj2._c_type  # noqa: B018, SLF001

    obj2 = obj.fork()
    obj3 = obj2.fork()

    assert obj2.is_valid()
    assert obj3.is_valid()

    obj.join(obj2, obj3)
    assert not obj2.is_valid()
    assert not obj3.is_valid()
    assert obj.is_valid()
    assert str(obj) == "{1; 1}"

    obj = Stamp()
    with pytest.raises(OverlappingIdIntervalError) as exc_info:
        obj.join(Stamp())
    assert exc_info.value.status == ItcStatus.OVERLAPPING_ID_INTERVAL

    with pytest.raises(
        TypeError, match=r"Expected instance of Stamp, got stamp=<class '.*\.Event'>"
    ):
        obj.join(Event())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=r"A Stamp cannot be joined with itself"):
        obj.join(obj)


def test_comparison() -> None:
    """Test comparing Stamps."""
    obj: Stamp = Stamp()
    obj2: Stamp = obj.fork()
    assert obj == obj2
    obj2.event()
    assert obj < obj2
    assert obj <= obj2
    assert obj2 > obj
    assert obj2 >= obj
    assert obj != obj2
    obj.event()
    assert not obj == obj2  # noqa: SIM201
    assert not obj <= obj2
    assert not obj >= obj2
    assert not obj > obj2
    assert not obj < obj2
    assert obj != obj2

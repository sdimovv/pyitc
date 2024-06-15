import pytest

from pyitc.extended_api import Id, Event
from pyitc.exceptions import InactiveIdError, OverlappingIdIntervalError, ItcStatus

def test_create_seed_id() -> None:
    """Test creating a new seed ID"""
    assert str(Id()) == "1"
    assert str(Id(True)) == "1"
    assert str(Id(seed=True)) == "1"

def test_create_null_id() -> None:
    """Test creating a new null ID"""
    assert str(Id(False)) == "0"
    assert str(Id(seed=False)) == "0"

def test_no_id_temp_attributes() -> None:
    """Test temporary ID attributes have been cleaned up"""
    assert not hasattr(Id(), "_seed")

def test_split_id() -> None:
    """Test splitting an ID"""
    def _do_tests(obj, obj2) -> None:
        assert isinstance(obj2, Id)
        assert id(obj) != id(obj2)
        assert obj.is_valid()
        assert obj2.is_valid()

    obj: Id = Id(seed=True)
    obj2: Id = obj.split()
    _do_tests(obj, obj2)
    assert str(obj) == "(1, 0)"
    assert str(obj2) == "(0, 1)"

    obj: Id = Id(seed=False)
    obj2: Id = obj.split()
    _do_tests(obj, obj2)
    assert str(obj) == "0"
    assert str(obj2) == "0"

def test_sum_id() -> None:
    """Test summing an ID"""
    def _do_tests(obj, obj2) -> None:
        assert obj.is_valid()
        assert not obj2.is_valid()
        with pytest.raises(InactiveIdError):
            obj2._c_type

    obj: Id = Id(seed=True)
    obj2: Id = obj.split()
    obj.sum(obj2)
    _do_tests(obj, obj2)
    assert str(obj) == "1"

    obj2: Id = obj.split()
    obj3: Id = obj2.split()
    obj.sum(obj2, obj3)
    assert str(obj) == "1"

    obj: Id = Id(seed=False)
    obj2: Id = obj.split()
    obj.sum(obj2)
    _do_tests(obj, obj2)
    assert str(obj) == "0"

    obj: Id = Id(seed=True)
    with pytest.raises(OverlappingIdIntervalError) as exc_info:
        obj.sum(Id(seed=True))
    assert exc_info.value.status == ItcStatus.OVERLAPPING_ID_INTERVAL

    with pytest.raises(TypeError):
        obj.sum(Event())

    with pytest.raises(ValueError):
        obj.sum(obj)

def test_create_event() -> None:
    """Test creating a new Event"""
    assert str(Event()) == "0"

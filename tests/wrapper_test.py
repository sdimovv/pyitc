import pytest
from copy import deepcopy

from pyitc import Stamp
from pyitc.extended_api import Id, Event

@pytest.mark.parametrize('cls', [Id, Event, Stamp])
def test_cloning_and_deepcopy(cls) -> None:
    """Test cloning and deepcopying an ITC object"""
    def _do_checks(obj, obj_clone) -> None:
        assert isinstance(obj_clone, cls)
        assert id(obj) != id(obj_clone)
        assert id(obj._c_type) != id(obj_clone._c_type)

    obj = cls()
    _do_checks(obj, obj.clone())
    _do_checks(obj, deepcopy(obj))

@pytest.mark.parametrize('cls', [Id, Event, Stamp])
def test_is_valid(cls) -> None:
    """Test invoking the is_valid() method of an ITC object"""
    assert cls().is_valid()

@pytest.mark.parametrize('cls', [Id, Event, Stamp])
def test_str_and_repr(cls) -> None:
    """Test invoking the __str__ and __repr__ methods of an ITC object"""
    assert len(str(cls())) > 0
    repr_ = repr(cls())
    assert repr_.startswith(f"<{cls.__name__} = ")
    assert repr_.endswith(f">")

@pytest.mark.parametrize('cls', [Id, Event, Stamp])
def test_serdes(cls) -> None:
    """Test serialisation and deserialisation of an ITC object"""
    obj = cls()
    ser_data = obj.serialise()
    deserialised_obj = cls.deserialise(ser_data)
    assert isinstance(ser_data, bytes)
    assert len(ser_data) > 0
    assert isinstance(deserialised_obj, cls)
    assert str(obj) == str(deserialised_obj)

    with pytest.raises(TypeError):
        cls.deserialise([1, 2, 3])

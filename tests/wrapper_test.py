import pytest
from copy import deepcopy

from pyitc import Stamp
from pyitc.extended_api import Id, Event

@pytest.mark.parametrize('klass', [Id, Event, Stamp])
def test_cloning_and_deepcopy(klass) -> None:
    """Test cloning and deepcopying an ITC object"""
    def _do_checks(obj, obj_clone) -> None:
        assert isinstance(obj_clone, klass)
        assert id(obj) != id(obj_clone)
        assert id(obj._c_type) != id(obj_clone._c_type)

    obj = klass()
    _do_checks(obj, obj.clone())
    _do_checks(obj, deepcopy(obj))

@pytest.mark.parametrize('klass', [Id, Event, Stamp])
def test_is_valid(klass) -> None:
    """Test invoking the is_valid() method of an ITC object"""
    assert klass().is_valid()

@pytest.mark.parametrize('klass', [Id, Event, Stamp])
def test_str_and_repr(klass) -> None:
    """Test invoking the __str__ and __repr__ methods of an ITC object"""
    assert len(str(klass())) > 0
    repr_ = repr(klass())
    assert repr_.startswith(f"<{klass.__name__} = ")
    assert repr_.endswith(f">")

@pytest.mark.parametrize('klass', [Id, Event, Stamp])
def test_serdes(klass) -> None:
    """Test serialisation and deserialisation of an ITC object"""
    obj = klass()
    ser_data = obj.serialise()
    deserialised_obj = klass.deserialise(ser_data)
    assert isinstance(ser_data, bytes)
    assert len(ser_data) > 0
    assert isinstance(deserialised_obj, klass)
    assert str(obj) == str(deserialised_obj)

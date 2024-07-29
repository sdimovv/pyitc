# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
"""Tests for the ItcWrapper class."""

from __future__ import annotations

from copy import deepcopy

import pytest

from pyitc import Stamp
from pyitc.extended_api import Event, Id


@pytest.mark.parametrize("cls", [Id, Event, Stamp])
def test_cloning_and_deepcopy(cls: type[Id | Event | Stamp]) -> None:
    """Test cloning and deepcopying an ITC object."""

    def _do_checks(obj, obj_clone) -> None:  # noqa: ANN001
        assert isinstance(obj_clone, cls)
        assert id(obj) != id(obj_clone)
        assert id(obj._c_type) != id(obj_clone._c_type)  # noqa: SLF001

    obj = cls()
    _do_checks(obj, obj.clone())
    _do_checks(obj, deepcopy(obj))


@pytest.mark.parametrize("cls", [Id, Event, Stamp])
def test_is_valid(cls: type[Id | Event | Stamp]) -> None:
    """Test invoking the is_valid() method of an ITC object."""
    assert cls().is_valid()


@pytest.mark.parametrize("cls", [Id, Event, Stamp])
def test_str_and_repr(cls: type[Id | Event | Stamp]) -> None:
    """Test invoking the __str__ and __repr__ methods of an ITC object."""
    assert len(str(cls())) > 0
    repr_ = repr(cls())
    assert repr_.startswith(f"<{cls.__name__} = ")
    assert repr_.endswith(">")


@pytest.mark.parametrize("cls", [Id, Event, Stamp])
def test_serdes(cls: type[Id | Event | Stamp]) -> None:
    """Test serialisation and deserialisation of an ITC object."""
    obj = cls()
    ser_data = obj.serialise()
    deserialised_obj = cls.deserialise(ser_data)
    assert isinstance(ser_data, bytes)
    assert len(ser_data) > 0
    assert isinstance(deserialised_obj, cls)
    assert str(obj) == str(deserialised_obj)

    with pytest.raises(TypeError):
        cls.deserialise([1, 2, 3])  # type: ignore[arg-type]

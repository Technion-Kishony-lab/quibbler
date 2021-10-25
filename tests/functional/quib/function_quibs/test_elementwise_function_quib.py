from unittest import mock

import numpy as np
from pyquibbler import iquib
from pyquibbler.quib import ElementWiseFunctionQuib, Quib
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus

from ..utils import PathBuilder


def test_elementwise_function_quib_invalidation_with_flat_list():
    a = iquib([1, 2])
    b = np.add(a, 1)
    c = b[0]
    c.get_value()
    d = b[1]
    d.get_value()

    a.invalidate_and_redraw_at_path(PathBuilder(a)[0].path)

    assert c.cache_status == CacheStatus.ALL_INVALID
    assert d.cache_status == CacheStatus.ALL_VALID


def test_elementwise_function_quib_invalidation_with_broadcast_numpy_array():
    a = iquib(np.array([[1, 2]]))
    b = iquib(np.array([[1], [2]]))
    sum_ = a + b
    indices = [(0, 0), (0, 1), (1, 0), (1, 1)]
    should_be_invalidated_list = [True, False, True, False]
    quibs = [sum_[i] for i in indices]
    for quib in quibs:
        quib.get_value()

    a.invalidate_and_redraw_at_path(PathBuilder(a)[0, 0].path)

    for quib, should_be_invalidated in zip(quibs, should_be_invalidated_list):
        assert quib.cache_status == (CacheStatus.ALL_INVALID if should_be_invalidated else CacheStatus.ALL_VALID)


def test_elementwise_function_quib_does_not_request_unneeded_indices_on_get_value():
    fake_quib = mock.Mock(spec=Quib)
    fake_quib.get_value_valid_at_path.return_value = np.array([1, 2])
    fake_quib.get_shape.return_value.get_value.return_value = (2,)
    b = ElementWiseFunctionQuib.create(
        func=np.add,
        func_args=(fake_quib, 1)
    )

    result = b.get_value_valid_at_path([PathComponent(
        indexed_cls=np.ndarray,
        component=1
    )])

    assert result[1] == 3
    calls_requesting_values = [c for c in fake_quib.get_value_valid_at_path.mock_calls if c.args != (None,)]
    assert len(calls_requesting_values) == 1
    second_call = calls_requesting_values[0]
    assert isinstance(second_call.args[0][0], PathComponent)
    component = second_call.args[0][0]
    assert bool(np.array([False, True])[component.component]) is True

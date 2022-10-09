import numpy as np

from pyquibbler import iquib
from pyquibbler.cache.cache import CacheStatus
from tests.functional.utils import PathBuilder


def test_elementwise_function_quib_invalidation_with_flat_list():
    a = iquib([1, 2])
    b = np.add(a, 1)
    c = b[0]
    c.get_value()
    d = b[1]
    d.get_value()

    a.handler.invalidate_and_aggregate_redraw_at_path(PathBuilder(a)[0].path)

    assert c.cache_status == CacheStatus.ALL_INVALID
    assert d.cache_status == CacheStatus.ALL_VALID


def test_elementwise_function_quib_invalidation_with_nested_list():
    a = iquib([[1, 2], [3, 4]])
    b = np.exp2(a)
    c = b[1, 0]
    c.get_value()
    d = b[1, 1]
    d.get_value()

    a[1][0] = 10

    assert c.cache_status == CacheStatus.ALL_INVALID
    assert d.cache_status == CacheStatus.ALL_VALID


def test_elementwise_function_quib_with_quib_in_list():
    a = iquib(np.array([3, 4]))
    b = np.exp2([[1, 2], a])
    b00 = b[0, 0]
    b01 = b[0, 1]
    b10 = b[1, 0]
    b11 = b[1, 1]

    b00.get_value()
    b01.get_value()
    b10.get_value()
    b11.get_value()

    a[1] = 10

    assert b00.cache_status == CacheStatus.ALL_VALID
    assert b01.cache_status == CacheStatus.ALL_VALID
    assert b10.cache_status == CacheStatus.ALL_VALID
    assert b11.cache_status == CacheStatus.ALL_INVALID


def test_elementwise_function_quib_invalidation_with_broadcast_numpy_array():
    a = iquib(np.array([[1, 2]]))
    b = iquib(np.array([[1], [2]]))
    sum_ = a + b
    indices = [(0, 0), (0, 1), (1, 0), (1, 1)]
    should_be_invalidated_list = [True, False, True, False]
    quibs = [sum_[i] for i in indices]
    for quib in quibs:
        quib.get_value()

    a.handler.invalidate_and_aggregate_redraw_at_path(PathBuilder(a)[0, 0].path)

    for quib, should_be_invalidated in zip(quibs, should_be_invalidated_list):
        assert quib.cache_status == (CacheStatus.ALL_INVALID if should_be_invalidated else CacheStatus.ALL_VALID)

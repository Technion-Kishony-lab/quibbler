import numpy as np
import pytest

from pyquibbler import iquib, q
from pyquibbler.cache.cache import CacheStatus
from tests.functional.utils import PathBuilder

SHAPE_ONLY_FUNCTIONS_TO_TEST = [
    np.zeros_like,
    np.shape,
    len,
]

@pytest.mark.parametrize("func", SHAPE_ONLY_FUNCTIONS_TO_TEST)
def test_shape_only_function_quib_is_not_invalidated_upon_change_in_data_source_elements(func):
    a = iquib(np.arange(6).reshape(2, 3))
    b = q(func, a).setp(caching='on')
    b.get_value()

    a[:] = 7
    assert b.cache_status == CacheStatus.ALL_VALID


@pytest.mark.parametrize("func", SHAPE_ONLY_FUNCTIONS_TO_TEST)
def test_shape_only_function_quib_is_fully_invalidated_upon_change_in_data_source_shape(func):
    a = iquib(np.arange(6).reshape(2, 3))
    b = q(func, a).setp(caching='on')
    b.get_value()

    a.assign(np.arange(6).reshape(3, 2))
    assert b.cache_status == CacheStatus.ALL_INVALID


@pytest.mark.parametrize("func", SHAPE_ONLY_FUNCTIONS_TO_TEST)
def test_shape_only_function_quib_is_fully_invalidated_upon_list_extension_assignment(func):
    a = iquib([1, 2, 3])
    b = q(func, a).setp(caching='on')
    b.get_value()

    a[:] = [11, 12, 13, 14]  # list is extended
    assert b.cache_status == CacheStatus.ALL_INVALID


@pytest.mark.parametrize("func", SHAPE_ONLY_FUNCTIONS_TO_TEST)
def test_shape_only_function_quib_is_not_invalidated_upon_list_assignment(func):
    a = iquib([1, 2, 3])
    b = q(func, a).setp(caching='on')
    b.get_value()

    a[1] = 100
    assert b.cache_status == CacheStatus.ALL_VALID

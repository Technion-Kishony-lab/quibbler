import numpy as np

from pyquibbler import iquib
from pyquibbler.cache.cache import CacheStatus
from tests.functional.utils import PathBuilder


def test_shape_only_function_quib_is_not_invalidated_upon_change_in_data_source_elements():
    a = iquib(np.arange(6).reshape(2, 3))
    b = np.zeros_like(a).setp(cache_behavior='on')
    b.get_value()

    a[:] = 7
    assert b.cache_status == CacheStatus.ALL_VALID


def test_shape_only_function_quib_is_fully_invalidated_upon_change_in_data_source_shape():
    a = iquib(np.arange(6).reshape(2, 3))
    b = np.zeros_like(a).setp(cache_behavior='on')
    b.get_value()

    a.assign_value(np.arange(6).reshape(3, 2))
    assert b.cache_status == CacheStatus.ALL_INVALID

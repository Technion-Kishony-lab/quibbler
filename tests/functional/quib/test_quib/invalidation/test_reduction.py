import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.cache import CacheStatus
from tests.functional.quib.test_quib.get_value.test_apply_along_axis import parametrize_indices_to_invalidate, \
    parametrize_data, parametrize_keepdims, parametrize_where
from tests.functional.quib.test_quib.invalidation.utils import check_invalidation


@parametrize_indices_to_invalidate
@parametrize_data
@pytest.mark.parametrize('axis', [-1, (-1, 1), 0, 1, 2, (0, 2), (0, 1), None])
@parametrize_keepdims
@parametrize_where
def test_reduction_axiswise_invalidation(indices_to_invalidate, axis, keepdims, where, data):
    kwargs = dict(axis=axis)
    if keepdims is not None:
        kwargs['keepdims'] = keepdims
    if where is not None:
        kwargs['where'] = where
    check_invalidation(lambda quib: np.sum(quib, **kwargs), data, indices_to_invalidate)


@pytest.mark.regression
def test_sum_invalidation():
    z = iquib(np.array([3, 1, 2]))
    sum_z = np.sum(z).setp(cache_mode='on')
    sum_z.get_value()
    assert sum_z.cache_status == CacheStatus.ALL_VALID, "Sanity"

    z[1] = 0

    assert sum_z.cache_status == CacheStatus.ALL_INVALID

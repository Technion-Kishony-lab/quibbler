from pyquibbler.quib import PathComponent
from tests.functional.refactor.quib.test_quib.get_value.utils import check_get_value_valid_at_path
import numpy as np
import pytest


# A 3d array in which every dimension has a different size
parametrize_data = pytest.mark.parametrize('data', [np.arange(24).reshape((2, 3, 4))])
parametrize_indices_to_invalidate = pytest.mark.parametrize('indices_to_invalidate',
                                                     [-1, 0, (0, 0), (0, 1, 2), (0, ...), [True, False]])
parametrize_keepdims = pytest.mark.parametrize('keepdims', [True, False, None])
parametrize_where = pytest.mark.parametrize('where', [True, False, [[[True], [False], [True]]], None])


@parametrize_data
@pytest.mark.parametrize('axis', [0, 1, 2, -1, -2])
@pytest.mark.parametrize('func_out_dims', [0, 1, 2])
@pytest.mark.parametrize('indices_to_get_value_at', [0, (0, 0), (-1, ...)])
def test_apply_along_axis_get_value_valid_at_path(indices_to_get_value_at, axis, func_out_dims, data):
    func1d = lambda slice: np.sum(slice).reshape((1,) * func_out_dims)
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]

    check_get_value_valid_at_path(lambda quib: np.apply_along_axis(func1d, axis, quib), data, path_to_get_value_at)

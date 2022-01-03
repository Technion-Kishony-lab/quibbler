import numpy as np
import pytest

from tests.functional.refactor.quib.test_quib.get_value.test_apply_along_axis import parametrize_indices_to_invalidate, \
    parametrize_data
from tests.functional.refactor.quib.test_quib.invalidation.utils import check_invalidation


@parametrize_indices_to_invalidate
@parametrize_data
@pytest.mark.parametrize('axis', [0, 1, 2, -1, -2])
@pytest.mark.parametrize('func_out_dims', [0, 1, 2])
def test_apply_along_axis_invalidation_(indices_to_invalidate, axis, func_out_dims, data):
    func1d = lambda slice: np.sum(slice).reshape((1,) * func_out_dims)
    check_invalidation(lambda quib: np.apply_along_axis(func1d, axis, quib), data, indices_to_invalidate)


import numpy as np
import pytest

from tests.functional.refactor.quib.test_quib.get_value.test_apply_along_axis import parametrize_indices_to_invalidate, \
    parametrize_data
from tests.functional.refactor.quib.test_quib.invalidation.utils import check_invalidation


@parametrize_indices_to_invalidate
@parametrize_data
@pytest.mark.parametrize('axis', [-1, 0, 1, 2, None])
def test_accumulation_axiswise_invalidation(indices_to_invalidate, axis, data):
    check_invalidation(lambda quib: np.cumsum(quib, axis=axis), data, indices_to_invalidate)

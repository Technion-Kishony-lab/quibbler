import numpy as np
import pytest

from tests.functional.refactor.quib.test_quib.get_value.test_apply_along_axis import parametrize_indices_to_invalidate, \
    parametrize_data
from tests.functional.refactor.quib.test_quib.invalidation.utils import check_invalidation


@parametrize_indices_to_invalidate
@parametrize_data
@pytest.mark.parametrize('excluded', [{0}, set(), None])
@pytest.mark.parametrize('func', [lambda x: np.sum(x), lambda x: (np.sum(x), np.sum(x))])
def test_vectorize_invalidation(indices_to_invalidate, data, excluded, func):
    kwargs = {}
    if excluded is not None:
        kwargs['excluded'] = excluded
    check_invalidation(np.vectorize(func, **kwargs), data, indices_to_invalidate)

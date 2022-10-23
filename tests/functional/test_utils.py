from unittest import mock

import pytest
import numpy as np

from pyquibbler.utilities.decorators import ensure_only_run_once_globally
from pyquibbler.utilities.general_utils import get_shared_shape


def test_ensure_run_once_globally_runs_once():
    global_func = mock.Mock()

    wrapped_func = ensure_only_run_once_globally(global_func)
    res = wrapped_func()
    wrapped_func()

    global_func.assert_called_once()
    assert res == global_func.return_value


@pytest.mark.parametrize('shapes, expected', [
    [[(2, 3), (2, 3)], (2, 3)],
    [[(2, 3), (2, 4)], (2,)],
    [[(2, 3), ], (2, 3)],
    [[(1, 3), (2, 3)], tuple()],
    [[], tuple()],
])
def test_get_shared_shape(shapes, expected):
    assert get_shared_shape([np.zeros(shape) for shape in shapes]) == expected

import numpy as np
import pytest

from pyquibbler.quib import PathComponent
from tests.functional.refactor.quib.test_quib.get_value.test_apply_along_axis import parametrize_data
from tests.functional.refactor.quib.test_quib.get_value.utils import check_get_value_valid_at_path


@parametrize_data
@pytest.mark.parametrize('func', [lambda x: np.sum(x)])
@pytest.mark.parametrize('indices_to_get_value_at', [0, (0, 0), (-1, ...)])
def test_vectorize_get_value_valid_at_path(data, func, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(np.vectorize(func), data, path_to_get_value_at)

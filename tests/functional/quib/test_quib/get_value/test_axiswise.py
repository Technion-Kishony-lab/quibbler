import numpy as np
import pytest

from pyquibbler.path import PathComponent
from tests.functional.quib.test_quib.get_value.test_apply_along_axis import parametrize_data
from tests.functional.quib.test_quib.get_value.utils import check_get_value_valid_at_path


@parametrize_data
@pytest.mark.parametrize(['axis', 'indices_to_get_value_at'], [
    (-1, 0),
    (0, 0),
    (1, (1, 0)),
    (2, (0, 0)),
])
def test_axiswise_get_value_valid_at_path(axis, data, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(indices_to_get_value_at)]
    check_get_value_valid_at_path(lambda quib: np.sort(quib, axis=axis), data, path_to_get_value_at)

import numpy as np
from pytest import mark

from pyquibbler import iquib


@mark.parametrize(['axis', 'indices_to_invalidate', 'expected_invalidated_result_indices', 'kwargs'], [
    (0, (0, 1, 2), {(1, 2,)}, dict()),
    (1, 0, {(0, 0), (0, 1), (0, 2)}, dict()),
    (None, 0, {()}, dict()),
    ((0, 2), (0, 0), {(0,)}, dict()),
    (None, 0, {(0, 0, 0)}, dict(keepdims=True)),
    (2, (0, 1), set(), dict(where=[[[True], [False]]])),
])
def test_axiswise_invalidation(axis, indices_to_invalidate, expected_invalidated_result_indices, kwargs):
    arr = np.array([[[1, 2, 3], [4, 5, 6]]])
    data = iquib(arr)
    result = np.sum(data, axis=axis, **kwargs)
    children = {idx: result[idx] for idx in np.ndindex(result.get_shape().get_value())}

    values = {idx: child.get_value() for idx, child in children.items()}
    data[indices_to_invalidate] = 999

    invalidated_result_indices = {idx for idx, child in children.items() if not child.is_cache_valid}
    new_values = {idx: child.get_value() for idx, child in children.items()}
    changed_result_indices = {idx for idx in new_values if values[idx] != new_values[idx]}
    assert invalidated_result_indices == expected_invalidated_result_indices == changed_result_indices

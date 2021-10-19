import numpy as np
from pytest import mark

from pyquibbler import iquib

from ..utils import PathBuilder


@mark.parametrize(['axis', 'indices_to_invalidate', 'expected_invalidated_result_indices', 'kwargs'], [
    (0, (0, 1, 2), {(1, 2,)}, dict()),
    (1, 0, {(0, 0), (0, 1), (0, 2)}, dict()),
    (None, 0, {()}, dict()),
    ((0, 2), (0, 0), {(0,)}, dict()),
    (None, 0, {(0, 0, 0)}, dict(keepdims=True)),
    (2, (0, 1), set(), dict(where=[[[True], [False]]])),
])
@mark.parametrize('arr', [
    [[[1, 2, 3], [4, 5, 6]]],
    np.array([[[1, 2, 3], [4, 5, 6]]])
])
def test_axiswise_invalidation(axis, indices_to_invalidate, expected_invalidated_result_indices, arr, kwargs):
    data = iquib(arr)
    result = np.sum(data, axis=axis, **kwargs)
    children = {idx: result[idx] for idx in np.ndindex(result.get_shape().get_value())}
    for child in children.values():
        child.get_value()

    data.invalidate_and_redraw_at_path(PathBuilder(data)[indices_to_invalidate].path)

    invalidated_result_indices = {idx for idx, child in children.items() if not child.is_cache_valid}
    assert invalidated_result_indices == expected_invalidated_result_indices

import numpy as np
from pytest import mark

from pyquibbler import iquib


def check_invalidation(func, data, indices_to_invalidate):
    """
    Run func on an ndarray iquib, change the iquib in the given indices,
    and verify that the invalidated indices were also the ones that changed values.
    Make sure that func works in a way that guarantees that when a value in the input changes,
    all affected values in the result also change.
    """
    input_quib = iquib(data)
    result = func(input_quib)
    children = {idx: result[idx] for idx in np.ndindex(result.get_shape().get_value())}

    values = {idx: child.get_value() for idx, child in children.items()}
    input_quib[indices_to_invalidate] = 999

    invalidated_result_indices = {idx for idx, child in children.items() if not child.is_cache_valid}
    new_values = {idx: child.get_value() for idx, child in children.items()}
    changed_result_indices = {idx for idx in new_values if not np.array_equal(values[idx], new_values[idx])}
    assert invalidated_result_indices == changed_result_indices


# A 3d array in which every dimension has a different size
parametrize_data = mark.parametrize('data', [np.arange(24).reshape((2, 3, 4))])
parametrize_indices = mark.parametrize('indices_to_invalidate', [-1, 0, (0, 0), (0, 1, 2), (0, ...), [True, False]])


@parametrize_indices
@parametrize_data
@mark.parametrize('axis', [-1, (-1, 1), 0, 1, 2, (0, 2), (0, 1), None])
@mark.parametrize('keepdims', [True, False, None])
@mark.parametrize('where', [True, False, [[[True], [False], [True]]], None])
def test_axiswise_invalidation_with_sum(indices_to_invalidate, axis, keepdims, where, data):
    kwargs = dict(axis=axis)
    if keepdims is not None:
        kwargs['keepdims'] = keepdims
    if where is not None:
        kwargs['where'] = where
    check_invalidation(lambda iq: np.sum(iq, **kwargs), data, indices_to_invalidate)


@parametrize_indices
@parametrize_data
@mark.parametrize('axis', [0, 1, 2, -1, -2])
@mark.parametrize('func_out_dims', [0, 1, 2])
def test_axiswise_invalidation_with_apply_along_axis(indices_to_invalidate, axis, func_out_dims, data):
    func1d = lambda slice: np.sum(slice).reshape((1,) * func_out_dims)
    check_invalidation(lambda iq: np.apply_along_axis(func1d, axis, iq), data, indices_to_invalidate)


@parametrize_indices
@parametrize_data
def test_axiswise_invalidation_with_vectorize(indices_to_invalidate, data):
    check_invalidation(lambda iq: np.vectorize(lambda x: x)(iq), data, indices_to_invalidate)

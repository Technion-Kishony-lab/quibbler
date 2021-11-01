import numpy as np
from pytest import mark

from pyquibbler import CacheBehavior
from pyquibbler.quib.assignment import PathComponent

from ..utils import check_invalidation, check_get_value_valid_at_path, MockQuib

# A 3d array in which every dimension has a different size
parametrize_data = mark.parametrize('data', [np.arange(24).reshape((2, 3, 4))])
parametrize_indices_to_invalidate = mark.parametrize('indices_to_invalidate',
                                                     [-1, 0, (0, 0), (0, 1, 2), (0, ...), [True, False]])
parametrize_keepdims = mark.parametrize('keepdims', [True, False, None])
parametrize_where = mark.parametrize('where', [True, False, [[[True], [False], [True]]], None])


@parametrize_indices_to_invalidate
@parametrize_data
@mark.parametrize('axis', [-1, (-1, 1), 0, 1, 2, (0, 2), (0, 1), None])
@parametrize_keepdims
@parametrize_where
def test_reduction_axiswise_invalidation(indices_to_invalidate, axis, keepdims, where, data):
    kwargs = dict(axis=axis)
    if keepdims is not None:
        kwargs['keepdims'] = keepdims
    if where is not None:
        kwargs['where'] = where
    check_invalidation(lambda quib: np.sum(quib, **kwargs), data, indices_to_invalidate)


def test_reduction_function_gets_whole_value_of_non_data_source_parents():
    # This is also a regression to handling 0 data source quibs
    non_data = MockQuib(0)
    fquib = np.sum([1, 2, 3], axis=non_data)
    fquib.set_cache_behavior(CacheBehavior.OFF)
    with non_data.collect_valid_paths() as valid_paths:
        fquib.get_value()

    assert valid_paths == [[]]


def test_reduction_function_gets_whole_value_of_data_source_parents_when_whole_value_changed():
    data = MockQuib([1, 2, 3])
    fquib = np.sum(data)
    fquib.set_cache_behavior(CacheBehavior.OFF)
    with data.collect_valid_paths() as valid_paths:
        fquib.get_value()

    assert valid_paths == [[]]


@parametrize_data
@mark.parametrize(['axis', 'indices_to_get_value_at'], [
    (-1, 0),
    ((-1, 1), 1),
    (0, 0),
    (1, (1, 0)),
    (2, (0, 0)),
    ((0, 2), -1),
    ((0, 1), 0),
    (None, ...),
])
@parametrize_keepdims
@parametrize_where
def test_reduction_axiswise_get_value_valid_at_path(axis, data, keepdims, where, indices_to_get_value_at):
    kwargs = dict(axis=axis)
    if keepdims is not None:
        kwargs['keepdims'] = keepdims
    if where is not None:
        kwargs['where'] = where
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(lambda quib: np.sum(quib, **kwargs), data, path_to_get_value_at)


@parametrize_indices_to_invalidate
@parametrize_data
@mark.parametrize('axis', [0, 1, 2, -1, -2])
@mark.parametrize('func_out_dims', [0, 1, 2])
def test_apply_along_axis_invalidation(indices_to_invalidate, axis, func_out_dims, data):
    func1d = lambda slice: np.sum(slice).reshape((1,) * func_out_dims)
    check_invalidation(lambda quib: np.apply_along_axis(func1d, axis, quib), data, indices_to_invalidate)


@parametrize_data
@mark.parametrize('axis', [0, 1, 2, -1, -2])
@mark.parametrize('func_out_dims', [0, 1, 2])
@mark.parametrize('indices_to_get_value_at', [0, (0, 0), (-1, ...)])
def test_apply_along_axis_get_value_valid_at_path(indices_to_get_value_at, axis, func_out_dims, data):
    func1d = lambda slice: np.sum(slice).reshape((1,) * func_out_dims)
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(lambda quib: np.apply_along_axis(func1d, axis, quib), data, path_to_get_value_at)

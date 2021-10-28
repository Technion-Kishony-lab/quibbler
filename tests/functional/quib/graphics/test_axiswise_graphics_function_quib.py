import numpy as np
from pytest import mark

from pyquibbler import iquib, CacheBehavior
from pyquibbler.env import LAZY
from pyquibbler.quib.assignment import PathComponent

from ..utils import check_invalidation, check_get_value_valid_at_path, MockQuib, PathBuilder

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


@parametrize_indices_to_invalidate
@parametrize_data
@mark.parametrize('excluded', [{0}, set(), None])
@mark.parametrize('func', [lambda x: np.sum(x), lambda x: (np.sum(x), np.sum(x))])
def test_vectorize_invalidation(indices_to_invalidate, data, excluded, func):
    kwargs = {}
    if excluded is not None:
        kwargs['excluded'] = excluded
    check_invalidation(np.vectorize(func, **kwargs), data, indices_to_invalidate)


@parametrize_data
@mark.parametrize('func', [lambda x: np.sum(x)])
@mark.parametrize('indices_to_get_value_at', [0, (0, 0), (-1, ...)])
def test_vectorize_get_value_valid_at_path(data, func, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(np.vectorize(func), data, path_to_get_value_at)


def test_vectorize_get_value_valid_at_path_with_excluded_quib():
    excluded = MockQuib([1, 2, 3])
    func = np.vectorize(lambda a, b: np.array([1, 2, 3]), excluded={1}, signature='(n)->(m)')
    fquib = func([0, 1], excluded)
    fquib.set_cache_behavior(CacheBehavior.OFF)
    path = PathBuilder(fquib)[0].path

    with excluded.collect_valid_paths() as valid_paths:
        fquib.get_value_valid_at_path(path)

    assert valid_paths == [[]]


@mark.parametrize(['quib_data', 'non_quib_data'], [
    (np.zeros((2, 3)), np.zeros((4, 2, 3))),
    (np.zeros((3, 3)), np.zeros((1, 3))),
    (np.zeros((1, 3, 3)), np.zeros((4, 1, 3))),
    (np.zeros((4, 2, 3)), np.zeros((2, 3))),
])
def test_vectorize_get_value_valid_at_path_when_args_have_different_loop_dimensions(quib_data, non_quib_data):
    func = lambda quib: np.vectorize(lambda x, y: x + y)(quib, quib_data)
    check_get_value_valid_at_path(func, non_quib_data, [PathComponent(np.ndarray, 0)])


@mark.parametrize('indices_to_get_value_at', [0, (1, 1), (1, ..., 2)])
def test_vectorize_get_value_at_path_with_core_dims(indices_to_get_value_at):
    quib_data = np.zeros((2, 2, 3, 4))
    non_quib_data = np.zeros((2, 3, 4, 5))
    func = lambda a, b: np.array([np.sum(a) + np.sum(b)] * 6)
    vec = np.vectorize(func, signature='(a,b),(c)->(d)')
    check_get_value_valid_at_path(lambda quib: vec(non_quib_data, quib), quib_data,
                                  [PathComponent(np.ndarray, indices_to_get_value_at)])


def test_vectorize_invalidation_with_non_numpy_return_value():
    vec = np.vectorize(lambda a: int(np.sum(a)), signature='(a)->()')
    check_invalidation(lambda quib: vec(quib), [1, 2, 3], 0)


@parametrize_indices_to_invalidate
@parametrize_data
def test_vectorize_invalidation_with_multiple_params(data, indices_to_invalidate):
    quib_arg = iquib(np.arange(12).reshape((3, 4)))
    non_quib_arg = np.arange(8).reshape((2, 1, 4))
    quib_kwarg = iquib(3)
    non_quib_kwarg = np.arange(3).reshape((3, 1))

    vec = np.vectorize(lambda a, b, c, d, e=0: a + b + c + d + e)
    check_invalidation(lambda quib: vec(quib, quib_arg, non_quib_arg, d=quib_kwarg, e=non_quib_kwarg),
                       data, indices_to_invalidate)


@mark.parametrize('excluded', [{1}, {'b'}, set(), None])
def test_vectorize_invalidation_with_quib_as_kwarg(excluded):
    kwargs = {}
    if excluded is not None:
        kwargs['excluded'] = excluded
    vec = np.vectorize(lambda a, b: a + b)
    check_invalidation(lambda quib: vec(5, b=quib), [1, 2, 3], 0)


@parametrize_indices_to_invalidate
@parametrize_data
def test_vectorize_invalidation_with_different_core_dims(data, indices_to_invalidate):
    data2 = np.arange(100, 122).reshape(1, 22)
    func = lambda a, b: (np.array([np.sum(a) + np.sum(b)] * 4), np.sum(a) + np.sum(b))
    vec = np.vectorize(func, signature='(a,b),(c)->(d),()')
    check_invalidation(lambda quib: vec(quib, data2), data, indices_to_invalidate)


def test_vectorize_partial_calculation():
    from unittest import mock
    def func(x):
        return x

    func_mock = mock.create_autospec(func, side_effect=func)
    with LAZY.temporary_set(True):
        quib = np.vectorize(func_mock)(iquib(np.arange(3)))
    assert quib.get_value_valid_at_path(PathBuilder(quib)[0].path)[0] == 1
    # TODO: 2 is because vectorize calls first. Learn to use that call and call vectorize with otypes.
    assert func_mock.call_count == 2

def test_vectorize_get_value_valid_at_path_none():
    quib = np.vectorize(lambda x: x)(iquib([1, 2, 3]))
    value = quib.get_value_valid_at_path(None)
    assert len(value) == 3
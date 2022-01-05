import itertools

import numpy as np
import pytest
from pytest import mark

from pyquibbler import iquib
from pyquibbler.refactor.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.quib import PathComponent, Quib
from pyquibbler.quib.assignment.utils import deep_get
from tests.functional.quib.graphics.test_axiswise_graphics_function_quib import parametrize_indices_to_invalidate, \
    parametrize_data
from tests.functional.quib.utils import check_invalidation, check_get_value_valid_at_path, get_func_mock


# MOVED
@parametrize_indices_to_invalidate
@parametrize_data
@mark.parametrize('axis', [0, 1, 2, -1, -2])
@mark.parametrize('func_out_dims', [0, 1, 2])
def test_apply_along_axis_invalidation(indices_to_invalidate, axis, func_out_dims, data):
    func1d = lambda slice: np.sum(slice).reshape((1,) * func_out_dims)
    check_invalidation(lambda quib: np.apply_along_axis(func1d, axis, quib), data, indices_to_invalidate)


# MOVED
@parametrize_data
@mark.parametrize('axis', [0, 1, 2, -1, -2])
@mark.parametrize('func_out_dims', [0, 1, 2])
@mark.parametrize('indices_to_get_value_at', [0, (0, 0), (-1, ...)])
def test_apply_along_axis_get_value_valid_at_path(indices_to_get_value_at, axis, func_out_dims, data):
    func1d = lambda slice: np.sum(slice).reshape((1,) * func_out_dims)
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]

    check_get_value_valid_at_path(lambda quib: np.apply_along_axis(func1d, axis, quib), data, path_to_get_value_at)


def create_lazy_apply_along_axis_quib(func, arr, axis, args=None, kwargs=None, pass_quibs=False):
    with GRAPHICS_EVALUATE_NOW.temporary_set(True):
        return np.apply_along_axis(func, axis, iquib(arr) if not isinstance(arr, Quib) else arr,
                                   *(args or []), **(kwargs or {}), pass_quibs=pass_quibs)


# MOVED
@mark.parametrize('shape, axis, func1d_res', [
        (tuple(dimensions), axis, res)
        for shape_size in range(0, 3)
        for axis in range(-shape_size, shape_size)
        for dimensions in itertools.product(*[range(1, 4) for _ in range(shape_size)])
        for res in [1, np.arange(9).reshape((3, 3)), None]
])
@mark.parametrize('pass_quibs', [True, False])
def test_apply_along_axis_get_shape(shape, axis, func1d_res, pass_quibs):
    func = get_func_mock(lambda x: func1d_res)
    arr = np.arange(np.prod(shape)).reshape(shape)
    quib = create_lazy_apply_along_axis_quib(func=func, arr=arr, axis=axis, pass_quibs=pass_quibs)
    expected_input_arr = arr[tuple([slice(None) if i == quib.core_axis else 0 for i in range(len(arr.shape))])]

    res = quib.get_shape()

    assert func.call_count == 1
    call = func.mock_calls[0]
    oned_slice = call.args[0]
    if pass_quibs:
        assert isinstance(oned_slice, Quib)
        oned_slice = oned_slice.get_value()
    else:
        assert not isinstance(oned_slice, Quib)
    assert np.array_equal(oned_slice, expected_input_arr)
    assert res == np.apply_along_axis(func, axis=axis, arr=arr).shape


def get_sample_indexing_paths(input_shape, apply_shape, axis):
    res = np.apply_along_axis(func1d=lambda _: np.zeros(apply_shape), arr=np.zeros(input_shape), axis=axis)

    paths = [[()], []]

    if len(res.shape) > 0:
        paths.append([np.array([0 for _ in res.shape])])

    if len(res.shape) > 1:
        paths.append([(0, np.arange(res.shape[1]))])
        paths.append([(0, res.shape[1] - 1)])
    return paths


def assert_all_apply_calls_with_slices_were_relevant(func, axis, input_arr, path, applied_slices):
    whole_result = np.apply_along_axis(func, axis=axis, arr=input_arr)
    current_result = deep_get(whole_result, path)

    for slice_ in applied_slices:
        for num in np.ravel(slice_):
            new_arr = np.array(input_arr)
            new_arr[new_arr == num] = 999
            new_result = np.apply_along_axis(func, axis=axis, arr=new_arr)
            new_result_at_path = deep_get(new_result, path)
            assert not np.array_equal(new_result_at_path, current_result )


# MOVED
@mark.parametrize('input_shape, apply_result_shape, axis, components', [
        (tuple(input_dimensions), tuple(apply_dimensions), axis, components)
        for input_shape_size in range(0, 3)
        for axis in range(-input_shape_size, input_shape_size)
        for apply_result_shape_size in range(0, 3)
        for input_dimensions in itertools.product(*[range(1, 3) for _ in range(input_shape_size)])
        for apply_dimensions in [[], *itertools.product(*[range(1, 3) for _ in range(apply_result_shape_size)])]
        for components in get_sample_indexing_paths(tuple(input_dimensions), tuple(apply_dimensions), axis)
])
@mark.parametrize('pass_quibs', [True, False])
def test_apply_along_axis_get_value(input_shape, apply_result_shape, axis, components, pass_quibs):
    assert len(components) <= 1, "Sanity: No support for testing multiple components (also irrelevant)"
    slices = []
    running_in_quib = False

    def apply(oned_slice):
        if running_in_quib:
            if pass_quibs:
                assert isinstance(oned_slice, Quib)
                oned_slice = oned_slice.get_value()
            else:
                assert not isinstance(oned_slice, Quib)

            slices.append(oned_slice)
        return np.full(apply_result_shape, np.sum(oned_slice))

    func = get_func_mock(apply)
    arr = np.arange(np.prod(input_shape)).reshape(input_shape)
    quib = create_lazy_apply_along_axis_quib(arr=arr, func=func, axis=axis, pass_quibs=pass_quibs)
    quib.get_shape()  # We need to call get_shape to cache it as get_shape is a zero cost operation in overall scheme
    # and is allowed to be called without consequence by the quib
    path = [PathComponent(component=component, indexed_cls=np.ndarray) for component in components]
    running_in_quib = True

    res = quib.get_value_valid_at_path(path)

    running_in_quib = False
    whole_apply_axis_result = np.apply_along_axis(func, axis=axis, arr=arr)
    expected_result = deep_get(whole_apply_axis_result, path)
    res_at_components = deep_get(res, path)
    assert np.array_equal(res_at_components, expected_result)
    assert_all_apply_calls_with_slices_were_relevant(
        func=func,
        axis=axis,
        input_arr=arr,
        applied_slices=slices,
        path=path
    )


# MOVED
def test_apply_along_axis_returning_quib():
    res_arr = np.array([100])
    func = lambda x: iquib(res_arr)
    arr = np.array([[1]])
    axis = 0
    quib = create_lazy_apply_along_axis_quib(func=func, arr=arr, axis=axis)
    expected_res = np.apply_along_axis(lambda _: np.array([100]), arr=arr, axis=axis)

    res = quib.get_value()

    assert np.array_equal(res, expected_res)


@pytest.fixture
def mock_func_for_args_kwargs():
    return get_func_mock(lambda x, *_, **__: 1)


@pytest.fixture
def args():
    return [11, 1, 1]


@pytest.fixture
def kwargs():
    return {
        'funtimes': 1
    }


@pytest.fixture
def quib_with_args_and_kwargs(mock_func_for_args_kwargs, args, kwargs):
    return create_lazy_apply_along_axis_quib(func=mock_func_for_args_kwargs,
                                             arr=np.array([[1]]),
                                             axis=0,
                                             args=args,
                                             kwargs=kwargs)


# MOVED
def test_apply_along_axis_get_value_with_args_and_kwargs(quib_with_args_and_kwargs, mock_func_for_args_kwargs,
                                                         args, kwargs):
    quib_with_args_and_kwargs.get_value()

    mock_call = mock_func_for_args_kwargs.mock_calls[-1]
    assert mock_call.kwargs == kwargs
    assert mock_call.args[1:] == tuple(args)


# MOVED
def test_apply_along_axis_get_shape_with_args_and_kwargs(quib_with_args_and_kwargs, mock_func_for_args_kwargs,
                                                         args, kwargs):
    quib_with_args_and_kwargs.get_shape()

    assert len(mock_func_for_args_kwargs.mock_calls) == 1
    mock_call = mock_func_for_args_kwargs.mock_calls[0]
    assert mock_call.kwargs == kwargs
    assert mock_call.args[1:] == tuple(args)


# MOVED
def test_apply_along_axis_get_shape_with_looping_axis_quib():
    axis_quib = iquib(0)
    quib = create_lazy_apply_along_axis_quib(
        arr=np.array([[1]]),
        axis=axis_quib,
        func=lambda x: 1
    )

    shape = quib.get_shape()

    assert shape == (1,)


# MOVED
def test_apply_along_axis_get_shape_with_list():
    arr_quib = iquib([[1, 2], [3, 4]])
    quib = create_lazy_apply_along_axis_quib(
        arr=arr_quib,
        axis=0,
        func=lambda x: 1,
    )

    assert quib.get_shape() == (2,)


# MOVED
def test_apply_along_axis_get_shape_does_not_create_artists(mock_artists_collector):
    quib = create_lazy_apply_along_axis_quib(
        arr=np.array([[1, 2], [3, 4]]),
        axis=0,
        func=lambda x: 1
    )

    quib.get_shape()

    assert len(mock_artists_collector.mock_artists_in_axes) == 0


# MOVED
def test_apply_along_axis_removes_and_recreates_artists(mock_artists_collector):
    parent = iquib([[1, 2], [3, 4]])
    quib = create_lazy_apply_along_axis_quib(
        arr=parent,
        axis=0,
        func=lambda x: 1
    )

    quib.get_value()
    mock_artists = mock_artists_collector.mock_artists_in_axes
    parent.invalidate_and_redraw_at_path([PathComponent(component=0, indexed_cls=np.ndarray)])
    quib.get_value()

    assert len(mock_artists_collector.mock_artists_in_axes) == 2
    assert set(mock_artists_collector.mock_artists_in_axes) != set(mock_artists)


# MOVED
def test_apply_along_axis_does_not_remove_artists_that_are_not_his(mock_artists_collector):
    quib = create_lazy_apply_along_axis_quib(
        arr=np.array([[1, 2], [3, 4]]),
        axis=0,
        func=lambda x: 1
    )
    quib.get_value_valid_at_path([PathComponent(component=0, indexed_cls=np.ndarray)])
    artists = mock_artists_collector.mock_artists_in_axes
    assert len(artists) == 1, "Sanity check"

    quib.get_value_valid_at_path([PathComponent(component=1, indexed_cls=np.ndarray)])

    assert len(mock_artists_collector.mock_artists_in_axes) == 2
    assert len(set(artists) & set(mock_artists_collector.mock_artists_in_axes)) == 1


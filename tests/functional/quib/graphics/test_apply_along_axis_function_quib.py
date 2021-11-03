import itertools

import numpy as np
from pytest import mark

from pyquibbler import iquib
from pyquibbler.env import GRAPHICS_LAZY
from pyquibbler.quib import PathComponent
from tests.functional.quib.graphics.test_axiswise_graphics_function_quib import parametrize_indices_to_invalidate, \
    parametrize_data
from tests.functional.quib.utils import check_invalidation, check_get_value_valid_at_path, get_func_mock


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


@mark.parametrize('shape, axis, func1d_res', [
        (tuple(dimensions), axis, res)
        for shape_size in range(0, 3)
        for axis in range(-shape_size, shape_size)
        for dimensions in itertools.product(*[range(1, 4) for i in range(shape_size)])
        for res in [1, np.arange(9).reshape((3, 3)), None]
])
def test_apply_along_axis_only_calculates_once_with_sample_on_get_shape(shape, axis, func1d_res):
    func = get_func_mock(lambda x: func1d_res)
    arr = np.arange(np.prod(shape)).reshape(shape)
    quib = iquib(arr)
    expected_input_arr = arr[tuple([slice(None) if i == axis else 0 for i in range(len(arr.shape))])]
    with GRAPHICS_LAZY.temporary_set(True):
        quib = np.apply_along_axis(func, axis=axis, arr=quib)

    res = quib.get_shape()

    assert func.call_count == 1
    call = func.mock_calls[0]
    assert np.array_equal(call.args[0], expected_input_arr)
    assert res == np.apply_along_axis(func, axis=axis, arr=arr).shape


def test_apply_along_axis_only_calculates_once_with_sample_on_get_shape_with_ndarray():
    func = get_func_mock(lambda x: np.arange(9).reshape((3, 3)))
    arr = np.arange(8).reshape((2, 2, 2))
    quib = iquib(arr)
    with GRAPHICS_LAZY.temporary_set(True):
        quib = np.apply_along_axis(func, axis=0, arr=quib)

    res = quib.get_shape()

    assert func.call_count == 1
    call = func.mock_calls[0]
    assert np.array_equal(call.args[0], [0, 4])
    assert res == (3, 3, 2, 2)


def test_apply_along_axis_only_calculates_needed_with_returned_nd_array():
    func = get_func_mock(lambda x: np.full((3, 3), x[0]))
    arr = iquib(np.arange(8).reshape((2, 2, 2)))
    with GRAPHICS_LAZY.temporary_set(True):
        quib = np.apply_along_axis(func, axis=0, arr=arr)
    quib.get_shape()
    current_call_count = func.call_count

    # This is referencing one specific call of the function
    res = quib.get_value_valid_at_path([PathComponent(component=(0, 0, 0, 1), indexed_cls=np.ndarray)])

    assert func.call_count == current_call_count + 1
    last_call = func.mock_calls[-1]
    assert np.array_equal(last_call.args[0], [1, 5])
    assert res[0][0][0][1] == 1


def test_apply_along_axis_only_calculates_what_is_needed():
    func = get_func_mock(lambda x: 1)
    arr = iquib(np.arange(8).reshape((2, 2, 2)))
    with GRAPHICS_LAZY.temporary_set(True):
        quib = np.apply_along_axis(func, axis=0, arr=arr)
    quib.get_shape()
    current_call_count = func.call_count

    # This is referencing one specific call of the function
    res = quib[0][0].get_value()

    assert res == 1
    assert func.call_count == current_call_count + 1

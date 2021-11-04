import dataclasses
import itertools
from typing import Callable, Any

import numpy as np
from pytest import mark

from pyquibbler import iquib
from pyquibbler.env import GRAPHICS_LAZY
from pyquibbler.quib import PathComponent
from pyquibbler.quib.graphics import AlongAxisGraphicsFunctionQuib
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


def create_lazy_apply_along_axis_quib(func, arr, axis):
    with GRAPHICS_LAZY.temporary_set(True):
        return np.apply_along_axis(func, axis=axis, arr=iquib(arr))


@mark.parametrize('shape, axis, func1d_res', [
        (tuple(dimensions), axis, res)
        for shape_size in range(0, 3)
        for axis in range(-shape_size, shape_size)
        for dimensions in itertools.product(*[range(1, 4) for _ in range(shape_size)])
        for res in [1, np.arange(9).reshape((3, 3)), None]
])
def test_apply_along_axis_get_shape(shape, axis, func1d_res):
    func = get_func_mock(lambda x: func1d_res)
    arr = np.arange(np.prod(shape)).reshape(shape)
    quib = create_lazy_apply_along_axis_quib(func=func, arr=arr, axis=axis)
    expected_input_arr = arr[tuple([slice(None) if i == axis else 0 for i in range(len(arr.shape))])]

    res = quib.get_shape()

    assert func.call_count == 1
    call = func.mock_calls[0]
    assert np.array_equal(call.args[0], expected_input_arr)
    assert res == np.apply_along_axis(func, axis=axis, arr=arr).shape


@mark.parametrize('input_shape, apply_result_shape, axis, component', [
        (tuple(input_dimensions), tuple(apply_dimensions), axis, component)
        for input_shape_size in range(0, 3)
        for axis in range(-input_shape_size, input_shape_size)
        for apply_result_shape_size in range(0, 3)
        for input_dimensions in itertools.product(*[range(1, 4) for _ in range(input_shape_size)])
        for apply_dimensions in [[], *itertools.product(*[range(1, 3) for _ in range(apply_result_shape_size)])]
        for component in [()]
])
def test_apply_along_axis_get_value(input_shape, apply_result_shape, axis, component):

    slices = []
    collecting = False

    def apply(oned_slice):
        if collecting:
            slices.append(oned_slice)
        return np.full(apply_result_shape, np.sum(oned_slice))

    func = get_func_mock(apply)
    arr = np.arange(np.prod(input_shape)).reshape(input_shape)
    quib = create_lazy_apply_along_axis_quib(arr=arr, func=func, axis=axis)

    collecting = True
    res = quib.get_value_valid_at_path([PathComponent(component=component, indexed_cls=np.ndarray)])
    collecting = False

    current_result = np.apply_along_axis(func, axis=axis, arr=arr)[component]
    assert np.array_equal(res[component], current_result)

    # make sure all slices gotten were relevant
    for slice_ in slices:
        for num in np.ravel(slice_):
            new_arr = np.array(arr)
            new_arr[new_arr == num] = 999
            assert not np.array_equal(np.apply_along_axis(func, axis=axis, arr=new_arr)[component], current_result)


def test_apply_along_axis_returning_quib():
    func = lambda x: iquib(100)
    quib = create_lazy_apply_along_axis_quib(func=func, arr=np.array([[1]]), axis=0)

    res = quib.get_value()

    assert res == 1
    assert func.call_count == current_call_count + 1

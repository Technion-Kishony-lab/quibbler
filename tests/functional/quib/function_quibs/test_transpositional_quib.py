from unittest import mock

import numpy as np
import pytest
from operator import getitem

from pyquibbler import iquib
from pyquibbler.quib import DefaultFunctionQuib, Quib
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.cache import CacheStatus
from pyquibbler.quib.function_quibs.transpositional.transpositional_function_quib import TranspositionalFunctionQuib

from ..utils import PathBuilder, check_get_value_valid_at_path


@pytest.fixture()
def input_quib():
    return iquib(np.array([[1, 2, 3]]))


@pytest.fixture()
def rot90_quib(input_quib):
    return TranspositionalFunctionQuib.create(
        func=np.rot90,
        func_args=(input_quib,)
    )


@pytest.fixture()
def getitem_quib(rot90_quib):
    getitem_quib_ = TranspositionalFunctionQuib.create(
        func=getitem,
        func_args=(rot90_quib, (0, 0))
    )
    getitem_quib_.get_value()
    return getitem_quib_


def test_invalidate_and_redraw_invalidates_that_which_should_be_invalidated(rot90_quib, getitem_quib):
    rot90_quib.invalidate_and_redraw_at_path(PathBuilder(rot90_quib)[0, 0].path)

    assert getitem_quib.cache_status == CacheStatus.ALL_INVALID


def test_invalidate_and_redraw_does_not_invalidate_that_which_should_not_be_invalidated(rot90_quib, getitem_quib):
    rot90_quib.invalidate_and_redraw_at_path(PathBuilder(rot90_quib)[1, 0].path)

    assert getitem_quib.cache_status == CacheStatus.ALL_VALID


def test_invalidate_and_redraw_invalidates_that_which_should_be_invalidated_with_multiple_steps(
        input_quib,
        getitem_quib
):
    input_quib.invalidate_and_redraw_at_path(PathBuilder(input_quib)[0, 1].path)

    assert getitem_quib.cache_status == CacheStatus.ALL_VALID


def test_invalidate_and_redraw_does_not_invalidate_that_which_should_be_invalidated_with_multiple_steps(
        input_quib,
        getitem_quib
):
    input_quib.invalidate_and_redraw_at_path(PathBuilder(input_quib)[0, 2].path)

    assert getitem_quib.cache_status == CacheStatus.ALL_INVALID


def test_invalidate_and_redraw_on_dict_invalidates_child():
    quib = iquib({"maor": 1})
    second_quib = quib["maor"]

    quib.invalidate_and_redraw_at_path(PathBuilder(quib)['maor'].path)

    assert second_quib.cache_status == CacheStatus.ALL_INVALID


def test_invalidate_and_redraw_on_dict_doesnt_invalidate_irrelevant_child():
    quib = iquib({"maor": 1, 'y': 2})
    second_quib = quib["maor"]
    second_quib.get_value()

    quib.invalidate_and_redraw_at_path(PathBuilder(quib)['y'].path)

    assert second_quib.cache_status == CacheStatus.ALL_VALID


def test_invalidate_and_redraw_on_inner_list():
    quib = iquib({"a": np.array([[0, 2]])})
    second_quib = quib["a"]
    third_quib = second_quib[(0, 0)]
    third_quib.get_value()

    quib.invalidate_and_redraw_at_path(PathBuilder(quib)['a'].path)

    assert third_quib.cache_status == CacheStatus.ALL_INVALID


def test_invalidate_and_redraw_on_dict_after_index():
    quib = iquib([1, 2, {'MAOR': '^'}])
    second_quib = quib[2]
    third_quib = second_quib['MAOR']

    quib.invalidate_and_redraw_at_path(PathBuilder(quib)[2].path)

    assert third_quib.cache_status == CacheStatus.ALL_INVALID


@pytest.fixture()
def quib_dict():
    return iquib({'a': {'b': 1}})


def test_invalidate_embedded_dicts_shouldnt_invalidate(quib_dict):
    second_quib = quib_dict['a']
    third_quib = second_quib['b']
    third_quib.get_value()

    quib_dict.invalidate_and_redraw_at_path(PathBuilder(quib_dict)['a']['c'].path)

    assert third_quib.cache_status == CacheStatus.ALL_VALID


def test_invalidate_embedded_dicts_should_invalidate(quib_dict):
    second_quib = quib_dict['a']['b']
    second_quib.get_value()

    quib_dict.invalidate_and_redraw_at_path(PathBuilder(quib_dict)['a']['b'].path)

    assert second_quib.cache_status == CacheStatus.ALL_INVALID


@pytest.fixture()
def quib_with_nested_arr():
    dtype = [('nested', [('child_name', np.unicode, 30)], (2,))]
    return iquib(np.array(['Yechiel', "Yossiel"], dtype=dtype))


@pytest.fixture()
def children(quib_with_nested_arr):
    return quib_with_nested_arr['nested']['child_name']


def test_invalidate_and_redraw_with_expanding_shape_shouldnt_invalidate(quib_with_nested_arr, children):
    first_row = children[1]
    child = first_row[0]
    child.get_value()

    quib_with_nested_arr.invalidate_and_redraw_at_path(PathBuilder(quib_with_nested_arr)[0].path)

    assert child.cache_status == CacheStatus.ALL_VALID


def test_invalidate_and_redraw_with_expanding_shape_should_invalidate(quib_with_nested_arr, children):
    first_row = children[0]
    child = first_row[0]
    child.get_value()

    quib_with_nested_arr.invalidate_and_redraw_at_path(PathBuilder(quib_with_nested_arr)[0].path)

    assert child.cache_status == CacheStatus.ALL_INVALID


def test_invalidate_and_redraw_with_double_field_keys_invalidates(quib_with_nested_arr, children):
    first_row = children[0]
    child = first_row[0]
    child.get_value()

    quib_with_nested_arr.invalidate_and_redraw_at_path(PathBuilder(quib_with_nested_arr)["nested"]["child_name"].path)

    assert child.cache_status == CacheStatus.ALL_INVALID


def test_invalidate_and_redraw_multiple_getitems():
    quib = iquib(np.array([1, 2, 3, 4, 5]))
    child = quib[1:4][2:3]
    child.get_value()

    quib.invalidate_and_redraw_at_path(PathBuilder(quib)[3].path)

    assert child.cache_status == CacheStatus.ALL_INVALID


def test_invalidate_and_redraw_with_dict_and_ndarrays_within():
    quib = iquib({
        'a': np.array([{
            'c': 'd'
        }]),
    })
    child = quib['a'][0]['c']
    child.get_value()

    quib.invalidate_and_redraw_at_path(PathBuilder(quib)['a'][0]['c'].path)

    assert child.cache_status == CacheStatus.ALL_INVALID


def test_invalidate_and_redraw_with_dict_and_ndarrays_within_does_not_invalidate():
    quib = iquib({
        'a': np.array([{
            'c': 'd'
        }]),
    })
    child = quib['a'][0]['c']
    child.get_value()

    quib.invalidate_and_redraw_at_path(PathBuilder(quib)['a'][0]['e'].path)

    assert child.cache_status == CacheStatus.ALL_VALID


def test_invalidate_and_redraw_invalidates_all_when_minor_parameter_changes():
    quib = iquib(np.array([1, 2, 3]))
    param = iquib(3)
    repeated = np.repeat(quib, param)
    child = repeated[6]
    child.get_value()

    param.invalidate_and_redraw_at_path(PathBuilder(param)[...].path)

    assert child.cache_status == CacheStatus.ALL_INVALID


def test_can_getitem_on_object_without_diverged_cache():
    """
    If the function doesn't have a diverged cache it should request full validity from its parents,
    so it won't try to update the cache in a specific path component
    """
    obj = type('TypeACacheIsNotImplementedFor', (), dict(__getitem__=lambda self, item: item))()
    quib = iquib([obj])
    quib[0][0].get_value()


@pytest.mark.parametrize('data', [np.arange(24).reshape((2, 3, 4))])
@pytest.mark.parametrize('indices_to_get_value_at', [-1, 0, (1, 1), (2, 1, 3), [True, False, False], (0, ...)])
def test_transpositional_get_value(data, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(np.rot90, data, path_to_get_value_at)


@pytest.mark.parametrize('data', [np.array([[('a', 23, 1), ('b', 24, 10), ('c', 25, 100)]],
                                           dtype=[('name', '|S21'), ('age', 'i8'), ('random', 'i4')])])
@pytest.mark.parametrize('indices_to_get_value_at', [
    (0,), (slice(0, 2)), 'name', slice(None), slice(None, 2)
])
def test_transpositional_get_value_with_fields(data, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(lambda x: x[0], data, path_to_get_value_at)


@pytest.mark.regression
def test_transpositional_concatenate_different_sizes():
    def filter_out_none_calls(mock_calls):
        return [
            mock_call
            for mock_call in mock_calls
            if mock_call.args[0] is not None
        ]

    first = mock.Mock(spec=Quib)
    first.get_value_valid_at_path.return_value = [[1, 2, 3]]
    first.get_shape.return_value.get_value.return_value = (1, 3)
    second = mock.Mock(spec=Quib)
    second.get_shape.return_value.get_value.return_value = (1, 3)
    second.get_value_valid_at_path.return_value = [[1, 2, 3]]

    quib = np.concatenate((first, second))
    quib[1].get_value()

    assert len(filter_out_none_calls(first.get_value_valid_at_path.mock_calls)) == 0
    assert len(filter_out_none_calls(second.get_value_valid_at_path.mock_calls)) == 1

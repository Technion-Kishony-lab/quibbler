from operator import getitem

import numpy as np
import pytest

from pyquibbler import iquib, Assignment, q
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.function_quibs.transpositional_function_quib import TranspositionalFunctionQuib


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
    rot90_quib.invalidate_and_redraw_at_path(path=[PathComponent(component=(0, 0), indexed_cls=rot90_quib.get_type())])

    assert not getitem_quib.is_cache_valid


def test_invalidate_and_redraw_does_not_invalidate_that_which_should_not_be_invalidated(rot90_quib, getitem_quib):
    rot90_quib.invalidate_and_redraw_at_path(path=[PathComponent(component=(1, 0), indexed_cls=rot90_quib.get_type())])

    assert getitem_quib.is_cache_valid


def test_invalidate_and_redraw_invalidates_that_which_should_be_invalidated_with_multiple_steps(
        input_quib,
        getitem_quib
):
    input_quib.invalidate_and_redraw_at_path(path=[PathComponent(component=(0, 1), indexed_cls=input_quib.get_type())])

    assert getitem_quib.is_cache_valid


def test_invalidate_and_redraw_does_not_invalidate_that_which_should_be_invalidated_with_multiple_steps(
        input_quib,
        getitem_quib
):
    input_quib.invalidate_and_redraw_at_path(path=[PathComponent(component=(0, 2), indexed_cls=input_quib.get_type())])

    assert not getitem_quib.is_cache_valid


def test_invalidate_and_redraw_on_dict_invalidates_child():
    quib = iquib({"maor": 1})
    second_quib = quib["maor"]

    quib.invalidate_and_redraw_at_path(path=[PathComponent(component="maor", indexed_cls=quib.get_type())])

    assert not second_quib.is_cache_valid


def test_invalidate_and_redraw_on_dict_doesnt_invalidate_irrelevant_child():
    quib = iquib({"maor": 1, 'y': 2})
    second_quib = quib["maor"]
    second_quib.get_value()

    quib.invalidate_and_redraw_at_path(path=[PathComponent(indexed_cls=quib.get_type(), component="y")])

    assert second_quib.is_cache_valid


def test_invalidate_and_redraw_on_inner_list(
):
    quib = iquib({"a": np.array([[0, 2]])})
    second_quib = quib["a"]
    third_quib = second_quib[(0, 0)]
    third_quib.get_value()

    quib.invalidate_and_redraw_at_path(path=[PathComponent(indexed_cls=quib.get_type(), component="a")])

    assert not third_quib.is_cache_valid


def test_invalidate_and_redraw_on_dict_after_index(
):
    quib = iquib([1, 2, {
        'MAOR': 'YELED EFES'
    }])
    second_quib = quib[2]
    third_quib = second_quib['MAOR']

    quib.invalidate_and_redraw_at_path(path=[PathComponent(component=2, indexed_cls=quib.get_type())])

    assert not third_quib.is_cache_valid


@pytest.fixture()
def quib_dict():
    return iquib({
        'a': {
            'b': 1
        }
    })


def test_invalidate_embedded_dicts_shouldnt_invalidate(quib_dict):
    second_quib = quib_dict['a']
    third_quib = second_quib['b']
    third_quib.get_value()

    quib_dict.invalidate_and_redraw_at_path(path=[PathComponent(component='a', indexed_cls=dict),
                                                  PathComponent(component='c', indexed_cls=dict)])

    assert third_quib.is_cache_valid


def test_invalidate_embedded_dicts_should_invalidate(quib_dict):
    second_quib = quib_dict['a']['b']
    second_quib.get_value()

    quib_dict.invalidate_and_redraw_at_path(path=[PathComponent(component='a', indexed_cls=dict),
                                                  PathComponent(component='b', indexed_cls=dict)])

    assert not second_quib.is_cache_valid


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

    quib_with_nested_arr.invalidate_and_redraw_at_path(path=[PathComponent(component=0,
                                                                           indexed_cls=quib_with_nested_arr.get_type())])

    assert child.is_cache_valid


def test_invalidate_and_redraw_with_expanding_shape_should_invalidate(quib_with_nested_arr, children):
    first_row = children[0]
    child = first_row[0]
    child.get_value()

    quib_with_nested_arr.invalidate_and_redraw_at_path(path=[PathComponent(component=0, indexed_cls=quib_with_nested_arr.get_type())])

    assert not child.is_cache_valid


def test_invalidate_and_redraw_with_double_field_keys_invalidates(quib_with_nested_arr, children):
    first_row = children[0]
    child = first_row[0]
    child.get_value()

    quib_with_nested_arr.invalidate_and_redraw_at_path(path=[PathComponent(component="nested",
                                                                           indexed_cls=quib_with_nested_arr.get_type()),
                                                             PathComponent(component="child_name",
                                                                   indexed_cls=quib_with_nested_arr.get_type())
                                                             ])

    assert not child.is_cache_valid


def test_invalidate_and_redraw_multiple_getitems():
    quib = iquib(np.array([1, 2, 3, 4, 5]))
    child = quib[1:4][2:3]
    child.get_value()

    quib.invalidate_and_redraw_at_path(path=[PathComponent(component=3,
                                                           indexed_cls=np.ndarray), ])

    assert not child.is_cache_valid


def test_invalidate_and_redraw_with_dict_and_ndarrays_within():
    quib = iquib({
        'a': np.array([{
            'c': 'd'
        }]),
    })
    child = quib['a'][0]['c']
    child.get_value()

    quib.invalidate_and_redraw_at_path(path=[PathComponent(component="a",
                                                           indexed_cls=dict),
                                             PathComponent(component=0,
                                                   indexed_cls=np.ndarray),
                                             PathComponent(
                                         component='c',
                                         indexed_cls=dict
                                     )
                                             ])

    assert not child.is_cache_valid


def test_invalidate_and_redraw_with_dict_and_ndarrays_within_does_not_invalidate():
    quib = iquib({
        'a': np.array([{
            'c': 'd'
        }]),
    })
    child = quib['a'][0]['c']
    child.get_value()

    quib.invalidate_and_redraw_at_path(path=[PathComponent(component="a",
                                                           indexed_cls=dict),
                                             PathComponent(component=0,
                                                   indexed_cls=np.ndarray),
                                             PathComponent(
                                         component='e',
                                         indexed_cls=dict
                                     )
                                             ])

    assert child.is_cache_valid


def test_invalidate_and_redraw_invalidates_all_when_minor_parameter_changes():
    quib = iquib(np.array([1, 2, 3]))
    param = iquib(3)
    repeated = np.repeat(quib, param)
    child = repeated[6]
    child.get_value()

    param.invalidate_and_redraw_at_path(path=[PathComponent(component=...,
                                                            indexed_cls=int), ])

    assert not child.is_cache_valid

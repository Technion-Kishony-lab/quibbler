from unittest import mock

import numpy as np

from pyquibbler import create_quib


def test_parents(create_quib_with_return_value):
    grandparent =  create_quib(func=mock.Mock())
    parent1 =  create_quib(func=mock.Mock())
    parent2 = create_quib(func=mock.Mock(), args=(grandparent,))
    me = create_quib(func=mock.Mock(), args=(0, parent1, 2), kwargs=dict(a=parent2, b=3))

    assert me.get_parents() == {parent1, parent2}


def test_ancestors():
    great_grandparent = create_quib(func=mock.Mock())
    grandparent = create_quib(func=mock.Mock(), args=(great_grandparent,))
    parent = create_quib(func=mock.Mock(), args=(grandparent,))
    me = create_quib(func=mock.Mock(), args=(parent,))

    assert me.get_ancestors() == {great_grandparent, grandparent, parent}


def test_ancestors_with_depth():
    great_grandparent = create_quib(func=mock.Mock())
    grandparent = create_quib(func=mock.Mock(), args=(great_grandparent,))
    parent = create_quib(func=mock.Mock(), args=(grandparent,))
    me = create_quib(func=mock.Mock(), args=(parent,))
    assert me.get_ancestors(depth=2) == {grandparent, parent}


def test_descendants():
    me = create_quib(func=mock.Mock())
    child = create_quib(func=mock.Mock(), args=(me,), assigned_name='child')
    grand_child = create_quib(func=mock.Mock(), args=(child,))  # unnamed (intermediate)
    great_grand_child = create_quib(func=mock.Mock(), args=(grand_child,), assigned_name='great_grand_child')

    assert me.get_descendants() == {child, grand_child, great_grand_child}
    assert me.get_descendants(depth=2) == {child, grand_child}
    assert me.get_descendants(depth=2, bypass_intermediate_quibs=True) == {child, great_grand_child}


def test_named_parents():
    grandma = create_quib(func=mock.Mock(), assigned_name='grandma')
    mom = create_quib(func=mock.Mock(), args=(grandma,), assigned_name='mom')
    grandpa = create_quib(func=mock.Mock(), assigned_name='grandpa')
    dad = create_quib(func=mock.Mock(), args=(grandpa,), assigned_name=None)  # unnamed
    me = create_quib(func=mock.Mock(), args=(mom, dad))

    assert me.get_parents(True) == {mom, grandpa}


def test_data_versus_parameter_parents():
    data_mom = create_quib(func=mock.Mock())
    parameter_mom = create_quib(func=mock.Mock())
    me = create_quib(func=np.array, args=(data_mom, parameter_mom))

    assert me.get_parents(is_data_source=None) == {data_mom, parameter_mom}
    assert me.get_parents(is_data_source=True) == {data_mom}
    assert me.get_parents(is_data_source=False) == {parameter_mom}


def test_named_children():
    me = create_quib(func=mock.Mock())
    son = create_quib(func=mock.Mock(), args=(me,), assigned_name=None)  # unnamed
    daughter = create_quib(func=mock.Mock(), args=(me,), assigned_name='daughter')
    grand_son = create_quib(func=mock.Mock(), args=(son,), assigned_name='grandson')
    grand_daughter = create_quib(func=mock.Mock(), args=(daughter,), assigned_name='grandpa')

    assert me.get_children(True) == {daughter, grand_son}

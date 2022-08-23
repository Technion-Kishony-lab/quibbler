from unittest import mock

import matplotlib.pyplot as plt
import numpy as np
import pytest

from pyquibbler.env import PRETTY_REPR
from pyquibbler.quib.specialized_functions.iquib import iquib
from pyquibbler import q, quiby, create_quib, obj2quib


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_with_quibs_being_created_inline():
    a = iquib([1, 2, 3])
    b, c = a[0], iquib(2)

    assert b.pretty_repr == 'b = a[0]'
    assert c.pretty_repr == 'c = iquib(2)'


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_with_quibs_with_quib_creation_with_name_in_inner_func():
    @quiby(lazy=False)
    def inner_func():
        d = iquib(4)
        return d

    @quiby(lazy=False)
    def another_inner_func():
        e = iquib(4)
        return e

    a, b = inner_func(), another_inner_func()

    assert a.pretty_repr == 'a = inner_func()'
    assert b.pretty_repr == 'b = another_inner_func()'


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_with_repr_throwing_exception():
    class A:
        def __repr__(self):
            raise Exception()

    quib = iquib(A())
    assert quib.pretty_repr == "quib = [exception during repr]"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_without_name():
    a = iquib(1)
    b = iquib(2)

    assert q("".join, [a, b]).pretty_repr == 'join([a, b])'


@pytest.mark.parametrize("statement", [
    "a[:]",
    "a[1:2:3]",
    "a[1::2]",
    "a[::2]",
    "a[:2]",
    "a[1:]"
])
@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_getitem_colon(statement):
    a = iquib(np.array([1, 2, 3]))
    b = eval(statement)

    assert b.pretty_repr == statement


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_set():
    a = iquib({0})

    assert a.pretty_repr == "a = iquib({0})"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_none():
    a = iquib([None])

    assert a.pretty_repr == "a = iquib([None])"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_dict():
    a = iquib(1)
    b = q(str, {'data': a, 'num': 2, 1.0: 'b'})

    assert b.pretty_repr == "b = str({'data': a, 'num': 2, 1.0: 'b'})"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_slice_as_objet():
    a = iquib(slice(0, 4, 1))

    assert a.pretty_repr == "a = iquib(slice(0, 4, 1))"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_kwargs():
    a = iquib(1)
    b = np.sum([[1]], axis=(0, a))

    assert b.pretty_repr == "b = sum([[1]], axis=(0, a))"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_getitem_ellipsis():
    a = iquib(np.array([1, 2, 3]))
    b = a[...]

    assert b.pretty_repr == "b = a[...]"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_getitem_multiple_axes():
    a = iquib(np.array([[1]]))
    b = a[0, 0]

    assert b.pretty_repr == "b = a[0, 0]"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_single_tuple_getitem():
    a = iquib(np.array([0]))
    b = a[(0,)]

    assert b.pretty_repr == "b = a[(0,)]"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_getitem_index():
    a = iquib(np.array([1, 2, 3]))
    b = a[1]

    assert b.pretty_repr == "b = a[1]"


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_on_q_with_dict():
    x = iquib(3)

    assert q(dict, ('num', x)).pretty_repr == "dict(('num', x))"


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_getitem_pretty_repr_with_quib_as_item():
    a = iquib([1, 2, 3])
    b = iquib(1)

    assert a[:b].pretty_repr == 'a[:b]'


@pytest.mark.get_variable_names(True)
def test_pretty_repr_str_format():
    a = iquib(3)
    b = iquib(7)
    assert q('a = {}, b = {}'.format, a, b).pretty_repr == '"a = {}, b = {}".format(a, b)'


@pytest.mark.get_variable_names(True)
def test_pretty_repr_class_override():
    from matplotlib.patches import Rectangle
    xy = iquib((3, 2))
    w = iquib(7)
    r = Rectangle(xy, w, 4, color='r')
    assert r.pretty_repr == "r = Rectangle(xy, w, 4, color='r')"


@pytest.mark.get_variable_names(True)
def test_pretty_plt_plot(axes):
    x = iquib(1)
    h = plt.plot(x, x ** 2, color='r')
    assert h.pretty_repr == "h = plot(x, x ** 2, color='r')"


@pytest.mark.get_variable_names(True)
def test_pretty_plt_bar(axes):
    heights = iquib([1, 2, 3])
    h = plt.bar(['r', 'g', 'b'], heights)
    assert h.pretty_repr == "h = bar(['r', 'g', 'b'], heights)"


# This test only broke within Jupyter lab
@pytest.mark.get_variable_names(True)
def test_pretty_plt_imshow(axes):
    img = iquib(np.zeros((3, 4)))
    plt.imshow(img)
    assert next(iter(img.get_children())).pretty_repr == "imshow(img)"


@pytest.mark.get_variable_names(True)
def test_pretty_obj2quib():
    a = iquib(1)
    b = obj2quib([0, a, 1])

    assert b.pretty_repr == "b = obj2quib([0, a, 1])"


def test_ugly_repr():
    with PRETTY_REPR.temporary_set(False):
        a = iquib(17)
        b = a + 10
        assert repr(b) == '<Quib - <built-in function add>>'

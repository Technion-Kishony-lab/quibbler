import numpy as np
from pytest import fixture

from pyquibbler import iquib, quiby, is_quiby, not_quiby
from pyquibbler.quib.graphics.event_handling.utils import is_quib
from pyquibbler.utilities.basic_types import Mutable


def normal_func_that_cannot_work_directly_on_quibs(x, y, z):
    assert not is_quib(x)
    assert not is_quib(y)
    assert not is_quib(z)
    return x + y + z


@fixture
def dummy_graphics_quib():
    return Mutable(None)


@fixture
def x_value():
    return np.array([1, 2])


@fixture
def y_value():
    return 10


@fixture
def z_value():
    return 100


@fixture
def x_quib(x_value):
    return iquib(x_value)


@fixture
def y_quib(y_value):
    return iquib(y_value)


@fixture()
def quiby_class(dummy_graphics_quib):

    @quiby(create_quib=None)
    class Obj:
        CALLED = {'quiby_property': 0, 'quiby_method': 0, 'dependent_quiby_method': 0,
                  'set_x_value_at_idx': 0, 'create_graphics': 0}

        def __init__(self, x, y, z):
            self.x = x  # quib
            self.y = y  # quib
            self.z = z  # not a quib
            dummy_graphics_quib.set(None)


        @property
        def quiby_property(self):
            self.CALLED['quiby_property'] += 1
            return normal_func_that_cannot_work_directly_on_quibs(self.x, self.y, self.z)

        def quiby_method(self):
            self.CALLED['quiby_method'] += 1
            return normal_func_that_cannot_work_directly_on_quibs(self.x, self.y, self.z)

        def dependent_quiby_method(self, factor):
            self.CALLED['dependent_quiby_method'] += 1
            return self.quiby_method() * factor

        @not_quiby
        def set_x_value_at_idx(self, idx, value):
            self.CALLED['set_x_value_at_idx'] += 1
            self.x[idx] = value

        @quiby(pass_quibs=True, is_graphics=True)
        def create_graphics(self):
            self.CALLED['create_graphics'] += 1
            dummy_graphics_quib.set(self.x + self.y)

        @not_quiby
        def get_bare_x(self):
            # return the quib itself
            return self.x

    return Obj


@fixture
def quiby_obj(quiby_class, x_quib, y_quib, z_value):
    return quiby_class(x_quib, y_quib, z_value)


def test_quiby_class_init(quiby_obj, x_quib, y_quib, z_value):
    assert quiby_obj.x is x_quib
    assert quiby_obj.y is y_quib
    assert quiby_obj.z == z_value
    # assert no function calls were made yet:
    assert all(v == 0 for v in quiby_obj.CALLED.values())


def test_quiby_class_quiby_method(quiby_obj, x_quib, y_quib, x_value, y_value, z_value):
    quiby_obj.quiby_method()
    assert is_quiby(quiby_obj.quiby_method)
    result = quiby_obj.quiby_method()
    assert is_quib(result)
    assert np.array_equal(result.get_value(), x_value + y_value + z_value)
    x_quib[0] = 20
    assert np.array_equal(result.get_value(), x_value + y_value + z_value + [19, 0])


def test_quiby_class_quiby_property(quiby_obj, x_quib, y_quib, x_value, y_value, z_value):
    result = quiby_obj.quiby_property
    assert is_quib(result)
    assert np.array_equal(result.get_value(), x_value + y_value + z_value)
    x_quib[0] = 20
    assert np.array_equal(result.get_value(), x_value + y_value + z_value + [19, 0])
    y_quib.assign(50)
    assert np.array_equal(result.get_value(), x_value + 50 + z_value + [19, 0])


def test_quiby_class_dependent_quiby_method(quiby_obj, x_quib, y_quib, x_value, y_value, z_value):
    result = quiby_obj.dependent_quiby_method(2)
    assert is_quib(result)
    assert np.array_equal(result.get_value(), 2 * (x_value + y_value + z_value))
    x_quib[0] = 20
    assert np.array_equal(result.get_value(), 2 * (x_value + y_value + z_value + [19, 0]))
    y_quib.assign(50)
    assert np.array_equal(result.get_value(), 2 * (x_value + 50 + z_value + [19, 0]))


def test_quiby_class_set_x_value_at_idx(quiby_obj, x_quib, y_quib, x_value, y_value, z_value):
    assert np.array_equal(x_quib.get_value(), [1, 2])  # sanity check
    quiby_obj.set_x_value_at_idx(0, 30)
    assert np.array_equal(x_quib.get_value(), [30, 2])
    result = quiby_obj.quiby_method()
    assert is_quib(result)
    assert np.array_equal(result.get_value(), np.array([30, 2]) + y_value + z_value)
    x_quib[0] = 40
    assert np.array_equal(result.get_value(), np.array([40, 2]) + y_value + z_value)

def test_quiby_class_get_bare_x(quiby_obj, x_quib):
    bare_x = quiby_obj.get_bare_x()
    assert bare_x is x_quib


def test_quiby_class_create_graphics(quiby_obj, x_quib, y_quib, dummy_graphics_quib):
    assert dummy_graphics_quib.val is None
    graphics_quib = quiby_obj.create_graphics()
    assert is_quib(graphics_quib)
    assert np.array_equal(dummy_graphics_quib.val.get_value(), np.array([1, 2]) + 10)
    x_quib[0] = 20
    assert np.array_equal(dummy_graphics_quib.val.get_value(), np.array([20, 2]) + 10)

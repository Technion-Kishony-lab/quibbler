import pytest

import numpy as np
from matplotlib.patches import Rectangle
from pyquibbler import iquib


def check_rectangle_location(rectangle: Rectangle, args):
    xy, w, h = args
    return np.array_equal(rectangle.get_xy(), xy) \
        and rectangle.get_width() == w \
        and rectangle.get_height() == h


@pytest.fixture()
def get_only_patch_from_axes(axes):

    def get_():
        assert len(axes.patches) == 1
        return axes.patches[0]

    return get_


def test_axes_add_patch_on_non_quib(axes, get_only_patch_from_axes):
    p = Rectangle((1, 2), 3, 4)
    axes.add_patch(p)
    assert p is get_only_patch_from_axes()


def test_axes_add_patch_on_quib(axes, get_only_patch_from_axes):
    w = iquib(3)
    p = Rectangle((1, 2), w, 4)
    axes.add_patch(p)
    assert p.get_value() is get_only_patch_from_axes()


def test_patch_update(axes, get_only_patch_from_axes):
    w = iquib(3)
    p = Rectangle((1, 2), w, 4)
    axes.add_patch(p)
    assert check_rectangle_location(p.get_value(), ((1, 2), 3, 4)), "sanity"

    w.assign(10)
    assert p.get_value() is get_only_patch_from_axes()
    assert check_rectangle_location(p.get_value(), ((1, 2), 10, 4))
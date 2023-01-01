import pytest

from pyquibbler import iquib, quiby
from pyquibbler.quib.graphics.graphics_assignment_mode import graphics_assignment_mode
from pyquibbler.quib.graphics.redraw import start_dragging, end_dragging
import matplotlib.pyplot as plt

from tests.conftest import create_axes_mouse_press_move_release_events


@quiby(is_graphics=True)
def validate_input(x):
    if x < 0:
        raise Exception("x cannot be negative")


def test_prevent_assignments_causing_exception():

    a = iquib(1)
    validate = validate_input(a)

    with graphics_assignment_mode(True):
        a.assign(-1)
    assert a.get_value() == 1


def test_prevent_assignments_causing_exception_on_drop():
    @quiby(is_graphics=True)
    def validate_input(x):
        if x < 0:
            raise Exception("x cannot be negative")

    a = iquib(1)
    validate = validate_input(a)
    validate.graphics_update = 'drop'

    start_dragging()
    with graphics_assignment_mode(True):
        a.assign(-1)
        assert a.get_value() == -1

    end_dragging()
    assert a.get_value() == 1


# TODO: need to implement drag causing exception only on one axis. See test below

@pytest.mark.skip
def test_prevent_assignments_causing_exception_on_one_axis(axes, create_axes_mouse_press_move_release_events):

    x = iquib(0)
    y = iquib(5)
    validate = validate_input(x)

    axes.axis([-10, 10, -10, 10])
    plt.plot(x, y, 'o')

    create_axes_mouse_press_move_release_events(((0, 5), (-2, 8)))

    assert x.get_value() == 0
    assert y.get_value() == 8

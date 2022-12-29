from pyquibbler import iquib, quiby
from pyquibbler.quib.graphics.graphics_assignment_mode import graphics_assignment_mode
from pyquibbler.quib.graphics.redraw import start_dragging, end_dragging


def test_prevent_assignments_causing_exception():
    @quiby(is_graphics=True)
    def validate_input(x):
        if x < 0:
            raise Exception("x cannot be negative")

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

from pyquibbler import iquib, quiby
from pyquibbler.quib.graphics.graphics_assignment_mode import graphics_assignment_mode


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

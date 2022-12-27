from pyquibbler import iquib, quiby


@quiby(is_graphics=True)
def validate_input(x):
    if x < 0:
        raise Exception("x cannot be negative")


def test_prevent_assignments_causing_exception():
    a = iquib(1)
    validate = validate_input(a)

    a.assign(-1)
    assert a.get_value() == 1

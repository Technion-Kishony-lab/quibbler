from pyquibbler.quib.assignment import Overrider


def test_overrider():
    overrider = Overrider()
    overrider.add_assignment(0, 1)
    data = [0]

    overrider.override(data)

    assert data == [1]

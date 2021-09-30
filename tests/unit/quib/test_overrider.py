from pyquibbler.quib.overrider import Overrider


def test_overrider():
    overrider = Overrider()
    overrider.add_override(0, 1)
    data = [0]

    overrider.override(data)

    assert data == [1]

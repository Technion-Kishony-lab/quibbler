from pyquibbler import iquib


def test_display_props_of_iquib():
    a = iquib(0)
    a.display()


def test_display_props_of_fquib():
    a = iquib(0)
    b = a + 1
    b.display()

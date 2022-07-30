from pyquibbler import iquib

def test_display_props_of_iquib():
    a = iquib(0)
    a.display_props()

def test_display_props_of_fquib():
    a = iquib(0)
    b = a + 1
    b.display_props()


def test_wip():
    a = iquib(1)
    b = a + 2
    a.named_children
    b.named_parents
    
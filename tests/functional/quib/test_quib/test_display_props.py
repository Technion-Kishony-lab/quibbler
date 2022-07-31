from pyquibbler import iquib


def test_display_props_of_iquib():
    a = iquib(0)
    a.display().get_html_repr()
    a.display().get_text_repr()


def test_display_props_of_fquib():
    a = iquib(0)
    b = a + 1
    a.display().get_html_repr()
    a.display().get_text_repr()

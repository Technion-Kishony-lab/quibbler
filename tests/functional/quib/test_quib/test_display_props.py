from pyquibbler import iquib


def test_display_properties_of_iquib():
    a = iquib(0)
    a.display_properties().get_html_repr()
    a.display_properties().get_text_repr()


def test_display_properties_of_fquib():
    a = iquib(0)
    b = a + 1
    a.display_properties().get_html_repr()
    a.display_properties().get_text_repr()

import matplotlib.pyplot as plt

from pyquibbler.quibapp import QuibApp


def test_get_or_create_creates_an_instance():
    assert QuibApp.current_quibapp is None, "sanity"
    QuibApp.get_or_create()
    assert QuibApp.current_quibapp is not None


def test_get_or_create_only_creates_one_instance():
    assert QuibApp.get_or_create() is QuibApp.get_or_create()


def test_quibapp_opens_the_app_figure():
    app = QuibApp.get_or_create()
    assert isinstance(app.app_figure, plt.Figure)


def test_quibapp_clears_upon_close():
    QuibApp.get_or_create()
    assert QuibApp.current_quibapp is not None, "sanity"
    QuibApp.close()
    assert QuibApp.current_quibapp is None

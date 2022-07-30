import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import pytest

from pyquibbler import iquib
from pyquibbler.quibapp import QuibApp


@pytest.fixture
def simulate_button_press():
    def _press(button: Button):
        for func_ref in button._observers.callbacks['clicked'].values():
            func = func_ref()
            func(None)
    return _press

def test_get_or_create_creates_an_instance():
    assert QuibApp.current_quibapp is None, "sanity"
    QuibApp.get_or_create()
    assert QuibApp.current_quibapp is not None


def test_get_or_create_only_creates_one_instance():
    assert QuibApp.get_or_create() is QuibApp.get_or_create()


def test_quibapp_opens_the_app_figure():
    app = QuibApp.get_or_create()
    assert isinstance(app.figure, plt.Figure)


def test_quibapp_clears_upon_close():
    QuibApp.get_or_create()
    assert QuibApp.current_quibapp is not None, "sanity"
    QuibApp.close()
    assert QuibApp.current_quibapp is None


def test_quibapp_undo_exception(simulate_button_press, capsys):
    app = QuibApp.get_or_create()
    undo_button = app._buttons['undo']
    simulate_button_press(undo_button)
    assert capsys.readouterr().out == 'There are no actions left to undo\n'


def test_quibapp_undo_exception2(simulate_button_press):
    app = QuibApp.get_or_create()
    a = iquib(1)
    a.assign(2)
    assert a.get_value() == 2, "sanity"
    undo_button = app._buttons['undo']
    simulate_button_press(undo_button)
    assert a.get_value() == 1

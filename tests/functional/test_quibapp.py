import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import pytest

from pyquibbler import iquib
from pyquibbler.user_utils.quibapp import QuibApp


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
    QuibApp.current_quibapp.close()

def test_get_or_create_only_creates_one_instance():
    assert QuibApp.get_or_create() is QuibApp.get_or_create()
    QuibApp.current_quibapp.close()


def test_quibapp_opens_the_app_figure(quibapp_):
    assert isinstance(quibapp_.figure, plt.Figure)


def test_quibapp_clears_upon_close(quibapp_):
    assert quibapp_.current_quibapp is not None, "sanity"
    QuibApp.get_or_create().close()
    assert quibapp_.current_quibapp is None


def test_quibapp_undo_exception(quibapp_, simulate_button_press, capsys):
    undo_button = quibapp_._buttons['undo']
    simulate_button_press(undo_button)
    assert capsys.readouterr().out == 'There are no actions left to undo.\n'


def test_quibapp_undo(quibapp_, simulate_button_press):
    a = iquib(1)
    a.assign(2)
    assert a.get_value() == 2, "sanity"
    undo_button = quibapp_._buttons['undo']
    simulate_button_press(undo_button)
    assert a.get_value() == 1

from unittest import mock

import matplotlib.pyplot as plt
import pytest

from pyquibbler import iquib
from pyquibbler.project import Project, NothingToUndoException
from pyquibbler.quibapp import QuibApp
from pyquibbler.quib import ImpureFunctionQuib, GraphicsFunctionQuib
from pyquibbler.quib.graphics.widgets.drag_context_manager import dragging
from pyquibbler.quibapp import APP_TITLE

def test_get_or_create_creates_an_instance():
    assert QuibApp.current_quibapp is None, "sanity"
    QuibApp.get_or_create()
    assert QuibApp.current_quibapp is not None


def test_get_or_create_only_creates_one_instance():
    assert QuibApp.get_or_create() is QuibApp.get_or_create()


def test_quibapp_opens_the_app_figure():
    plt.close(APP_TITLE)
    assert not plt.fignum_exists(APP_TITLE), "sanity"
    QuibApp.get_or_create()
    assert plt.fignum_exists(APP_TITLE)


def test_quibapp_clears_upon_window_closed():
    QuibApp.get_or_create()
    assert QuibApp.current_quibapp is not None, "sanity"
    plt.close(QuibApp.current_quibapp.app_figure)
    assert QuibApp.current_quibapp is None


import gc

import pytest
from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.widgets import AxesWidget

from pyquibbler.utilities.performance_utils import track_instances_of_class, TRACKED_CLASSES_TO_WEAKREFS, \
    get_all_instances_in_tracked_class


@pytest.fixture
def create_button_press_event(axes):
    def _create(x, y):
        # We use FigureCanvasBase directly and not as a method because some backends (for example the TkAgg) have
        # a different signature for this method
        FigureCanvasBase.button_press_event(axes.figure.canvas, x, y, button=1)

    return _create


@pytest.fixture
def create_button_release_event(axes):
    def _create(x, y):
        # We use FigureCanvasBase directly and not as a method because some backends (for example the TkAgg) have
        # a different signature for this method
        FigureCanvasBase.button_release_event(axes.figure.canvas, x, y, button=1)

    return _create


@pytest.fixture
def create_motion_notify_event(axes):
    def _create(x, y):
        # We use FigureCanvasBase directly and not as a method because some backends (for example the TkAgg) have
        # a different signature for this method
        FigureCanvasBase.motion_notify_event(axes.figure.canvas, x, y)

    return _create


@pytest.fixture
def create_key_press_and_release_event(axes):
    def _create(key):
        FigureCanvasBase.key_press_event(axes.figure.canvas, key)
        FigureCanvasBase.key_release_event(axes.figure.canvas, key)

    return _create


@pytest.fixture()
def get_axes_start(axes):
    def _get():
        x, y, *_ = axes.bbox.bounds
        return x + 1, y + 1

    return _get


@pytest.fixture()
def get_axes_end(axes):
    def _get():
        x, y, width, height = axes.bbox.bounds
        return x + width - 1, y + height - 1

    return _get


@pytest.fixture()
def get_axes_middle(axes):
    def _get():
        x, y, width, height = axes.bbox.bounds
        return x + width / 2, y + height / 2

    return _get

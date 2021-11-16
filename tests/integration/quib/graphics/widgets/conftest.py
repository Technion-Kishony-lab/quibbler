import pytest
from matplotlib.backend_bases import MouseEvent
from matplotlib.widgets import AxesWidget

from pyquibbler.performance_utils import track_class, TRACKED_CLASSES_TO_WEAKREFS


@pytest.fixture
def create_button_press_event(axes):
    def _create(x, y):
        axes.figure.canvas.button_press_event(
            x, y, button=1
        )
    return _create


@pytest.fixture
def create_button_release_event(axes):
    def _create(x, y):
        axes.figure.canvas.button_release_event(
            x, y, button=1
        )
    return _create


@pytest.fixture
def create_motion_notify_event(axes):
    def _create(x, y):
        axes.figure.canvas.motion_notify_event(
            x, y
        )
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
        return x + width / 2, y + height  / 2
    return _get


@pytest.fixture()
def get_only_live_widget(get_live_widgets):
    def _get():
        live = get_live_widgets()
        assert len(live) == 1
        return live[0]
    return _get


@pytest.fixture()
def get_live_widgets():
    track_class(AxesWidget)

    def _get():
        return [
            a() for a in TRACKED_CLASSES_TO_WEAKREFS.get(AxesWidget, [])
            if a() is not None
        ]

    yield _get

    TRACKED_CLASSES_TO_WEAKREFS[AxesWidget] = set()

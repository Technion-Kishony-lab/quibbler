import shutil
from functools import partial
from pathlib import Path

import pytest
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from pytest import fixture
import gc

from pyquibbler import CacheMode
from pyquibbler.env import DEBUG, LAZY, PRETTY_REPR, \
    SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS, GET_VARIABLE_NAMES, GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION, \
    ALLOW_ARRAY_WITH_DTYPE_OBJECT, SAFE_MODE
from pyquibbler.optional_packages.emulate_missing_packages import EMULATE_MISSING_PACKAGES
from pyquibbler.project import Project
from pyquibbler import initialize_quibbler
from pyquibbler.quib.func_calling import CachedQuibFuncCall
from pyquibbler.quib.graphics.redraw import is_dragging
from pyquibbler.user_utils.quibapp import QuibApp

from pyquibbler.utilities.basic_types import Flag

from matplotlib.widgets import Slider as OriginalSlider
from matplotlib.backend_bases import FigureCanvasBase, MouseEvent

from pyquibbler.debug_utils.track_instances import track_instances_of_class, TRACKED_CLASSES_TO_WEAKREFS, \
    get_all_instances_in_tracked_class


DEFAULT_EMULATE_MISSING_PACKAGES = []
DEFAULT_DEBUG = True
DEFAULT_ALLOW_ARRAY_WITH_DTYPE_OBJECT = False
DEFAULT_LAZY = True
DEFAULT_ASSIGNMENT_RESTRICTIONS = False
DEFAULT_PRETTY_REPR = True
DEFAULT_SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACK = False
DEFAULT_SAFE_MODE = False
DEFAULT_GET_VARIABLE_NAMES = False
DEFAULT_GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION = 1000


@pytest.fixture(autouse=True)
def check_reset_dragging():
    yield
    assert is_dragging() is False


@fixture(autouse=True, scope="session")
def setup_environment_for_tests():
    CachedQuibFuncCall.DEFAULT_CACHE_MODE = CacheMode.ON


@fixture(autouse=True, scope="session")
def setup_missing_packages(request):
    yield from setup_flag(EMULATE_MISSING_PACKAGES, DEFAULT_EMULATE_MISSING_PACKAGES, request)


@pytest.fixture(autouse=True, scope="session")
def initialize_quibbler_(setup_missing_packages):
    initialize_quibbler()


def pytest_configure(config):
    # register additional markers
    config.addinivalue_line("markers", "debug(on): mark test to run with or without debug mode")
    config.addinivalue_line("markers", "allow_array_with_dtype_object(on): mark test to run with or without ")
    config.addinivalue_line("markers", "evaluate_now(off): mark test to run with or without evaluate now mode")
    config.addinivalue_line("markers", "regression: mark test as regression test")
    config.addinivalue_line("markers", "assignment_restrictions(on): mark test to run with or without assignment "
                                       "restrictions mode")
    config.addinivalue_line("markers", "pretty_repr(on): mark test to run with or without pretty repr")
    config.addinivalue_line("markers", "get_variable_names(on): mark test to run with or without get variable name")
    config.addinivalue_line("markers", "graphics_driven_assignment_resolution(on): mark test to run with or without ")
    config.addinivalue_line("markers", "show_quib_exceptions_as_quib_traceback(True)(on): "
                                       "mark test to run with traceback")
    # Copied from matplotlib to disable warning
    config.addinivalue_line("markers", "style: Set alternate Matplotlib style temporarily (deprecated).")


def parametrize_flag_fixture(metafunc, name, fixture_name):
    markers = list(metafunc.definition.iter_markers(name=name))
    if markers:
        marker, = markers
        flag, = marker.args
        metafunc.parametrize(fixture_name, [flag], indirect=True, ids=[f'{name}={flag}'])


def pytest_generate_tests(metafunc):
    parametrize_flag_fixture(metafunc, 'debug', 'setup_debug')
    parametrize_flag_fixture(metafunc, 'allow_array_with_dtype_object', 'setup_allow_array_with_dtype_object')
    parametrize_flag_fixture(metafunc, 'evaluate', 'setup_evaluate_now')
    parametrize_flag_fixture(metafunc, 'assignment_restrictions', 'setup_assignment_restrictions')
    parametrize_flag_fixture(metafunc, 'pretty_repr', 'setup_pretty_repr')
    parametrize_flag_fixture(metafunc, 'get_variable_names', 'setup_get_variable_names')
    parametrize_flag_fixture(metafunc, 'graphics_driven_assignment_resolution', 'setup_graphics_driven_assignment_resolution')
    parametrize_flag_fixture(metafunc, 'show_quib_exceptions_as_quib_traceback', 'setup_show_quib_exceptions_as_quib_traceback')
    parametrize_flag_fixture(metafunc, 'safe_mode', 'setup_safe_mode')


def setup_flag(flag: Flag, default: bool, request):
    val = getattr(request, 'param', default)
    with flag.temporary_set(val):
        yield


@fixture(autouse=True)
def setup_allow_array_with_dtype_object(request):
    yield from setup_flag(ALLOW_ARRAY_WITH_DTYPE_OBJECT, DEFAULT_ALLOW_ARRAY_WITH_DTYPE_OBJECT, request)


@fixture(autouse=True)
def setup_debug(request):
    yield from setup_flag(DEBUG, DEFAULT_DEBUG, request)


@fixture(autouse=True)
def setup_evaluate_now(request):
    yield from setup_flag(LAZY, DEFAULT_LAZY, request)


@fixture(autouse=True)
def setup_pretty_repr(request):
    yield from setup_flag(PRETTY_REPR, DEFAULT_PRETTY_REPR, request)


@fixture(autouse=True)
def setup_show_quib_exceptions_as_quib_traceback(request):
    yield from setup_flag(SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS, DEFAULT_SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACK,
                          request)


@fixture(autouse=True)
def setup_safe_mode(request):
    yield from setup_flag(SAFE_MODE, DEFAULT_SAFE_MODE, request)


@fixture(autouse=True)
def setup_get_variable_names(request):
    yield from setup_flag(GET_VARIABLE_NAMES, DEFAULT_GET_VARIABLE_NAMES,
                          request)


@fixture(autouse=True)
def setup_graphics_driven_assignment_resolution(request):
    yield from setup_flag(GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION, DEFAULT_GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION,
                          request)


@fixture(scope='session', autouse=True)
def set_backend():
    import matplotlib
    # A backend that doesn't do anything. We use it because some tests failed in the TK backend because of tk bugs
    matplotlib.use("template")


@fixture
def axes():
    ax = get_axes()
    yield ax
    plt.close(ax.figure)  # Ensure the figure is closed after the test


def get_axes():
    plt.close('all')
    fig, ax = plt.subplots(figsize=(8, 6))
    return ax


@fixture(autouse=True)
def project(tmpdir):
    path = tmpdir.strpath
    yield Project.get_or_create(directory=Path(path))
    Project.current_project = None
    shutil.rmtree(path)


@fixture()
def quibapp_(tmpdir):
    app = QuibApp.get_or_create()
    yield app
    app.close()


@fixture()
def get_live_artists(axes):
    axes.figure.canvas.draw()
    track_instances_of_class(Artist)

    def _get():
        gc.collect()
        return list(get_all_instances_in_tracked_class(Artist))

    yield _get

    TRACKED_CLASSES_TO_WEAKREFS[Artist] = set()


@pytest.fixture
def original_slider():
    return OriginalSlider


"""
mouse events
"""


def convert_normalized_axes_xy_to_figure_xy(ax, xy):
    x0, y0, width, height = ax.bbox.bounds
    x_start, y_start = x0 + 1, y0 + 1
    x_end, y_end = x0 + width - 1, y0 + height - 1
    x, y = xy
    return (1 - x) * x_start + x * x_end, (1 - y) * y_start + y * y_end


def convert_axes_xy_to_normalized_xy(ax, xy):
    if isinstance(xy, str):
        return xy
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    xx = (xy[0] - xlim[0]) / (xlim[1] - xlim[0])
    yy = (xy[1] - ylim[0]) / (ylim[1] - ylim[0])
    return xx, yy


def convert_str_xy_to_normalized_xy(xy):
    if not isinstance(xy, str):
        return xy
    if xy == 'middle':
        return 0.5, 0.5
    if xy == 'left':
        return 0., 0.5
    if xy == 'right':
        return 1., 0.5


def simulate_event(canvas, name, x, y, button=1, ax=None):
    event = MouseEvent(name, canvas, x, y, button=button)

    event.inaxes = ax
    canvas.callbacks.process(name, event)


def create_mouse_press_move_release_events(ax, xys, button: int = 1,
                                           press: bool = True, release: bool = True, normalized: bool = False,
                                           pause: float = None):

    if not normalized:
        xys = [convert_axes_xy_to_normalized_xy(ax, xy) for xy in xys]

    xys = [convert_str_xy_to_normalized_xy(xy) for xy in xys]
    xys = [convert_normalized_axes_xy_to_figure_xy(ax, xy) for xy in xys]

    _xy_init = xys[0]
    _xy_end = xys[-1]

    # Use canvas directly for button press, motion notify, and button release events

    if press:
        simulate_event(ax.figure.canvas, 'button_press_event', _xy_init[0], _xy_init[1], button=button, ax=ax)
    for _xy in xys[1:]:
        simulate_event(ax.figure.canvas, 'motion_notify_event', _xy[0], _xy[1], ax=ax)
        if pause is not None:
            plt.pause(pause)
    if release:
        simulate_event(ax.figure.canvas, 'button_release_event', _xy_end[0], _xy_end[1], button=button, ax=ax)

@pytest.fixture
def create_axes_mouse_press_move_release_events(axes):
    return partial(create_mouse_press_move_release_events, axes)


def create_key_press_and_release_event(axes, key):
    canvas = axes.figure.canvas
    canvas.key_press_event(key)
    canvas.key_release_event(key)

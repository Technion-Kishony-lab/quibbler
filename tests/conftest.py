from pytest import fixture

from pyquibbler import CacheBehavior
from pyquibbler.env import set_debug, is_debug
from pyquibbler.quib import FunctionQuib

DEFAULT_DEBUG = True


@fixture(scope="session", autouse=True)
def setup_environment_for_tests():
    FunctionQuib._DEFAULT_CACHE_BEHAVIOR = CacheBehavior.ON


def pytest_configure(config):
    # register additional markers
    config.addinivalue_line("markers", "debug(on): mark test to run with or without debug mode")
    config.addinivalue_line("markers", "regression: mark test as regression test")
    # Copied from matplotlib to disable warning
    config.addinivalue_line("markers", "style: Set alternate Matplotlib style temporarily (deprecated).")


def pytest_generate_tests(metafunc):
    debug_markers = list(metafunc.definition.iter_markers(name='debug'))
    if debug_markers:
        marker, = debug_markers
        debug_on, = marker.args
        metafunc.parametrize('setup_debug', [debug_on], indirect=True, ids=[f'debug={debug_on}'])


@fixture(autouse=True)
def setup_debug(request):
    on = getattr(request, 'param', DEFAULT_DEBUG)
    current = is_debug()
    set_debug(on)
    yield
    set_debug(current)

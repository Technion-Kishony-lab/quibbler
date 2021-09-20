from unittest.mock import Mock

from pytest import fixture

from pyquibbler import CacheBehavior
from pyquibbler.env import set_debug, is_debug
from pyquibbler.quib import FunctionQuib

DEFAULT_DEBUG = True


@fixture(scope="session", autouse=True)
def setup_environment_for_tests():
    FunctionQuib.DEFAULT_CACHE_BEHAVIOR = CacheBehavior.ON


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "debug(on): mark test to run with or without debug mode"
    )


def pytest_generate_tests(metafunc):
    debug_markers = list(metafunc.definition.iter_markers(name='debug'))
    if debug_markers:
        marker, = debug_markers
        debug_on, = marker.args
        metafunc.parametrize('setup_debug', [debug_on])


@fixture(autouse=True)
def setup_debug(request):
    on = getattr(request, 'param', DEFAULT_DEBUG)
    current = is_debug()
    set_debug(on)
    yield
    set_debug(current)


@fixture
def function_mock_return_val():
    return object()


@fixture
def function_mock(function_mock_return_val):
    return Mock(return_value=function_mock_return_val)

from pytest import fixture

from pyquibbler import CacheBehavior, override_all
from pyquibbler.env import DEBUG, LAZY, ASSIGNMENT_RESTRICTIONS
from pyquibbler.quib import FunctionQuib
from pyquibbler.utils import Flag

DEFAULT_DEBUG = True
DEFAULT_LAZY = True
DEFAULT_ASSIGNMENT_RESTRICTIONS = False


@fixture(scope="session", autouse=True)
def setup_environment_for_tests():
    FunctionQuib._DEFAULT_CACHE_BEHAVIOR = CacheBehavior.ON
    override_all()


def pytest_configure(config):
    # register additional markers
    config.addinivalue_line("markers", "debug(on): mark test to run with or without debug mode")
    config.addinivalue_line("markers", "lazy(on): mark test to run with or without lazy mode")
    config.addinivalue_line("markers", "regression: mark test as regression test")
    config.addinivalue_line("markers", "assignment_restrictions(on): mark test to run with or without assignment "
                                       "restrictions mode")
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
    parametrize_flag_fixture(metafunc, 'lazy', 'setup_lazy')
    parametrize_flag_fixture(metafunc, 'assignment_restrictions', 'setup_assignment_restrictions')


def setup_flag(flag: Flag, default: bool, request):
    val = getattr(request, 'param', default)
    with flag.temporary_set(val):
        yield


@fixture(autouse=True)
def setup_debug(request):
    yield from setup_flag(DEBUG, DEFAULT_DEBUG, request)


@fixture(autouse=True)
def setup_lazy(request):
    yield from setup_flag(LAZY, DEFAULT_LAZY, request)


@fixture(autouse=True)
def setup_assignment_restrictions(request):
    yield from setup_flag(ASSIGNMENT_RESTRICTIONS, DEFAULT_ASSIGNMENT_RESTRICTIONS, request)

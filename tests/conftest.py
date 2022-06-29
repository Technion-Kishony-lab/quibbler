import shutil
from pathlib import Path

import pytest
from pytest import fixture

from pyquibbler import CacheMode
from pyquibbler.env import DEBUG, LAZY, ASSIGNMENT_RESTRICTIONS, PRETTY_REPR, \
    SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS, GET_VARIABLE_NAMES
from pyquibbler.project import Project
from pyquibbler.function_overriding import initialize_quibbler
from pyquibbler.quib.func_calling import CachedQuibFuncCall
from pyquibbler.utils import Flag

DEFAULT_DEBUG = True
DEFAULT_LAZY = True
DEFAULT_ASSIGNMENT_RESTRICTIONS = False
DEFAULT_PRETTY_REPR = True
DEFAULT_SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACK = False
DEFAULT_GET_VARIABLE_NAMES = False


@fixture(scope="session", autouse=True)
def setup_environment_for_tests():
    CachedQuibFuncCall.DEFAULT_CACHE_MODE = CacheMode.ON


@pytest.fixture(autouse=True, scope="session")
def initialize_quibbler_():
    initialize_quibbler()


def pytest_configure(config):
    # register additional markers
    config.addinivalue_line("markers", "debug(on): mark test to run with or without debug mode")
    config.addinivalue_line("markers", "evaluate_now(off): mark test to run with or without evaluate now mode")
    config.addinivalue_line("markers", "regression: mark test as regression test")
    config.addinivalue_line("markers", "assignment_restrictions(on): mark test to run with or without assignment "
                                       "restrictions mode")
    config.addinivalue_line("markers", "pretty_repr(on): mark test to run with or without pretty repr")
    config.addinivalue_line("markers", "get_variable_names(on): mark test to run with or without get variable name")
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
    parametrize_flag_fixture(metafunc, 'evaluate', 'setup_evaluate_now')
    parametrize_flag_fixture(metafunc, 'assignment_restrictions', 'setup_assignment_restrictions')
    parametrize_flag_fixture(metafunc, 'pretty_repr', 'setup_pretty_repr')
    parametrize_flag_fixture(metafunc, 'get_variable_names', 'setup_get_variable_names')
    parametrize_flag_fixture(metafunc, 'show_quib_exceptions_as_quib_traceback', 'setup_show_quib_exceptions_as_quib_traceback')


def setup_flag(flag: Flag, default: bool, request):
    val = getattr(request, 'param', default)
    with flag.temporary_set(val):
        yield


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
def setup_get_variable_names(request):
    yield from setup_flag(GET_VARIABLE_NAMES, DEFAULT_GET_VARIABLE_NAMES,
                          request)


@fixture(autouse=True)
def setup_assignment_restrictions(request):
    yield from setup_flag(ASSIGNMENT_RESTRICTIONS, DEFAULT_ASSIGNMENT_RESTRICTIONS, request)


@fixture(scope='session', autouse=True)
def set_backend():
    import matplotlib
    # A backend that doesn't do anything. We use it because some tests failed in the TK backend because of tk bugs
    matplotlib.use("template")


@fixture
def axes():
    from matplotlib import pyplot as plt
    plt.close("all")
    plt.gcf().set_size_inches(8, 6)
    return plt.gca()


@fixture(autouse=True)
def project(tmpdir):
    path = tmpdir.strpath
    yield Project.get_or_create(directory=Path(path))
    Project.current_project = None
    shutil.rmtree(path)

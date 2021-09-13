from pytest import fixture

from pyquibbler.env import set_debug


@fixture(scope="session", autouse=True)
def use_debug_for_tests():
    set_debug(True)

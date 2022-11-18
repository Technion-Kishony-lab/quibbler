import pytest

from pyquibbler.env import GRAPHICS_LAZY
from pyquibbler.function_overriding.third_party_overriding.matplotlib.helpers import graphics_override


@pytest.fixture(autouse=True)
def graphics_definition(mock_module, func_name_to_override, func_mock_on_module):
    definition = graphics_override(func_name=func_name_to_override, module_or_cls=mock_module)
    definition.override()
    return definition


def test_graphics_func_does_run_by_default(overridden_func, func_mock_on_module, quib):
    overridden_func(quib, )

    assert func_mock_on_module.call_count == 1


def test_graphics_func_does_not_run_when_lazy_flag_set_to_true(overridden_func, func_mock_on_module, quib):
    with GRAPHICS_LAZY.temporary_set(True):
        overridden_func(quib, )

    assert func_mock_on_module.call_count == 0

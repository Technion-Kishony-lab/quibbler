import pytest

from pyquibbler.env import EVALUATE_NOW
from pyquibbler.refactor.overriding.override_definition import OverrideDefinition


@pytest.fixture(autouse=True)
def override(mock_module, func_name_to_override, func_mock_on_module):
    def _override(**quib_creation_flags):
        definition = OverrideDefinition(func_name=func_name_to_override, module_or_cls=mock_module,
                                        quib_creation_flags=quib_creation_flags)
        definition.override()
        return definition
    return _override


def test_overriding_definition_does_not_call_func(overriden_func, func_mock_on_module, override, quib):
    override()
    overriden_func(quib)

    func_mock_on_module.assert_not_called()


def test_overriding_definition_does_call_func_when_set_to_evaluate_now(overriden_func, func_mock_on_module, override,
                                                                       quib):
    override(evaluate_now=True)
    overriden_func(quib)

    func_mock_on_module.assert_called_once()


def test_overriding_definition_does_call_func_when_no_quib_args(overriden_func, func_mock_on_module, override):
    override()
    overriden_func()

    func_mock_on_module.assert_called_once()


def test_overriding_definition_defaults_to_evaluate_now_when_flag_set_to_true(overriden_func,
                                                                              func_mock_on_module,
                                                                              override, quib):
    with EVALUATE_NOW.temporary_set(True):
        override()
        overriden_func(quib)

        func_mock_on_module.assert_called_once()

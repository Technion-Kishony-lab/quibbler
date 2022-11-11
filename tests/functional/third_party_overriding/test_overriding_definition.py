import pytest

from pyquibbler.env import LAZY
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_definitions.definitions import add_definition_for_function
from pyquibbler import list_quiby_funcs, is_quiby
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override_with_cls, override_class


@pytest.fixture(autouse=True)
def override(mock_module, func_name_to_override, func_mock_on_module):
    def _override(**quib_creation_flags):
        definition = override_with_cls(override_cls=FuncOverride,
                                       func_name=func_name_to_override, module_or_cls=mock_module,
                                       **quib_creation_flags)
        definition.override()
        return definition
    return _override


@pytest.fixture(autouse=True)
def add_definition(mock_module, func_name_to_override, func_mock_on_module, overridden_func):
    def _add_definition():
        definition = FuncOverride(func_name=func_name_to_override, module_or_cls=mock_module)
        add_definition_for_function(
            func=definition.original_func,
            func_definition=definition.func_definition,
            module_or_cls=definition.module_or_cls,
            func_name=definition.func_name,
            quib_creating_func=overridden_func,
        )
    return _add_definition


def test_overriding_definition_does_not_call_func(overridden_func, func_mock_on_module, override, quib):
    override()
    overridden_func(quib, )

    func_mock_on_module.assert_not_called()


def test_overriding_definition_does_call_func_when_set_to_lazy_false(overridden_func, func_mock_on_module, override,
                                                                     quib):
    override(lazy=False)
    overridden_func(quib, )

    func_mock_on_module.assert_called_once()


def test_overriding_definition_does_call_func_when_no_quib_args(overridden_func, func_mock_on_module, override):
    override()
    overridden_func()

    func_mock_on_module.assert_called_once()


def test_overriding_definition_defaults_to_evaluate_now_when_lazy_flag_set_to_false(overridden_func,
                                                                                    func_mock_on_module,
                                                                                    override, quib):
    with LAZY.temporary_set(False):
        override()
        overridden_func(quib, )

        func_mock_on_module.assert_called_once()


def test_overridden_function_in_list_quiby_funcs(overridden_func, func_mock_on_module, add_definition):
    add_definition()
    assert 'MockModule: hello_my_good_good_friend' in list_quiby_funcs()


def test_overridden_function_is_quiby(mock_module, func_name_to_override, override):
    assert not is_quiby(getattr(mock_module, func_name_to_override)), 'sanity'
    override()
    assert is_quiby(getattr(mock_module, func_name_to_override))


def test_overridden_class_is_quiby():
    class Mdl:
        class Cls: pass

    override = override_class(Mdl, 'Cls')
    assert not is_quiby(Mdl.Cls.__new__), 'sanity'
    assert not is_quiby(Mdl.Cls), 'sanity'
    override.override()
    assert is_quiby(Mdl.Cls.__new__)
    assert is_quiby(Mdl.Cls)

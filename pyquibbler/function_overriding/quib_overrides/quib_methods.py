from __future__ import annotations
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.translation.translators.elementwise.elementwise_translator import BackwardsElementwisePathTranslator, \
    ForwardsElementwisePathTranslator


def create_quib_method_overrides():
    from pyquibbler.quib import Quib
    from pyquibbler.function_definitions.func_definition import create_func_definition
    return [FuncOverride(func_name='get_override_mask', module_or_cls=Quib, quib_creation_flags=dict(
        call_func_with_quibs=True
    ), function_definition=create_func_definition(raw_data_source_arguments=[0],
                                                  backwards_path_translators=[BackwardsElementwisePathTranslator],
                                                  forwards_path_translators=[ForwardsElementwisePathTranslator]))]

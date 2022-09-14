from __future__ import annotations

from pyquibbler.quib.quib import Quib
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.translation.translators.elementwise.elementwise_translator import BackwardsElementwisePathTranslator, \
    ForwardsElementwisePathTranslator
from pyquibbler.quib.func_calling.quiby_name_func_call import QuibyNameFuncCall
from pyquibbler.translation.translators.quiby_name.quiby_name import BackwardsQuibyNameTranslator, \
    ForwardsQuibyNameTranslator

ORIGINAL_GET_QUIBY_NAME = Quib.get_quiby_name


def create_quib_method_overrides():
    from pyquibbler.quib.quib import Quib
    from pyquibbler.function_definitions.func_definition import create_func_definition
    return [FuncOverride(func_name='get_override_mask', module_or_cls=Quib,
                         func_definition=create_func_definition(
                             raw_data_source_arguments=[0],
                             pass_quibs=True,
                             backwards_path_translators=[BackwardsElementwisePathTranslator],
                             forwards_path_translators=[ForwardsElementwisePathTranslator])),

            FuncOverride(func_name='get_quiby_name', module_or_cls=Quib,
                         func_definition=create_func_definition(
                             quib_function_call_cls=QuibyNameFuncCall,
                             raw_data_source_arguments=[0],
                             pass_quibs=True,
                             backwards_path_translators=[BackwardsQuibyNameTranslator],
                             forwards_path_translators=[ForwardsQuibyNameTranslator])),
            ]

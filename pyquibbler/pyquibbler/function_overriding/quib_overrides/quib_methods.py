from __future__ import annotations

from pyquibbler.quib.quib import Quib
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.quib.func_calling.quiby_name_func_call import QuibyNameFuncCall
from pyquibbler.path_translation.translators.elementwise import UnaryElementwiseBackwardsPathTranslator, \
    UnaryElementwiseForwardsPathTranslator
from pyquibbler.path_translation.translators.quiby_name import QuibyNameBackwardsPathTranslator, \
    QuibyNameForwardsPathTranslator

ORIGINAL_GET_QUIBY_NAME = Quib.get_quiby_name


def create_quib_method_overrides():
    from pyquibbler.quib.quib import Quib
    from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition
    return [
        FuncOverride(func_name='get_override_mask', module_or_cls=Quib,
                     func_definition=create_or_reuse_func_definition(raw_data_source_arguments=[0], pass_quibs=True,
                                                                     backwards_path_translators=[
                                                                         UnaryElementwiseBackwardsPathTranslator],
                                                                     forwards_path_translators=[
                                                                         UnaryElementwiseForwardsPathTranslator])),

        FuncOverride(func_name='get_quiby_name', module_or_cls=Quib,
                     func_definition=create_or_reuse_func_definition(raw_data_source_arguments=[0], pass_quibs=True,
                                                                     backwards_path_translators=[
                                                                         QuibyNameBackwardsPathTranslator],
                                                                     forwards_path_translators=[
                                                                         QuibyNameForwardsPathTranslator],
                                                                     quib_function_call_cls=QuibyNameFuncCall,
                                                                     result_type_or_type_translators=str)),
    ]

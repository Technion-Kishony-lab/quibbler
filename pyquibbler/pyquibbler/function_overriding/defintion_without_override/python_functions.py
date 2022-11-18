# flake8: noqa

from __future__ import annotations
from typing import List, TYPE_CHECKING, Callable, Dict

from pyquibbler.inversion.inverters.transpositional import TranspositionalOneToOneInverter
from pyquibbler.path_translation.translators import TranspositionalBackwardsPathTranslator, TranspositionalForwardsPathTranslator
from pyquibbler.path_translation.translators.shape_only import \
    ShapeOnlyBackwardsPathTranslator, ShapeOnlyForwardsPathTranslator
from pyquibbler.inversion.inverters.casting import \
    StrCastingInverter, NumericCastingInverter, BoolCastingInverter

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition


def create_definitions_for_python_functions() -> Dict[Callable, FuncDefinition]:
    from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition
    return {
        # shape only:
        len: create_or_reuse_func_definition(raw_data_source_arguments=[0],
                                             backwards_path_translators=[ShapeOnlyBackwardsPathTranslator],
                                             forwards_path_translators=[ShapeOnlyForwardsPathTranslator],
                                             result_type_or_type_translators=int),

        # casting:
        **{func: create_or_reuse_func_definition(raw_data_source_arguments=[0], inverters=[inverter],
                                                 result_type_or_type_translators=func)
            for func, inverter in [
            (str,   StrCastingInverter),
            (int,   NumericCastingInverter),
            (float, NumericCastingInverter),
            (bool,  BoolCastingInverter),
        ]},

        # transpositional:
        **{func: create_or_reuse_func_definition(raw_data_source_arguments=[0],
                                                 inverters=[TranspositionalOneToOneInverter],
                                                 backwards_path_translators=[TranspositionalBackwardsPathTranslator],
                                                 forwards_path_translators=[TranspositionalForwardsPathTranslator],
                                                 result_type_or_type_translators=func)
             for func in [list, tuple]},

        # TODO: need definition for dict
    }

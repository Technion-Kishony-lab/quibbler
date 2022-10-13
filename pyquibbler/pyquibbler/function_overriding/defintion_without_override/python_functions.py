# flake8: noqa

from __future__ import annotations
from typing import List, TYPE_CHECKING

from pyquibbler.inversion.inverters.transpositional_inverter import TranspositionalOneToOneInverter
from pyquibbler.translation.translators import BackwardsTranspositionalTranslator, ForwardsTranspositionalTranslator
from pyquibbler.translation.translators.shape_only_translators import \
    BackwardsShapeOnlyPathTranslator, ForwardsShapeOnlyPathTranslator
from pyquibbler.inversion.inverters.casting_inverter import \
    StrCastingInverter, NumericCastingInverter, BoolCastingInverter

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition


def create_definitions_for_python_functions() -> List[FuncDefinition]:
    from pyquibbler.function_definitions.func_definition import create_func_definition
    return [
        create_func_definition(
            func=len,
            raw_data_source_arguments=[0],
            pre_known_result_type=int,
            backwards_path_translators=[BackwardsShapeOnlyPathTranslator],
            forwards_path_translators=[ForwardsShapeOnlyPathTranslator]),

        *(create_func_definition(
            func=func,
            raw_data_source_arguments=[0],
            pre_known_result_type=func,
            inverters=[inverter])
            for func, inverter in [

            (str,   StrCastingInverter),
            (int,   NumericCastingInverter),
            (float, NumericCastingInverter),
            (bool,  BoolCastingInverter),
        ]),

        *(create_func_definition(
            func=func,
            raw_data_source_arguments=[0],
            inverters=[TranspositionalOneToOneInverter],
            backwards_path_translators=[BackwardsTranspositionalTranslator],
            forwards_path_translators=[ForwardsTranspositionalTranslator],
            pre_known_result_type=func,
         )
             for func in [list, tuple]),

        # TODO: need definition for dict (to have fully functional obj2quib inversion and translation)
    ]

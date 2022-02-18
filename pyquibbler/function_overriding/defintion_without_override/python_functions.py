from __future__ import annotations
from typing import List, TYPE_CHECKING
from pyquibbler.translation.translators.shape_only.shape_only_translators import \
    BackwardsShapeOnlyPathTranslator, ForwardsShapeOnlyPathTranslator
from pyquibbler.inversion.inverters.str_inverter import StrInverter

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition


def create_defintions_for_python_functions() -> List[FuncDefinition]:
    from pyquibbler.function_definitions.func_definition import create_func_definition
    return [
        create_func_definition(
            func=len,
            raw_data_source_arguments=[0],
            backwards_path_translators=[BackwardsShapeOnlyPathTranslator],
            forwards_path_translators=[ForwardsShapeOnlyPathTranslator]),

        create_func_definition(
            func=str,
            raw_data_source_arguments=[0],
            inverters=[StrInverter],
            forwards_path_translators=[ForwardsShapeOnlyPathTranslator]),
    ]

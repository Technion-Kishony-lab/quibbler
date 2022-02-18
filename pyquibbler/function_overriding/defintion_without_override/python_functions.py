from __future__ import annotations
from typing import List, TYPE_CHECKING
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.translation.translators.shape_only.shape_only_translators import \
    BackwardsShapeOnlyPathTranslator, ForwardsShapeOnlyPathTranslator

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition


def create_defintions_for_python_functions() -> List[FuncDefinition]:
    from pyquibbler.function_definitions.func_definition import create_func_definition
    return [create_func_definition(
        func=len,
        raw_data_source_arguments=[0],
        backwards_path_translators=[BackwardsShapeOnlyPathTranslator],
        forwards_path_translators=[ForwardsShapeOnlyPathTranslator]
    )]

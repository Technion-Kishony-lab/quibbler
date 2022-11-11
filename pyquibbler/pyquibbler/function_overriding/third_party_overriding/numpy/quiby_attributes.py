from typing import Dict

import numpy as np

from pyquibbler.function_definitions import get_definition_for_function
from pyquibbler.function_definitions.func_definition import FuncDefinition

ATTRIBUTES_TO_FUNCS = {
    'T': np.transpose,
}


def get_numpy_attributes_to_definitions() -> Dict[str, FuncDefinition]:
    return {
        attribute: get_definition_for_function(func) for attribute, func in ATTRIBUTES_TO_FUNCS.items()
    }

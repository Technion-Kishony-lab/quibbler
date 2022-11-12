import numpy as np

from typing import Dict

from pyquibbler.function_definitions import get_definition_for_function
from pyquibbler.function_overriding.attribute_override import AttributeOverride, MethodOverride

ATTRIBUTES_TO_FUNCS = {
    'T': np.transpose,
    'imag': np.imag,
    'real': np.real,
    'ndim': np.ndim,
    'shape': np.shape,
    'size': np.size,
}


METHODS_TO_FUNCS = {
    'sum': np.sum,
    'flatten': np.ravel,
}


def get_numpy_attributes_to_attribute_overrides() -> Dict[str, AttributeOverride]:
    return {
        attribute: AttributeOverride(attribute=attribute,
                                     func_definition=get_definition_for_function(func))
        for attribute, func in ATTRIBUTES_TO_FUNCS.items()
    }


def get_numpy_methods_to_method_overrides() -> Dict[str, MethodOverride]:
    return {
        method: MethodOverride(attribute=method,
                               func_definition=get_definition_for_function(func))
        for method, func in METHODS_TO_FUNCS.items()
    }

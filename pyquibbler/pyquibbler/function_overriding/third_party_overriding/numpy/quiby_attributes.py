import numpy as np

from typing import Dict

from pyquibbler.function_definitions import get_definition_for_function
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.function_overriding.attribute_override import AttributeOverride, MethodOverride
from .func_definitions import FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE, FUNC_DEFINITION_SHAPE_ONLY, \
    FUNC_DEFINITION_REDUCTION

ATTRIBUTES_TO_FUNCS_OR_FUNC_DEFINITIONS = {
    'T': FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE,
    'imag': np.imag,
    'real': np.real,
    'ndim': FUNC_DEFINITION_SHAPE_ONLY,
    'shape': FUNC_DEFINITION_SHAPE_ONLY,
    'size': FUNC_DEFINITION_SHAPE_ONLY,
}

METHODS_TO_FUNCS_OR_FUNC_DEFINITIONS = {
    'sum': FUNC_DEFINITION_REDUCTION,
    'flatten': FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE,
    # 'all',
    # 'any',
    # 'argmax',
    # 'argmin',
    # 'argpartition',
    # 'argsort',
    # 'astype',
    # 'choose',
    # 'clip',
    # 'compress',
    # 'conj',
    # 'conjugate',
    # 'copy',
    # 'cumprod',
    # 'cumsum',
    # 'diagonal',
    # 'dump',
    # 'dumps',
    # 'fill',
    # 'flatten',
    # 'getfield',
    # 'item',
    # 'itemset',
    # 'max',
    # 'mean',
    # 'min',
    # 'newbyteorder',
    # 'nonzero',
    # 'partition',
    # 'prod',
    # 'ptp',
    # 'put',
    # 'ravel',
    # 'repeat',
    # 'reshape',
    # 'resize',
    # 'round',
    # 'searchsorted',
    # 'setfield',
    # 'setflags',
    # 'sort',
    # 'squeeze',
    # 'std',
    # 'sum',
    # 'swapaxes',
    # 'take',
    # 'tobytes',
    # 'tofile',
    # 'tolist',
    # 'tostring',
    # 'trace',
    # 'transpose',
    # 'var',
    # 'view',
}


def get_numpy_attributes_to_attribute_overrides() -> Dict[str, AttributeOverride]:
    return {
        attribute: AttributeOverride(
            attribute=attribute,
            func_definition=func if isinstance(func, FuncDefinition) else get_definition_for_function(func))
        for attribute, func in ATTRIBUTES_TO_FUNCS_OR_FUNC_DEFINITIONS.items()
    }


def get_numpy_methods_to_method_overrides() -> Dict[str, MethodOverride]:
    return {
        method: MethodOverride(
            attribute=method,
            func_definition=func if isinstance(func, FuncDefinition) else get_definition_for_function(func))
        for method, func in METHODS_TO_FUNCS_OR_FUNC_DEFINITIONS.items()
    }

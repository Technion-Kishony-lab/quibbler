import numpy as np

from typing import Dict, Union, Callable

from pyquibbler.function_definitions import get_definition_for_function
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.function_overriding.attribute_override import AttributeOverride, MethodOverride
from .func_definitions import FUNC_DEFINITION_ELEMENTWISE_IDENTITY

# quiby attributes to func or FuncDefinition.
#  `None` to get the function definition of the corresponding np function
ATTRIBUTES_TO_FUNCS_OR_FUNC_DEFINITIONS = {
    'T': np.transpose,
    'imag': None,
    'real': None,
    'ndim': None,
    'shape': None,
    'size': None,
}

# quiby methods to func or FuncDefinition
#  `None` to get the function definition of the corresponding np function
# list of methods compiled from https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html
METHODS_TO_FUNCS_OR_FUNC_DEFINITIONS = {
    'all': None,
    'any': None,
    'argmax': None,
    'argmin': None,
    # 'argpartition'
    # 'argsort'
    # 'astype'
    # 'choose',
    # 'clip',
    # 'compress',
    'conj': None,
    'conjugate': None,
    # 'copy',
    'cumprod': None,
    'cumsum': None,
    'diagonal': None,
    # 'dump',
    # 'dumps',
    # 'fill'  # NOT PURE
    'flatten': np.ravel,
    # 'getfield',
    # 'item',
    # 'itemset',
    'max': None,
    'mean': None,
    'min': None,
    # 'newbyteorder',
    'nonzero': None,
    # 'partition',
    'prod': None,
    'ptp': None,
    # 'put',  # NOT PURE
    'ravel': None,
    'repeat': None,
    'reshape': None,
    # 'resize'  # NOT PURE
    'round': None,
    # 'searchsorted',
    # 'setfield',  # NOT PURE
    # 'setflags',  # NOT PURE
    # 'sort',  # NOT PURE
    'squeeze': None,
    'std': None,
    'sum': None,
    'swapaxes': None,
    # 'take',
    # 'tobytes',
    # 'tofile',
    'tolist': FUNC_DEFINITION_ELEMENTWISE_IDENTITY,
    # 'tostring',
    'trace': None,
    'transpose': None,
    'var': None,
    # 'view',
}


def _get_func_definition(func_name: str, func_or_func_definition: Union[None, Callable, FuncDefinition]):
    if func_or_func_definition is None:
        func_or_func_definition = getattr(np, func_name)
    func_definition = func_or_func_definition if isinstance(func_or_func_definition, FuncDefinition) \
        else get_definition_for_function(func_or_func_definition, return_default=False)
    if func_definition is None:
        raise Exception(f'Definition for function `{func_name}` was not found')
    return func_definition


def get_numpy_attributes_to_attribute_overrides() -> Dict[str, AttributeOverride]:
    return {
        attribute: AttributeOverride(
            attribute=attribute,
            func_definition=_get_func_definition(attribute, func_or_func_definition))
        for attribute, func_or_func_definition in ATTRIBUTES_TO_FUNCS_OR_FUNC_DEFINITIONS.items()
    }


def get_numpy_methods_to_method_overrides() -> Dict[str, MethodOverride]:
    return {
        method: MethodOverride(
            attribute=method,
            func_definition=_get_func_definition(method, func_or_func_definition))
        for method, func_or_func_definition in METHODS_TO_FUNCS_OR_FUNC_DEFINITIONS.items()
    }

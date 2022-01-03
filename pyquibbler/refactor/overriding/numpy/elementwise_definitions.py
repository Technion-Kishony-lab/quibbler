from __future__ import annotations

import operator
from inspect import signature
from operator import __truediv__, __sub__, __mul__, __add__
from typing import Any, TYPE_CHECKING, Dict, Callable, List

import numpy as np
from numpy.core import ufunc

from pyquibbler.refactor.overriding.numpy.numpy_definition import numpy_definition
from pyquibbler.refactor.overriding.override_definition import OverrideDefinition
from pyquibbler.refactor.translation.translators import BackwardsTranspositionalTranslator
from pyquibbler.refactor.translation.translators.elementwise.elementwise_translator import \
    ForwardsElementwisePathTranslator

if TYPE_CHECKING:
    from pyquibbler.refactor.translation.types import Source


def create_inverse_func_from_indexes_to_funcs(data_source_argument_indexes_to_inverse_functions: Dict[int, Callable]):
    """
    Create an inverse function that will call actual inverse functions based on the index of the quib in the arguments
    """

    def _inverse(representative_result: Any, args, kwargs, source_to_change: Source, relevant_path_in_quib):
        source_index = next(i for i, v in enumerate(args) if v is source_to_change)
        inverse_func = data_source_argument_indexes_to_inverse_functions[source_index]
        new_args = list(args)
        new_args.pop(source_index)
        from pyquibbler.refactor.translation.utils import call_func_with_sources_values
        return call_func_with_sources_values(inverse_func, [representative_result, *new_args], kwargs)

    return _inverse


identity = lambda x: x
pi = np.pi

# We use indexes instead of arg names because you cannot get signature from ufuncs (numpy functions)
FUNCTIONS_TO_INVERSE_FUNCTIONS = {
    **{
        func: create_inverse_func_from_indexes_to_funcs(
            {
                0: np.subtract,
                1: np.subtract
            }
        ) for func in [np.add, __add__]},
    **{
        func: create_inverse_func_from_indexes_to_funcs(
            {
                0: np.divide,
                1: np.divide
            }
        ) for func in [np.multiply, __mul__]},
    **{
        func: create_inverse_func_from_indexes_to_funcs(
            {
                0: np.add,
                1: lambda result, other: np.subtract(other, result)
            }
        ) for func in [np.subtract, __sub__]},
    **{
        func: create_inverse_func_from_indexes_to_funcs(
            {
                0: np.multiply,
                1: lambda result, other: np.divide(other, result)
            }
        ) for func in [np.divide, __truediv__]},
}


def elementwise(func, reverse_func: Callable):
    from pyquibbler.refactor.translation.translators.elementwise.elementwise_translator import \
        BackwardsElementwisePathTranslator
    if isinstance(func, ufunc):
        data_source_arguments = list(range(func.nin))
        return numpy_definition(func,
                                data_source_arguments,
                                backwards_path_translators=[BackwardsElementwisePathTranslator],
                                forwards_path_translators=[ForwardsElementwisePathTranslator]
                                )
    else:
        data_source_arguments = list(signature(func).parameters)
        return OverrideDefinition.from_func(
            module_or_cls=operator,
            func=func,
            data_source_arguments=set(data_source_arguments),
            backwards_path_translators=[BackwardsElementwisePathTranslator],
            forwards_path_translators=[ForwardsElementwisePathTranslator]
        )


def create_elementwise_definitions():
    return [
        elementwise(func, inverse_function)
        for func, inverse_function in FUNCTIONS_TO_INVERSE_FUNCTIONS.items()
    ]

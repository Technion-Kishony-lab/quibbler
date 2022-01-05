from __future__ import annotations

import functools
import math
from inspect import signature
from typing import Callable, List, Union

import numpy as np
from numpy.core import ufunc

from pyquibbler.refactor.function_definitions.function_definition import create_function_definition
from pyquibbler.refactor.function_overriding.function_override import FunctionOverride
from pyquibbler.refactor.translation.translators.elementwise.elementwise_translator import \
    ForwardsElementwisePathTranslator
from pyquibbler.refactor.translation.translators.elementwise.generic_inverse_functions import \
    create_inverse_func_from_indexes_to_funcs, create_inverse_single_arg_many_to_one, create_inverse_single_arg_func

FUNCS_TO_INVERTERS = {}


@functools.lru_cache()
def get_inverter_for_func(func: Callable):
    return FUNCS_TO_INVERTERS[func]


def elementwise(func: Callable,
                inverse_func: Callable = None,
                data_source_arguments: List[Union[str, int]] = None,
                module_or_cls=np):
    """
    Create an elementwise override together with it's function definition
    """
    from pyquibbler.refactor.translation.translators.elementwise.elementwise_translator import \
        BackwardsElementwisePathTranslator
    from pyquibbler.refactor.inversion.inverters.elementwise_inverter import ElementwiseInverter
    if inverse_func:
        FUNCS_TO_INVERTERS[func] = functools.partial(ElementwiseInverter, inverse_func=inverse_func)

    if data_source_arguments is None:
        # Our default is to consider all arguments data sources for elementwise functions- if this is not true for your
        # particular case, specify data_source_arguments
        if isinstance(func, ufunc):
            data_source_arguments = list(range(func.nin))
        else:
            data_source_arguments = list(signature(func).parameters)

    return FunctionOverride.from_func(
        module_or_cls=module_or_cls,
        func=func,
        function_definition=create_function_definition(
            data_source_arguments=data_source_arguments,
            backwards_path_translators=[BackwardsElementwisePathTranslator],
            forwards_path_translators=[ForwardsElementwisePathTranslator],
            inverters=[FUNCS_TO_INVERTERS[func]] if inverse_func else []
        )
    )


def single_arg(func, inverse_func, module_or_cls=np):
    return elementwise(func=func,
                       inverse_func=create_inverse_single_arg_func(inverse_func),
                       data_source_arguments=[0],
                       module_or_cls=module_or_cls)


def single_arg_many_to_one(func, invfunc_period_tuple):
    return elementwise(func=func,
                       inverse_func=create_inverse_single_arg_many_to_one(invfunc_period_tuple),
                       data_source_arguments=[0])


identity = lambda x: x
pi = np.pi


def create_elementwise_overrides():
    multi_arg_funcs = [
        elementwise(np.add, create_inverse_func_from_indexes_to_funcs(
            {
                0: np.subtract,
                1: np.subtract
            }
        )),
        elementwise(np.subtract,  create_inverse_func_from_indexes_to_funcs({
            0: np.add,
            1: lambda result, other: np.subtract(other, result)
        })),
        elementwise(np.divide, create_inverse_func_from_indexes_to_funcs(
            {
                0: np.multiply,
                1: lambda result, other: np.divide(other, result)
            }
        )),
        elementwise(np.multiply, create_inverse_func_from_indexes_to_funcs({
            0: np.divide,
            1: np.divide
        })),
        elementwise(np.power, create_inverse_func_from_indexes_to_funcs({
            0: lambda x, n: x ** (1 / n),
            1: lambda result, other: math.log(result, other)
        }))
    ]

    single_arg_funcs = [
        single_arg(np.sqrt, np.square),
        single_arg(np.arcsin, np.sin),
        single_arg(np.arccos, np.cos),
        single_arg(np.arctan, np.tan),
        single_arg(np.arcsinh, np.sinh),
        single_arg(np.arccosh, np.cosh),
        single_arg(np.arctanh, np.tanh),
        single_arg(np.ceil, identity),
        single_arg(np.floor, identity),
        single_arg(np.round, identity),
        single_arg(np.exp, np.log),
        single_arg(np.exp2, np.log2),
        single_arg(np.expm1, np.log1p),
        single_arg(np.log, np.exp),
        single_arg(np.log2, np.exp2),
        single_arg(np.log1p, np.expm1),
        single_arg(np.log10, lambda x: 10 ** x),
        single_arg(np.int, identity),
        single_arg(np.float, identity),
    ]

    single_arg_many_to_one_funcs = [
        single_arg_many_to_one(np.sin, ((np.arcsin, 2 * pi), (lambda x: -np.arcsin(x) + np.pi, 2 * pi))),
        single_arg_many_to_one(np.cos, ((np.arccos, 2 * pi), (lambda x: -np.arccos(x), 2 * pi))),
        single_arg_many_to_one(np.tan, ((np.arctan, pi),)),
        single_arg_many_to_one(np.sinh, ((np.arcsinh, None),)),
        single_arg_many_to_one(np.cosh, ((np.arccosh, None), (lambda x: -np.arccosh(x), None))),
        single_arg_many_to_one(np.tanh, ((np.arctanh, None),)),
        single_arg_many_to_one(np.square, ((np.sqrt, None), (lambda x: -np.sqrt(x), None))),
        single_arg_many_to_one(np.abs, ((identity, None), (lambda x: -x, None))),
    ]

    rounding_funcs = [
        elementwise(func, data_source_arguments=[0])
        for func in [np.around, np.ceil, np.round, np.rint]
    ]

    return [
        *multi_arg_funcs,
        *single_arg_funcs,
        *single_arg_many_to_one_funcs,
        *rounding_funcs
    ]

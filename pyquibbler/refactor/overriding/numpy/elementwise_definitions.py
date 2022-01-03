from __future__ import annotations

import functools
import math
import operator
from inspect import signature
from operator import __truediv__, __sub__, __mul__, __add__, __neg__, __pos__
from typing import Any, TYPE_CHECKING, Dict, Callable, List, Tuple

import numpy as np
from numpy.core import ufunc

from pyquibbler.refactor.inversion.inverters.elementwise_inverter import ElementwiseInverter
from pyquibbler.refactor.overriding.numpy.numpy_definition import numpy_definition
from pyquibbler.refactor.overriding.override_definition import OverrideDefinition
from pyquibbler.refactor.translation.translators import BackwardsTranspositionalTranslator
from pyquibbler.refactor.translation.translators.elementwise.elementwise_translator import \
    ForwardsElementwisePathTranslator
from pyquibbler.refactor.translation.translators.elementwise.generic_inverse_functions import \
    create_inverse_func_from_indexes_to_funcs, create_inverse_single_arg_many_to_one, create_inverse_single_arg_func
from pyquibbler.refactor.translation.utils import call_func_with_sources_values


@functools.lru_cache()
def get_inverter_for_inverse_func(inverse_func: Callable):
    return functools.partial(ElementwiseInverter, inverse_func=inverse_func)


identity = lambda x: x
pi = np.pi


def elementwise(func, inverse_func: Callable, data_source_arguments=None, module_or_cls=np):
    from pyquibbler.refactor.translation.translators.elementwise.elementwise_translator import \
        BackwardsElementwisePathTranslator
    if data_source_arguments is None:
        if isinstance(func, ufunc):
            data_source_arguments = list(range(func.nin))
        else:
            data_source_arguments = list(signature(func).parameters)
            
    return OverrideDefinition.from_func(
        module_or_cls=module_or_cls,
        func=func,
        data_source_arguments=set(data_source_arguments),
        backwards_path_translators=[BackwardsElementwisePathTranslator],
        forwards_path_translators=[ForwardsElementwisePathTranslator],
        inverters=[get_inverter_for_inverse_func(inverse_func)]
    )


el = elementwise


def single_arg(func, inverse_func, module_or_cls=np):
    return elementwise(func=func,
                       inverse_func=create_inverse_single_arg_func(inverse_func),
                       data_source_arguments=[0],
                       module_or_cls=module_or_cls)


def single_arg_many_to_one(func, invfunc_period_tuple):
    return elementwise(func=func,
                       inverse_func=create_inverse_single_arg_many_to_one(invfunc_period_tuple),
                       data_source_arguments=[0])


add_inverse_func = create_inverse_func_from_indexes_to_funcs(
                {
                    0: np.subtract,
                    1: np.subtract
                }
            )

sub_inverse_func = create_inverse_func_from_indexes_to_funcs(
    {
        0: np.add,
        1: lambda result, other: np.subtract(other, result)
    })

mul_inverse_func = create_inverse_func_from_indexes_to_funcs(
            {
                0: np.divide,
                1: np.divide
            }
        )


div_inverse_func = create_inverse_func_from_indexes_to_funcs(
            {
                0: np.multiply,
                1: lambda result, other: np.divide(other, result)
            }
        )

pow_inverse_func = create_inverse_func_from_indexes_to_funcs({
    0: lambda x, n: x ** (1 / n),
    1: lambda result, other: math.log(result, other)
})


def create_elementwise_definitions():

    multi_arg_funcs = [
        el(np.add, add_inverse_func),
        el(np.subtract, sub_inverse_func),
        el(np.divide, div_inverse_func),
        el(np.multiply, mul_inverse_func),
        el(np.power, pow_inverse_func)
   ]

    single_arg_funcs = [
            # single_arg(__neg__, __neg__, module_or_cls=operator),
            # single_arg(__pos__, __pos__, module_or_cls=operator),
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
    return [
        *multi_arg_funcs,
        *single_arg_funcs,
        *single_arg_many_to_one_funcs,
    ]

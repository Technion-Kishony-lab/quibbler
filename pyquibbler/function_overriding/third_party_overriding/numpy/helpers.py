import functools
from typing import List, Callable

import numpy as np

from pyquibbler.function_overriding.third_party_overriding.general_helpers import RawArgument, override
from pyquibbler.inversion import TranspositionalInverter
from pyquibbler.translation.translators import ForwardsTranspositionalTranslator, BackwardsTranspositionalTranslator, \
    AccumulationBackwardsPathTranslator, AccumulationForwardsPathTranslator, ReductionAxiswiseBackwardsPathTranslator, \
    ReductionAxiswiseForwardsPathTranslator


numpy_override = functools.partial(override, np)

transpositional = functools.partial(numpy_override, inverters=[TranspositionalInverter],
                                    backwards_path_translators=[BackwardsTranspositionalTranslator],
                                    forwards_path_translators=[ForwardsTranspositionalTranslator])

accumulation = functools.partial(numpy_override, data_source_arguments=[0],
                                 backwards_path_translators=[AccumulationBackwardsPathTranslator],
                                 forwards_path_translators=[AccumulationForwardsPathTranslator])

reduction = functools.partial(numpy_override, data_source_arguments=[0],
                              backwards_path_translators=[ReductionAxiswiseBackwardsPathTranslator],
                              forwards_path_translators=[ReductionAxiswiseForwardsPathTranslator])


ELEMENTWISE_FUNCS_TO_INVERTERS = {}


@functools.lru_cache()
def get_inverter_for_func(func_name: str):
    return ELEMENTWISE_FUNCS_TO_INVERTERS[func_name]


def elementwise(func_name: str, data_source_arguments: List[RawArgument], inverse_func: Callable = None):
    from pyquibbler.translation.translators.elementwise.elementwise_translator import \
        BackwardsElementwisePathTranslator
    from pyquibbler.translation.translators.elementwise.elementwise_translator import ForwardsElementwisePathTranslator
    from pyquibbler.inversion.inverters.elementwise_inverter import ElementwiseInverter
    from pyquibbler.inversion.inverters.elementwise_single_arg_no_shape_inverter import ElementwiseNoShapeInverter

    if inverse_func:
        ELEMENTWISE_FUNCS_TO_INVERTERS[func_name] = [
            functools.partial(ElementwiseNoShapeInverter, inverse_func=inverse_func),
            functools.partial(ElementwiseInverter, inverse_func=inverse_func)
        ]

    return numpy_override(
        func_name=func_name,
        data_source_arguments=data_source_arguments,
        backwards_path_translators=[BackwardsElementwisePathTranslator],
        forwards_path_translators=[ForwardsElementwisePathTranslator],
        inverters=ELEMENTWISE_FUNCS_TO_INVERTERS[func_name] if inverse_func else []
    )


def single_arg_elementwise(func_name: str, inverse_func: Callable):
    from pyquibbler.translation.translators.elementwise.generic_inverse_functions import create_inverse_single_arg_func
    return elementwise(func_name, inverse_func=create_inverse_single_arg_func(inverse_func),
                       data_source_arguments=[0])


def many_to_one_elementwise(func_name: str, invfunc_period_tuple):
    from pyquibbler.translation.translators.elementwise.generic_inverse_functions import \
        create_inverse_single_arg_many_to_one
    return elementwise(func_name=func_name,
                       inverse_func=create_inverse_single_arg_many_to_one(invfunc_period_tuple),
                       data_source_arguments=[0])

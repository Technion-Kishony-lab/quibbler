import functools
from typing import List, Callable, Tuple, Union, Optional, Dict

import numpy as np

from pyquibbler.function_overriding.third_party_overriding.general_helpers import RawArgument, override
from pyquibbler.inversion import TranspositionalInverter
from pyquibbler.translation.translators import ForwardsTranspositionalTranslator, BackwardsTranspositionalTranslator, \
    AccumulationBackwardsPathTranslator, AccumulationForwardsPathTranslator, ReductionAxiswiseBackwardsPathTranslator, \
    ReductionAxiswiseForwardsPathTranslator
from pyquibbler.inversion.inverters.elementwise_inverter import ElementwiseInverter
from pyquibbler.inversion.inverters.elementwise_single_arg_no_shape_inverter import ElementwiseNoShapeInverter

numpy_override = functools.partial(override, np)

numpy_override_random = functools.partial(override, np.random, is_random_func=True)

numpy_override_read_file = functools.partial(numpy_override, is_file_loading_func=True)

numpy_override_transpositional = functools.partial(numpy_override, inverters=[TranspositionalInverter],
                                                   backwards_path_translators=[BackwardsTranspositionalTranslator],
                                                   forwards_path_translators=[ForwardsTranspositionalTranslator])

numpy_override_accumulation = functools.partial(numpy_override, data_source_arguments=[0],
                                                backwards_path_translators=[AccumulationBackwardsPathTranslator],
                                                forwards_path_translators=[AccumulationForwardsPathTranslator])

numpy_override_reduction = functools.partial(numpy_override, data_source_arguments=[0],
                                             backwards_path_translators=[ReductionAxiswiseBackwardsPathTranslator],
                                             forwards_path_translators=[ReductionAxiswiseForwardsPathTranslator])

ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS = {}

ELEMENTWISE_INVERTERS = [ElementwiseNoShapeInverter, ElementwiseInverter]


@functools.lru_cache()
def get_inverse_funcs_for_func(func_name: str):
    return ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name]


def elementwise(func_name: str, data_source_arguments: List[RawArgument],
                inverse_func_with_input: Union[None, Callable, Dict] = None,
                inverse_func_without_input: Union[None, Callable, Dict] = None):
    from pyquibbler.translation.translators.elementwise.elementwise_translator import \
        BackwardsElementwisePathTranslator
    from pyquibbler.translation.translators.elementwise.elementwise_translator import ForwardsElementwisePathTranslator
    from pyquibbler.inversion.inverters.elementwise_inverter import ElementwiseInverter
    from pyquibbler.inversion.inverters.elementwise_single_arg_no_shape_inverter import ElementwiseNoShapeInverter

    is_inverse = inverse_func_with_input or inverse_func_without_input
    if is_inverse:
        ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name] = (inverse_func_with_input, inverse_func_without_input)

    return numpy_override(
        func_name=func_name,
        data_source_arguments=data_source_arguments,
        backwards_path_translators=[BackwardsElementwisePathTranslator],
        forwards_path_translators=[ForwardsElementwisePathTranslator],
        inverters=ELEMENTWISE_INVERTERS if is_inverse else [],
        inverse_funcs=(inverse_func_with_input, inverse_func_without_input),
    )


def single_arg_elementwise(func_name: str,
                           inverse_func: Union[None, Callable, Tuple[Union[Optional[Callable]]]]):
    if inverse_func is None:
        inverse_func = (None, None)
    if not isinstance(inverse_func, tuple):
        inverse_func = (inverse_func, None)
    inverse_func_without_input, inverse_func_with_input = inverse_func
    return elementwise(
        func_name,
        data_source_arguments=[0],
        inverse_func_with_input=inverse_func_with_input,
        inverse_func_without_input=inverse_func_without_input,
    )

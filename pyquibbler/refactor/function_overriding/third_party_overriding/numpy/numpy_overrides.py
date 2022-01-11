from typing import List

import numpy as np

from pyquibbler.refactor.function_definitions.function_definition import create_function_definition
from pyquibbler.refactor.function_overriding.function_override import FunctionOverride
from pyquibbler.refactor.function_overriding.third_party_overriding.numpy.elementwise_overrides import \
    create_elementwise_overrides
from pyquibbler.refactor.function_overriding.third_party_overriding.numpy.vectorize_overrides import \
    create_vectorize_overrides
from pyquibbler.refactor.inversion import TranspositionalInverter
from pyquibbler.refactor.function_overriding.third_party_overriding.numpy.numpy_override import numpy_override
from pyquibbler.refactor.quib.function_running.function_runners.apply_along_axis_function_runner import ApplyAlongAxisFunctionRunner
from pyquibbler.refactor.translation.translators import BackwardsTranspositionalTranslator, \
    ForwardsTranspositionalTranslator, AccumulationBackwardsPathTranslator, AccumulationForwardsPathTranslator
from pyquibbler.refactor.translation.translators.apply_along_axis_translator import ApplyAlongAxisForwardsTranslator
from pyquibbler.refactor.translation.translators.axeswise.reduction_axiswise_translator import \
    ReductionAxiswiseBackwardsPathTranslator, ReductionAxiswiseForwardsPathTranslator


def transpositional(func, data_source_arguments: List = None):
    return numpy_override(func,
                          function_definition=create_function_definition(
                              data_source_arguments,
                              inverters=[TranspositionalInverter],
                              backwards_path_translators=[BackwardsTranspositionalTranslator],
                              forwards_path_translators=[ForwardsTranspositionalTranslator])
                          )


def create_transpositional_overrides():
    return [
        transpositional(np.rot90, data_source_arguments=['m']),
        transpositional(np.concatenate, data_source_arguments=[0]),
        transpositional(np.repeat, data_source_arguments=['a']),
        transpositional(np.full, data_source_arguments=['fill_value']),
        transpositional(np.reshape, data_source_arguments=['a']),
        transpositional(np.transpose, data_source_arguments=[0]),
        transpositional(np.array, data_source_arguments=[0]),
        transpositional(np.tile, data_source_arguments=[0]),
        transpositional(np.asarray, data_source_arguments=[0]),
        transpositional(np.squeeze, data_source_arguments=[0]),
        transpositional(np.expand_dims, data_source_arguments=[0]),
        transpositional(np.ravel, data_source_arguments=[0]),
        transpositional(np.squeeze, data_source_arguments=[0]),
    ]


def create_reduction_overrides():
    reduction_funcs = [np.amin, np.max, np.amax,  # min/max
                       np.argmin, np.argmax, np.nanargmin, np.nanargmax,  # arg-min/max
                       np.sum, np.prod, np.nanprod, np.nansum,  # sum/prod
                       np.any, np.all,  # logical
                       np.average, np.mean, np.var, np.std, np.median,  # statistics
                       np.diff, np.sort  # other
                       ]
    reduction_definition = create_function_definition(
        data_source_arguments=[0],
        backwards_path_translators=[ReductionAxiswiseBackwardsPathTranslator],
        forwards_path_translators=[ReductionAxiswiseForwardsPathTranslator]
    )
    return [
        numpy_override(reduction_func, function_definition=reduction_definition)
        for reduction_func in reduction_funcs
    ] + [FunctionOverride(func_name='min', module_or_cls=np, function_definition=reduction_definition)]


def create_accum_overrides():
    accum_funcs = [
        "cumsum", "cumprod", 'cumproduct', 'nancumsum', 'nancumprod'
    ]
    accum_definition = create_function_definition(
        data_source_arguments=[0],
        backwards_path_translators=[AccumulationBackwardsPathTranslator],
        forwards_path_translators=[AccumulationForwardsPathTranslator]
    )
    return [
               FunctionOverride(func_name=accum_func, module_or_cls=np, function_definition=accum_definition)
               for accum_func in accum_funcs
           ]


def create_numpy_overrides():

    default_behavior_numpy_overrides = [
        numpy_override(func) for func in
        [np.arange, np.polyfit, np.interp, np.linspace, np.polyval, np.corrcoef]
    ]

    return [
        *default_behavior_numpy_overrides,
        *create_transpositional_overrides(),
        *create_elementwise_overrides(),
        *create_reduction_overrides(),
        *create_accum_overrides(),
        numpy_override(np.sum, function_definition=create_function_definition(data_source_arguments=[0])),
        numpy_override(np.genfromtxt, function_definition=create_function_definition(is_file_loading_func=True)),
        numpy_override(np.apply_along_axis,
                       function_definition=create_function_definition(
                           data_source_arguments=["arr"],
                           forwards_path_translators=[ApplyAlongAxisForwardsTranslator],
                           function_runner_cls=ApplyAlongAxisFunctionRunner)
                       ),
        *create_vectorize_overrides()
    ]

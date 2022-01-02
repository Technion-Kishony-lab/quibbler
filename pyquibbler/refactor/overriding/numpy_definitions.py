import functools
from typing import List

import numpy as np

from pyquibbler.refactor.inversion import TranspositionalInverter
from pyquibbler.refactor.overriding.override_definition import OverrideDefinition
from pyquibbler.refactor.quib.function_runners.apply_along_axis_function_runner import ApplyAlongAxisFunctionRunner
from pyquibbler.refactor.translation.translators import BackwardsTranspositionalTranslator, ForwardsTranspositionalTranslator
from pyquibbler.refactor.translation.translators.axeswise.apply_along_axis_translator import \
    ApplyAlongAxisForwardsTranslator

numpy_definition = functools.partial(OverrideDefinition.from_func, module_or_cls=np)


def transpositional(func, data_source_arguments: List = None):
    return numpy_definition(func, data_source_arguments,
                            inverters=[TranspositionalInverter],
                            backwards_path_translators=[BackwardsTranspositionalTranslator],
                            forwards_path_translators=[ForwardsTranspositionalTranslator])


def create_numpy_definitions():
    return [
        transpositional(np.rot90, data_source_arguments=['m']),
        transpositional(np.concatenate, data_source_arguments=[0]),
        transpositional(np.repeat, data_source_arguments=['a']),
        transpositional(np.full, data_source_arguments=['fill_value']),
        transpositional(np.reshape, data_source_arguments=['a']),
        transpositional(np.transpose, data_source_arguments=[0]),
        transpositional(np.array, data_source_arguments=[0]),
        numpy_definition(np.sum, data_source_arguments=[0]),
        numpy_definition(np.apply_along_axis,
                         data_source_arguments=["arr"],
                         forwards_path_translators=[ApplyAlongAxisForwardsTranslator],
                         function_runner_cls=ApplyAlongAxisFunctionRunner)
    ]

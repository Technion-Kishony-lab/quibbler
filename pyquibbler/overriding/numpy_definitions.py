from typing import Callable, Set, List

import numpy as np

from pyquibbler.overriding.definitions import OverrideDefinition
from pyquibbler.overriding.types import Argument, KeywordArgument, IndexArgument


def numpy_definition(func, data_source_arguments: List = None):
    return OverrideDefinition.from_func(func=func, module_or_cls=np, data_source_arguments=data_source_arguments)


NUMPY_DEFINITIONS = [
    numpy_definition(np.rot90, data_source_arguments=['m']),
    numpy_definition(np.concatenate, data_source_arguments=[0]),
    numpy_definition(np.repeat, data_source_arguments=['a']),
    numpy_definition(np.full, data_source_arguments=['fill_value']),
    numpy_definition(np.reshape, data_source_arguments=['a']),
    numpy_definition(np.array, data_source_arguments=[0]),
]

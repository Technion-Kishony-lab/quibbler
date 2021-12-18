from typing import Callable, Set, List

import numpy as np

from pyquibbler.inversion import TranspositionalInverter
from pyquibbler.overriding.definitions import OverrideDefinition
from pyquibbler.overriding.types import Argument, KeywordArgument, IndexArgument
from pyquibbler.translation.translators import BackwardsTranspositionalTranslator


def numpy_definition(func, data_source_arguments: List = None, inverters=None,
                     backwards_path_translators: List = None):
    return OverrideDefinition.from_func(func=func,
                                        module_or_cls=np,
                                        data_source_arguments=data_source_arguments,
                                        inverters=inverters,
                                        backwards_path_translators=backwards_path_translators)


def transpositional(func, data_source_arguments: List = None):
    return numpy_definition(func, data_source_arguments,
                            inverters=[TranspositionalInverter],
                            backwards_path_translators=[BackwardsTranspositionalTranslator])


ct_fun = transpositional(np.concatenate, data_source_arguments=[0])
ct_fun.help = 1

NUMPY_DEFINITIONS = [
    transpositional(np.rot90, data_source_arguments=['m']),
    numpy_definition(np.concatenate, data_source_arguments=[0],
                     inverters=[TranspositionalInverter],
                     backwards_path_translators=[BackwardsTranspositionalTranslator]),
    transpositional(np.repeat, data_source_arguments=['a']),
    transpositional(np.full, data_source_arguments=['fill_value']),
    transpositional(np.reshape, data_source_arguments=['a']),
    transpositional(np.array, data_source_arguments=[0]),
]

from typing import Callable, Set

import numpy as np

from pyquibbler.third_party_overriding.definitions import OverrideDefinition
from pyquibbler.third_party_overriding.types import Argument, KeywordArgument, IndexArgument


class NumpyOverrideDefinition(OverrideDefinition):


    @classmethod
    def from_func(cls, func: Callable, data_source_arguments: Set[Argument]):
        return cls(func_name=func.__name__,
                   module_or_cls=np,
                   data_source_arguments=data_source_arguments or set())


NUMPY_DEFINITIONS = [
    NumpyOverrideDefinition.from_func(
        func=np.rot90,
        data_source_arguments={KeywordArgument(keyword="m")}
    ),
    NumpyOverrideDefinition.from_func(
        func=np.concatenate,
        data_source_arguments={IndexArgument(index=0)}
    ),
    NumpyOverrideDefinition.from_func(
        func=np.repeat,
        data_source_arguments={KeywordArgument(keyword="a")}
    ),
    NumpyOverrideDefinition.from_func(
        func=np.full,
        data_source_arguments={KeywordArgument(keyword="fill_value")}
    ),
    NumpyOverrideDefinition.from_func(
        func=np.reshape,
        data_source_arguments={KeywordArgument(keyword="a")}
    ),
    NumpyOverrideDefinition.from_func(
        func=np.array,
        data_source_arguments={IndexArgument(0)}
    )
]

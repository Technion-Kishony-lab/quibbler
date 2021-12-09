from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional, Callable, Any, Set, Mapping, List

from pyquibbler import Assignment
from pyquibbler.iterators import iter_objects_of_type_in_object_shallowly
from pyquibbler.path_translators.inversal_types import ArgumentWithValue, Source, SourceType
from pyquibbler.quib.function_quibs.utils import ArgsValues, FuncWithArgsValues
from pyquibbler.third_party_overriding.overriding import get_definition_for_function


class Inverter(ABC):

    SUPPORTING_FUNCS: Set[Callable] = set()
    PRIORITY = 0

    def __init__(self,
                 func_with_args_values: FuncWithArgsValues,
                 assignment: Assignment,
                 previous_value: Any
                 ):
        self._func_with_args_values = func_with_args_values
        self._assignment = assignment
        self._previous_result = previous_value

    def supports_func(self, func: Callable):
        return func in self.SUPPORTING_FUNCS

    @property
    def func(self):
        return self._func_with_args_values.func

    @property
    def args_values(self):
        return self._func_with_args_values.args_values

    @property
    def func_definition(self):
        return get_definition_for_function(self.func)

    def _get_data_source_arguments_with_values(self) -> List[ArgumentWithValue]:
        return [
            ArgumentWithValue(argument=argument, value=self.args_values[argument])
            for argument in self.func_definition.data_source_arguments
        ]

    @lru_cache()
    def _get_data_sources(self) -> Set[Source]:
        return set(iter_objects_of_type_in_object_shallowly(Source, [
            self.args_values[argument] for argument in self.func_definition.data_source_arguments
        ]))

    @abstractmethod
    def get_inversals(self):
        pass

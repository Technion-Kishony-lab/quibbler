from abc import ABC
from functools import lru_cache
from typing import Set, List

from pyquibbler.refactor.utilities.iterators import iter_objects_of_type_in_object_shallowly
from pyquibbler.refactor.translation.types import Source, ArgumentWithValue
from pyquibbler.refactor.function_definitions.func_call import FuncCall


class Translator(ABC):

    PRIORITY = 0

    def __init__(self, func_call: FuncCall):
        self._func_call = func_call

    @property
    def func(self):
        return self._func_call.func

    @property
    def args_values(self):
        return self._func_call.args_values

    @property
    def _args(self):
        return self.args_values.args

    @property
    def _kwargs(self):
        return self.args_values.kwargs

    @property
    def func_definition(self):
        from pyquibbler.refactor.function_definitions import get_definition_for_function
        return get_definition_for_function(self.func)

    def _get_data_source_arguments_with_values(self) -> List[ArgumentWithValue]:
        return [
            ArgumentWithValue(argument=argument, value=self.args_values[argument])
            for argument in self.func_definition.data_source_arguments
        ]

    @lru_cache()
    def get_data_sources(self) -> Set[Source]:
        return set(iter_objects_of_type_in_object_shallowly(Source, self._func_call.get_data_source_argument_values()))

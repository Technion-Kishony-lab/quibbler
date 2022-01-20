from abc import ABC
from typing import Set, List

from pyquibbler.translation.types import Source, ArgumentWithValue
from pyquibbler.function_definitions.func_call import FuncCall


class PathTranslator(ABC):

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = False

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
        from pyquibbler.function_definitions import get_definition_for_function
        return get_definition_for_function(self.func)

    def _get_data_source_arguments_with_values(self) -> List[ArgumentWithValue]:
        return [
            ArgumentWithValue(argument=argument, value=self.args_values[argument])
            for argument in self.func_definition.data_source_arguments
        ]

    def get_data_sources(self) -> Set[Source]:
        return self._func_call.get_data_sources()

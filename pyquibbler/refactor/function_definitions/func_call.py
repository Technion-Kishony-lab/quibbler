from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Any, Mapping, Optional, Callable, List, TYPE_CHECKING

from pyquibbler.refactor.quib.external_call_failed_exception_handling import \
    external_call_failed_exception_handling
from pyquibbler.refactor.utilities.iterators import iter_args_and_names_in_function_call

if TYPE_CHECKING:
    from pyquibbler.refactor.function_definitions import FunctionDefinition


@dataclass
class ArgsValues:
    """
    In a function call, when trying to understand what value an a specific parameter was given, looking at
    args and kwargs isn't enough. We have to deal with:
    - Positional arguments passed with a keyword
    - Keyword arguments passed positionally
    - Default arguments
    This class uses the function signature to determine the values each parameter was given,
    and can be indexed using ints, slices and keywords.
    """

    args: Tuple[Any, ...]
    kwargs: Mapping[str, Any]
    arg_values_by_position: Tuple[Any, ...]
    arg_values_by_name: Mapping[str, Any]

    def __getitem__(self, item):
        from pyquibbler.refactor.function_definitions import KeywordArgument, PositionalArgument

        if isinstance(item, KeywordArgument):
            return self.arg_values_by_name[item.keyword]
        elif isinstance(item, PositionalArgument):
            return self.arg_values_by_position[item.index]

        # TODO: Is following necessary? Primitive obssession..
        if isinstance(item, str):
            return self.arg_values_by_name[item]
        return self.arg_values_by_position[item]

    def get(self, keyword: str, default: Optional = None) -> Optional[Any]:
        return self.arg_values_by_name.get(keyword, default)

    @classmethod
    def from_function_call(cls, func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any], include_defaults):
        # We use external_call_failed_exception_handling here as if the user provided the wrong arguments to the
        # function we'll fail here
        with external_call_failed_exception_handling():
            try:
                arg_values_by_name = dict(iter_args_and_names_in_function_call(func, args, kwargs, include_defaults))
                arg_values_by_position = tuple(arg_values_by_name.values())
            except ValueError:
                arg_values_by_name = kwargs
                arg_values_by_position = args

        return cls(args, kwargs, arg_values_by_position, arg_values_by_name)


@dataclass
class FuncCall:
    args_values: ArgsValues
    func: Callable

    @classmethod
    def from_function_call(cls, func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any], include_defaults):
        return cls(args_values=ArgsValues.from_function_call(func, args, kwargs, include_defaults), func=func)

    def get_func_definition(self) -> FunctionDefinition:
        from pyquibbler.refactor.function_definitions import get_definition_for_function
        return get_definition_for_function(self.func)

    @property
    def args(self):
        return self.args_values.args

    @property
    def kwargs(self):
        return self.args_values.kwargs

    def get_data_source_argument_values(self) -> List[Any]:
        return self.get_func_definition().get_data_source_argument_values(self.args_values)

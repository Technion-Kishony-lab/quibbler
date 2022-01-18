from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Tuple, Any, Mapping, Optional, Callable, List, TYPE_CHECKING

from pyquibbler.path import Path
from pyquibbler.quib.external_call_failed_exception_handling import \
    external_call_failed_exception_handling
from pyquibbler.utilities.iterators import iter_args_and_names_in_function_call

if TYPE_CHECKING:
    from pyquibbler.function_definitions import FuncDefinition


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
        from pyquibbler.function_definitions import KeywordArgument, PositionalArgument

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
    def from_func_args_kwargs(cls, func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any], include_defaults):
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
class FuncCall(ABC):
    args_values: ArgsValues
    func: Callable

    @classmethod
    def from_(cls, func: Callable,
              func_args: Tuple[Any, ...],
              func_kwargs: Mapping[str, Any],
              include_defaults: bool = False,
              *args, **kwargs):
        return cls(args_values=ArgsValues.from_func_args_kwargs(func, func_args, func_kwargs, include_defaults), func=func,
                   *args, **kwargs)

    def get_func_definition(self) -> FuncDefinition:
        from pyquibbler.function_definitions import get_definition_for_function
        return get_definition_for_function(self.func)

    @property
    def args(self):
        return self.args_values.args

    @property
    def kwargs(self):
        return self.args_values.kwargs

    def get_data_source_argument_values(self) -> List[Any]:
        return self.get_func_definition().get_data_source_argument_values(self.args_values)

    @abstractmethod
    def get_value_valid_at_path(self, path: Path):
        pass

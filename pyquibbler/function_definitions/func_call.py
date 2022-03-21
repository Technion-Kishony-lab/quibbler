from __future__ import annotations

import functools
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Tuple, Any, Mapping, Optional, Callable, List, TYPE_CHECKING, Type, ClassVar

from .location import SourceLocation, create_source_location
from .types import Argument
from pyquibbler.quib.external_call_failed_exception_handling import \
    external_call_failed_exception_handling
from pyquibbler.utilities.iterators import iter_args_and_names_in_function_call, \
    get_paths_for_objects_of_type, iter_object_type_in_args

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

    def __hash__(self):
        return id(self)

    def __getitem__(self, item):
        from pyquibbler.function_definitions import KeywordArgument, PositionalArgument

        if isinstance(item, KeywordArgument):
            return self.arg_values_by_name[item.keyword]
        elif isinstance(item, PositionalArgument):
            return self.arg_values_by_position[item.index]

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
            except (ValueError, TypeError):
                arg_values_by_name = kwargs
                arg_values_by_position = args

        return cls(args, kwargs, arg_values_by_position, arg_values_by_name)


def load_source_locations_before_running(f):
    """
    Does this method need data_source/parameter locations?
    """
    @functools.wraps(f)
    def _wrapper(self, *args, **kwargs):
        self._load_source_locations()
        return f(self, *args, **kwargs)
    return _wrapper


@dataclass
class FuncCall(ABC):
    """
    Represents a call to a function - a function with given args and kwargs.
    This class is abstract- any class that wants to inherit must set what object type it's sources are (more on
    this further down) and implement the "run" method

    Any call to a function within quibbler has "sources"- a source can be of two types, either parameter or data.
    *Where* these sources are located (ie in which arguments) is defined in FuncDefinition.
    But every class that inherits from FuncCall must define what type it's sources are, so that functions such as
    `get_data_sources` can correctly search and find sources of that type within the arguments which pertain to
     them

    """

    SOURCE_OBJECT_TYPE: ClassVar[Type]

    data_source_locations: Optional[List[SourceLocation]] = None
    parameter_source_locations: Optional[List[SourceLocation]] = None

    def __hash__(self):
        return id(self)

    @property
    @abstractmethod
    def args_values(self):
        pass

    @property
    @abstractmethod
    def func(self):
        pass

    def _get_argument_used_in_current_func_call_for_argument(self, argument: Argument):
        """
        Get the argument actually used in this specific funccall corresponding to the given parameter `argument`.

        For example, given:

        def my_func(a):
            pass

        `a` could be referenced by both PositionalArgument(0) or KeywordArgument("a")

        Given either of the arguments PositionalArgument(0) or KeywordArgument("a"), this func will return the one
        actually being used in this instance
        """
        try:
            create_source_location(argument=argument, path=[]).find_in_args_kwargs(self.args, self.kwargs)
            return argument
        except (KeyError, IndexError):
            return self.get_func_definition().get_corresponding_argument(argument)

    def _get_locations_within_arguments_and_values(self, arguments_and_values):
        return [
            create_source_location(self._get_argument_used_in_current_func_call_for_argument(argument), path)
            for argument, value in arguments_and_values
            for path in get_paths_for_objects_of_type(obj=value, type_=self.SOURCE_OBJECT_TYPE)
        ]

    def _load_source_locations(self):
        """
        Load the locations of all sources (data sources and parameter sources) so we don't need to search within
        our args kwargs every time we need them
        """

        if self.data_source_locations is None:
            data_arguments_with_values = \
                self.get_func_definition().get_data_source_arguments_with_values(self.args_values)
            parameter_arguments_with_values = \
                self.get_func_definition().get_parameter_arguments_with_values(self.args_values)

            self.data_source_locations = \
                self._get_locations_within_arguments_and_values(data_arguments_with_values)
            self.parameter_source_locations = \
                self._get_locations_within_arguments_and_values(parameter_arguments_with_values)

        return self.data_source_locations, self.parameter_source_locations

    def _transform_source_locations(self,
                                    args,
                                    kwargs,
                                    locations: List[SourceLocation],
                                    transform_func: Callable[[Any], Any]):

        for location in locations:
            transformed = transform_func(
                location.find_in_args_kwargs(args=self.args, kwargs=self.kwargs)
            )
            args, kwargs = location.set_in_args_kwargs(args=args, kwargs=kwargs, value=transformed)
        return args, kwargs

    @load_source_locations_before_running
    def transform_sources_in_args_kwargs(self,
                                         transform_data_source_func: Callable[[Any], Any] = None,
                                         transform_parameter_func: Callable[[Any], Any] = None):
        """
        Return args and kwargs, transforming all data sources and parameter sources within by their respective function.
        If a function is not given for the respective source type the source will be returned as is
        """

        new_args, new_kwargs = self.args, self.kwargs

        if transform_data_source_func is not None:
            new_args, new_kwargs = self._transform_source_locations(args=new_args, kwargs=new_kwargs,
                                                                    locations=self.data_source_locations,
                                                                    transform_func=transform_data_source_func)
        if transform_parameter_func is not None:
            new_args, new_kwargs = self._transform_source_locations(args=new_args, kwargs=new_kwargs,
                                                                    locations=self.parameter_source_locations,
                                                                    transform_func=transform_parameter_func)

        return new_args, new_kwargs

    @functools.lru_cache()
    def get_objects_of_type_in_args_kwargs(self, type_):
        return list(iter_object_type_in_args(type_, self.args, self.kwargs))

    @functools.lru_cache()
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
        return [v for _, v in self.get_func_definition().get_data_source_arguments_with_values(self.args_values)]

    @load_source_locations_before_running
    @functools.lru_cache()
    def get_data_sources(self):
        sources = set()
        for location in self.data_source_locations:
            sources.add(location.find_in_args_kwargs(self.args, self.kwargs))
        return sources

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

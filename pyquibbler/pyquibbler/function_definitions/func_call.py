from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import dataclass
from inspect import BoundArguments, Signature
from typing import Tuple, Any, Mapping, Optional, Callable, List, TYPE_CHECKING, Type, ClassVar, Dict, Set, Union

from .location import SourceLocation
from pyquibbler.quib.external_call_failed_exception_handling import \
    external_call_failed_exception_handling
from pyquibbler.utilities.iterators import get_object_type_locations_in_args_kwargs
from ..utils import get_signature_for_func

if TYPE_CHECKING:
    from .func_definition import FuncDefinition


@dataclass
class FuncArgsKwargs:
    """
    In a function call, when trying to understand what value an a specific parameter was given, looking at
    args and kwargs isn't enough. We have to deal with:
    - Positional arguments passed with a keyword
    - Keyword arguments passed positionally
    - Default arguments
    This class uses the function signature to determine the values each parameter was given,
    and can be indexed using ints, slices and keywords.
    """

    func: Callable
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    @staticmethod
    def _get_arguments_without_equal_to_defaults(arguments, sig: Signature, defaults_to_include: Set[str]):
        """
        Remove arguments which exist as default arguments with the same value.
        """
        new_arguments = []
        parameters = sig.parameters
        for name, value in arguments.items():
            if name in defaults_to_include or not (name in parameters and parameters[name].default == value):
                new_arguments.append((name, value))

        return dict(new_arguments)

    def _iter_args_and_names_in_function_call(self,
                                              defaults_to_include: Union[None, set[str]],
                                              remove_arguments_equal_to_defaults: bool,
                                              ):
        """
        Given a specific function call - func, args, kwargs - return an iterator to (name, val) tuples
        of all arguments that would have been passed to the function.

        defaults_to_include:
            None: all defaults, or set of names of default kwargs to include
        """
        sig = get_signature_for_func(self.func)
        bound_args = sig.bind(*self.args, **self.kwargs)

        arguments = bound_args.arguments

        # Add defaults:
        if defaults_to_include is None or len(defaults_to_include) > 0:
            bound_args.apply_defaults()
            arguments_with_defaults = bound_args.arguments
            if defaults_to_include is None:
                arguments = arguments_with_defaults
            else:
                arguments = {**arguments, **{k: arguments_with_defaults[k] for k in defaults_to_include}}
        
        # Remove arguments with value equal to default: 
        if remove_arguments_equal_to_defaults:
            arguments = self._get_arguments_without_equal_to_defaults(arguments, sig,
                                                                      defaults_to_include=defaults_to_include)

        return arguments.items()

    def get_args_values_by_name_and_position(self,
                                             defaults_to_include: Union[None, set[str]] = None,
                                             remove_arguments_equal_to_defaults: bool = False
                                             ) -> Tuple[Mapping[str, Any], Tuple[Any, ...]]:
        # We use external_call_failed_exception_handling here as if the user provided the wrong arguments to the
        # function we'll fail here
        with external_call_failed_exception_handling():
            try:
                arg_values_by_name = dict(self._iter_args_and_names_in_function_call(
                    defaults_to_include, remove_arguments_equal_to_defaults))
                arg_values_by_position = tuple(arg_values_by_name.values())
            except (ValueError, TypeError):
                arg_values_by_name = self.kwargs
                arg_values_by_position = self.args
        return arg_values_by_name, arg_values_by_position

    def get_arg_values_by_name(self, include_defaults: bool = True) -> Mapping[str, Any]:
        return self.get_args_values_by_name_and_position(
            defaults_to_include=None if include_defaults else set()
        )[0]

    def get_arg_values_by_position(self, include_defaults: bool = True) -> Tuple[Any, ...]:
        return self.get_args_values_by_name_and_position(
            defaults_to_include=None if include_defaults else set()
        )[1]

    def __hash__(self):
        return id(self)

    def get(self, keyword: str, default: Optional = None, include_defaults: bool = True) -> Optional[Any]:
        return self.get_arg_values_by_name(include_defaults).get(keyword, default)


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
    _data_sources: Optional[Set[Any]] = None
    _parameter_sources: Optional[Set[Any]] = None
    func_args_kwargs: FuncArgsKwargs = None
    func_definition: FuncDefinition = None

    def __hash__(self):
        return id(self)

    @property
    def func(self) -> Callable:
        return self.func_args_kwargs.func

    @property
    def args(self):
        return self.func_args_kwargs.args

    @property
    def kwargs(self):
        return self.func_args_kwargs.kwargs

    def load_source_locations(self, locations: List[SourceLocation] = None):
        """
        Load the locations of all sources (data sources and parameter sources) so we don't need to search within
        our args kwargs every time we need them.
        Further save re-searching if locations is given (from _create_quib_supporting_func)
        """

        if locations is None:
            locations = get_object_type_locations_in_args_kwargs(self.SOURCE_OBJECT_TYPE,
                                                                 self.func_args_kwargs.args,
                                                                 self.func_args_kwargs.kwargs)

        self.data_source_locations = []
        self.parameter_source_locations = []
        data_arguments = \
            self.func_definition.get_data_source_arguments(self.func_args_kwargs)
        for location in locations:
            if location.argument in data_arguments:
                self.data_source_locations.append(location)
            else:
                self.parameter_source_locations.append(location)

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

    def get_data_sources(self):
        if self._data_sources is None:
            sources = set()
            for location in self.data_source_locations:
                sources.add(location.find_in_args_kwargs(self.args, self.kwargs))
            self._data_sources = sources
        return self._data_sources

    def get_parameter_sources(self):
        if self._parameter_sources is None:
            sources = set()
            for location in self.parameter_source_locations:
                sources.add(location.find_in_args_kwargs(self.args, self.kwargs))
            self._parameter_sources = sources
        return self._parameter_sources

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

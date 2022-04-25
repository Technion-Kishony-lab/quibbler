from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Set, Type, List, TYPE_CHECKING, Callable, Optional

from pyquibbler.function_definitions.func_call import FuncArgsKwargs
from pyquibbler.function_definitions.types import RawArgument, Argument, PositionalArgument, KeywordArgument, \
    convert_raw_data_source_arguments_to_data_source_arguments
from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.utils import get_signature_for_func

if TYPE_CHECKING:
    from pyquibbler.quib.func_calling import QuibFuncCall
    from pyquibbler.inversion.inverter import Inverter


def get_default_quib_func_call():
    from pyquibbler.quib.func_calling import CachedQuibFuncCall
    return CachedQuibFuncCall


@dataclass
class FuncDefinition:
    """
    Represents a definition of all metadata on how to use a function in all different parts of Quibbler.
    This includes which arguments are data_sources, how to translate paths, how to invert, how to run the function, etc
    """

    func: Optional[Callable] = None
    data_source_arguments: Set[Argument] = field(repr=False, default_factory=set)
    is_random: bool = False
    is_file_loading: bool = False
    is_graphics: Optional[bool] = False  # None for 'maybe'
    pass_quibs: bool = False
    lazy: Optional[bool] = None  # None for auto: LAZY for non-graphics, GRAPHICS_LAZY for is_graphics=True
    is_artist_setter: bool = field(repr=False, default=False)
    inverters: List[Type[Inverter]] = field(repr=False, default_factory=list)
    backwards_path_translators: List[Type[BackwardsPathTranslator]] = field(repr=False, default_factory=list)
    forwards_path_translators: List[Type[ForwardsPathTranslator]] = field(repr=False, default_factory=list)
    quib_function_call_cls: Type[QuibFuncCall] = field(repr=False, default_factory=get_default_quib_func_call)

    def __hash__(self):
        return id(self)

    @property
    def is_impure(self):
        return self.is_file_loading or self.is_random

    #@functools.lru_cache()
    def get_parameters(self):
        try:
            sig = get_signature_for_func(self.func)
            return sig.parameters
        except ValueError:
            return {}

    #@functools.lru_cache()
    def get_positional_to_keyword_arguments(self):
        return {
            PositionalArgument(i): KeywordArgument(name) if parameter.kind.name != "POSITIONAL_ONLY" else None
            for i, (name, parameter) in enumerate(self.get_parameters().items())
        }

    #@functools.lru_cache()
    def get_keyword_to_positional_arguments(self):
        return {
            KeywordArgument(name): PositionalArgument(i) if parameter.kind.name != "KEYWORD_ONLY" else None
            for i, (name, parameter) in enumerate(self.get_parameters().items())
        }

    def get_corresponding_argument(self, argument):
        """
        Get the argument of the opposite type (positional v keyword) which corresponds to the same argument

        For example, given:

        def my_func(a):
            pass

        `a` could be referenced by both PositionalArgument(0) or KeywordArgument("a")

        In this instance:
            If given PositionalArgument(0) will return KeywordArgument("a")
            If given KeywordArgument("a") will return PositionalArgument(0)
        """
        if isinstance(argument, PositionalArgument):
            corresponding_dict = self.get_positional_to_keyword_arguments()
        else:
            corresponding_dict = self.get_keyword_to_positional_arguments()
        return corresponding_dict[argument]

    def _get_all_data_source_arguments(self, func_args_kwargs: FuncArgsKwargs):
        all_data_source_arguments = set()
        for argument, value in self.get_data_source_arguments_with_values(func_args_kwargs):
            try:
                corresponding_argument = self.get_corresponding_argument(argument)
            except KeyError:
                corresponding_argument = None

            all_data_source_arguments.add(argument)
            if corresponding_argument is not None:
                all_data_source_arguments.add(corresponding_argument)

        return all_data_source_arguments

    #@functools.lru_cache()
    def get_data_source_arguments_with_values(self, func_args_kwargs: FuncArgsKwargs):
        return [
            (argument, func_args_kwargs[argument])
            for argument in self.data_source_arguments
        ]

    def get_parameter_arguments_with_values(self, func_args_kwargs: FuncArgsKwargs):
        all_data_source_arguments = self._get_all_data_source_arguments(func_args_kwargs)
        return [*[
            (PositionalArgument(index=i), func_args_kwargs.args[i])
            for i, arg in enumerate(func_args_kwargs.args)
            if PositionalArgument(index=i) not in all_data_source_arguments
        ], *[
            (KeywordArgument(keyword=kwarg), func_args_kwargs.kwargs[kwarg])
            for kwarg, value in func_args_kwargs.kwargs.items()
            if KeywordArgument(keyword=kwarg) not in all_data_source_arguments
        ]]


@dataclass
class ElementWiseFuncDefinition(FuncDefinition):
    """
    Represents a definition of functions that act element-wise on a single arg
    """

    inverse_func_without_input: Optional[Callable] = field(repr=False, default=None)
    inverse_func_with_input: Optional[Callable] = field(repr=False, default=None)


ElementWiseFuncDefinition.__hash__ = FuncDefinition.__hash__


def create_func_definition(raw_data_source_arguments: List[RawArgument] = None,
                           is_random: bool = False,
                           is_file_loading: bool = False,
                           is_graphics: Optional[bool] = False,
                           pass_quibs: bool = False,
                           lazy: Optional[bool] = None,
                           is_artist_setter: bool = False,
                           inverters: List[Type[Inverter]] = None,
                           backwards_path_translators: List[Type[BackwardsPathTranslator]] = None,
                           forwards_path_translators: List[Type[ForwardsPathTranslator]] = None,
                           quib_function_call_cls: Type[QuibFuncCall] = None,
                           func: Optional[Callable] = None,
                           func_definition_cls: Optional[FuncDefinition] = None,
                           **kwargs) -> FuncDefinition:
    """
    Create a definition for a function- this will allow quibbler to utilize Quibs with the function in a more
    specific manner (and not just use default behavior), for whichever parameters you give.
    """

    func_definition_cls = func_definition_cls or FuncDefinition
    quib_function_call_cls = quib_function_call_cls or get_default_quib_func_call()
    raw_data_source_arguments = raw_data_source_arguments or set()
    data_source_arguments = convert_raw_data_source_arguments_to_data_source_arguments(raw_data_source_arguments)
    return func_definition_cls(
        func=func,
        is_random=is_random,
        is_graphics=is_graphics,
        is_file_loading=is_file_loading,
        data_source_arguments=data_source_arguments,
        inverters=inverters or [],
        backwards_path_translators=backwards_path_translators or [],
        forwards_path_translators=forwards_path_translators or [],
        quib_function_call_cls=quib_function_call_cls,
        pass_quibs=pass_quibs,
        lazy=lazy,
        is_artist_setter=is_artist_setter,
        **kwargs
    )

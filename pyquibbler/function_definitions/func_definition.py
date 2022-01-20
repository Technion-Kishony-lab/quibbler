from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Set, Type, List, Union, TYPE_CHECKING, Callable

from pyquibbler.function_definitions.func_call import ArgsValues
from pyquibbler.function_definitions.types import Argument, PositionalArgument, KeywordArgument
from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.utils import get_signature_for_func

if TYPE_CHECKING:
    from pyquibbler.quib.func_calling import QuibFuncCall
    from pyquibbler.inversion.inverter import Inverter


def get_default_quib_func_call():
    from pyquibbler.quib.func_calling import QuibFuncCall
    return QuibFuncCall


@dataclass
class FuncDefinition:
    """
    Represents a definition of all metadata on how to use a function in all different parts of Quibbler.
    This includes which arguments are data_sources, how to translate paths, how to invert, how to run the function, etc
    """

    data_source_arguments: Set[Argument] = field(default_factory=set)
    is_random_func: bool = False
    is_file_loading_func: bool = False
    is_known_graphics_func: bool = False
    replace_previous_quibs_on_artists: bool = False
    inverters: List[Type[Inverter]] = field(default_factory=list)
    backwards_path_translators: List[Type[BackwardsPathTranslator]] = field(default_factory=list)
    forwards_path_translators: List[Type[ForwardsPathTranslator]] = field(default_factory=list)
    quib_function_call_cls: Type[QuibFuncCall] = field(default_factory=get_default_quib_func_call)

    def __hash__(self):
        return id(self)

    @functools.lru_cache()
    def get_parameters(self, func):
        try:
            sig = get_signature_for_func(func)
            return sig.parameters
        except ValueError:
            return {}

    @functools.lru_cache()
    def get_positional_to_keyword_arguments(self, func):
        return {
            PositionalArgument(i): KeywordArgument(name) if parameter.kind.name != "POSITIONAL_ONLY" else None
            for i, (name, parameter) in enumerate(self.get_parameters(func).items())
        }

    @functools.lru_cache()
    def get_keyword_to_positional_arguments(self, func):
        return {
            KeywordArgument(name): PositionalArgument(i) if parameter.kind.name != "KEYWORD_ONLY" else None
            for i, (name, parameter) in enumerate(self.get_parameters(func).items())
        }

    def get_corresponding_argument(self, func, argument):
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
            corresponding_dict = self.get_positional_to_keyword_arguments(func)
        else:
            corresponding_dict = self.get_keyword_to_positional_arguments(func)
        return corresponding_dict[argument]

    def _get_all_data_source_arguments(self, func: Callable, args_values):
        all_data_source_arguments = set()
        for argument, value in self.get_data_source_arguments_with_values(args_values):
            try:
                corresponding_argument = self.get_corresponding_argument(func, argument)
            except KeyError:
                corresponding_argument = None

            all_data_source_arguments.add(argument)
            if corresponding_argument is not None:
                all_data_source_arguments.add(corresponding_argument)

        return all_data_source_arguments

    @functools.lru_cache()
    def get_data_source_arguments_with_values(self, args_values: ArgsValues):
        return [
            (argument, args_values[argument])
            for argument in self.data_source_arguments
        ]

    def get_parameter_arguments_with_values(self, func, args_values: ArgsValues):
        all_data_source_arguments = self._get_all_data_source_arguments(func, args_values)
        return [*[
            (PositionalArgument(index=i), args_values.args[i])
            for i, arg in enumerate(args_values.args)
            if PositionalArgument(index=i) not in all_data_source_arguments
        ], *[
            (KeywordArgument(keyword=kwarg), args_values.kwargs[kwarg])
            for kwarg, value in args_values.kwargs.items()
            if KeywordArgument(keyword=kwarg) not in all_data_source_arguments
        ]]


def create_func_definition(data_source_arguments: List[Union[str, int]] = None,
                           is_random_func: bool = False,
                           is_file_loading_func: bool = False,
                           is_known_graphics_func: bool = False,
                           replace_previous_quibs_on_artists: bool = False,
                           inverters: List[Type[Inverter]] = None,
                           backwards_path_translators: List[Type[BackwardsPathTranslator]] = None,
                           forwards_path_translators: List[Type[ForwardsPathTranslator]] = None,
                           quib_function_call_cls: Type[QuibFuncCall] = None
                           ):
    """
    Create a definition for a function- this will allow quibbler to utilize Quibs with the function in a more
    specific manner (and not just use default behavior), for whichever parameters you give.
    """

    from pyquibbler.quib.func_calling import QuibFuncCall
    quib_function_call_cls = quib_function_call_cls or QuibFuncCall
    data_source_arguments = data_source_arguments or set()
    raw_data_source_arguments = {
        PositionalArgument(data_source_argument)
        if isinstance(data_source_argument, int)
        else KeywordArgument(data_source_argument)
        for data_source_argument in data_source_arguments
    }
    return FuncDefinition(
        is_random_func=is_random_func,
        is_known_graphics_func=is_known_graphics_func,
        is_file_loading_func=is_file_loading_func,
        data_source_arguments=raw_data_source_arguments,
        inverters=inverters or [],
        backwards_path_translators=backwards_path_translators or [],
        forwards_path_translators=forwards_path_translators or [],
        quib_function_call_cls=quib_function_call_cls,
        replace_previous_quibs_on_artists=replace_previous_quibs_on_artists
    )

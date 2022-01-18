from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set, Type, List, Union, TYPE_CHECKING

from pyquibbler.function_definitions.func_call import ArgsValues
from pyquibbler.function_definitions.types import Argument, PositionalArgument, KeywordArgument
from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator

if TYPE_CHECKING:
    from pyquibbler.quib.func_calling import QuibFuncCall
    from pyquibbler.inversion.inverter import Inverter


def get_function_runner():
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
    quib_function_call_cls: Type[QuibFuncCall] = field(default_factory=get_function_runner)

    def get_data_source_argument_values(self, args_values: ArgsValues):
        return [
            args_values[argument]
            for argument in self.data_source_arguments
        ]


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

from dataclasses import dataclass, field
from typing import Set, Type, List, Union

from pyquibbler.refactor.function_definitions.func_call import ArgsValues
from pyquibbler.refactor.function_definitions.types import Argument, PositionalArgument, KeywordArgument
from pyquibbler.refactor.inversion.inverter import Inverter
from pyquibbler.refactor.quib.function_runners import DefaultFunctionRunner, FunctionRunner
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator


@dataclass
class FunctionDefinition:
    """
    Represents a definition of all metadata on how to use a function in all different parts of Quibbler.
    This includes which arguments are data_sources, how to translate paths, how to invert, how to run the function, etc
    """

    data_source_arguments: Set[Argument] = field(default_factory=set)
    inverters: List[Type[Inverter]] = None
    backwards_path_translators: List[Type[BackwardsPathTranslator]] = field(default_factory=list)
    forwards_path_translators: List[Type[ForwardsPathTranslator]] = field(default_factory=list)
    function_runner_cls: Type[FunctionRunner] = DefaultFunctionRunner

    def get_data_source_argument_values(self, args_values: ArgsValues):
        return [
            args_values[argument]
            for argument in self.data_source_arguments
        ]


def create_function_definition(data_source_arguments: List[Union[str, int]] = None,
                               inverters: List[Type[Inverter]] = None,
                               backwards_path_translators: List[Type[BackwardsPathTranslator]] = None,
                               forwards_path_translators: List[Type[ForwardsPathTranslator]] = None,
                               function_runner_cls: Type[FunctionRunner] = DefaultFunctionRunner
                               ):
    """
    Create a definition for a function- this will allow quibbler to utilize Quibs with the function in a more
    specific manner (and not just use default behavior), for whichever parameters you give.
    """
    data_source_arguments = data_source_arguments or set()
    raw_data_source_arguments = {
        PositionalArgument(data_source_argument)
        if isinstance(data_source_argument, int)
        else KeywordArgument(data_source_argument)
        for data_source_argument in data_source_arguments
    }
    return FunctionDefinition(data_source_arguments=raw_data_source_arguments,
                              inverters=inverters or [],
                              backwards_path_translators=backwards_path_translators or [],
                              forwards_path_translators=forwards_path_translators or [],
                              function_runner_cls=function_runner_cls)

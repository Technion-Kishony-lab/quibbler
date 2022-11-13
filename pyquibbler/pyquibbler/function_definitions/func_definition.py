from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set, Type, List, Callable, Optional, Union, Tuple

from pyquibbler.path_translation import BackwardsPathTranslator, ForwardsPathTranslator
from pyquibbler.type_translation.translators import TypeTranslator
from pyquibbler.function_overriding.third_party_overriding.numpy.inverse_functions import InverseFunc

from .func_call import FuncArgsKwargs
from .types import ArgId, Argument, \
    convert_raw_data_arguments_to_data_argument_designations, DataArgumentDesignation, SubArgument
from .utils import get_corresponding_argument

from typing import TYPE_CHECKING
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

    data_argument_designations: List[DataArgumentDesignation] = field(repr=False, default_factory=list)
    is_random: bool = False
    is_file_loading: bool = False
    is_graphics: Optional[bool] = False  # None for 'maybe'
    is_operator: bool = False  # is the function an operator
    pass_quibs: bool = False
    lazy: Optional[bool] = None  # None for auto: LAZY for non-graphics, GRAPHICS_LAZY for is_graphics=True
    is_artist_setter: bool = field(repr=False, default=False)
    inverters: List[Type[Inverter]] = field(repr=False, default_factory=list)
    backwards_path_translators: List[Type[BackwardsPathTranslator]] = field(repr=False, default_factory=list)
    forwards_path_translators: List[Type[ForwardsPathTranslator]] = field(repr=False, default_factory=list)
    quib_function_call_cls: Type[QuibFuncCall] = field(repr=False, default_factory=get_default_quib_func_call)
    kwargs_to_ignore_in_repr: Optional[Set[str]] = None
    result_type_or_type_translators: Union[Type, List[Type[TypeTranslator]]] = field(repr=False, default_factory=list)

    def __hash__(self):
        return id(self)

    @property
    def is_impure(self):
        return self.is_file_loading or self.is_random

    def get_data_arguments(self, func_args_kwargs: FuncArgsKwargs) -> List[Argument]:
        """
        Returns the data arguments in the function call
        Takes care of cases like np.concatenate, where the function argument is a tuple containing multiple
        data arguments.
        """
        data_arguments = []
        designated_data_arguments = [data_argument_designation.argument
                                     for data_argument_designation in self.data_argument_designations]

        for func_call_argument in func_args_kwargs.get_all_arguments():
            data_argument_designation = None
            if func_call_argument in designated_data_arguments:
                data_argument_designation = \
                    self.data_argument_designations[designated_data_arguments.index(func_call_argument)]
            if not data_argument_designation:
                corresponding_func_call_argument = get_corresponding_argument(func_args_kwargs.func, func_call_argument)
                if corresponding_func_call_argument in designated_data_arguments:
                    data_argument_designation = \
                        self.data_argument_designations[
                            designated_data_arguments.index(corresponding_func_call_argument)]
            if not data_argument_designation:
                continue

            if data_argument_designation.is_multi_arg:
                argument_value = func_args_kwargs.get_arg_value_by_argument(func_call_argument)
                for index in range(len(argument_value)):
                    data_arguments.append(SubArgument(func_call_argument, sub_index=index))
            else:
                data_arguments.append(func_call_argument)

        return data_arguments


@dataclass
class ElementWiseFuncDefinition(FuncDefinition):
    """
    Represents a definition of functions that act element-wise on a single arg
    """

    func: Optional[Callable] = None
    inverse_funcs: Tuple[Optional[InverseFunc]] = field(repr=False, default_factory=tuple)


ElementWiseFuncDefinition.__hash__ = FuncDefinition.__hash__


def create_func_definition(raw_data_source_arguments: List[ArgId] = None,
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
                           result_type_or_type_translators: Union[Type, List[Type[TypeTranslator]]] = None,
                           func_definition_cls: Optional[FuncDefinition] = None,
                           kwargs_to_ignore_in_repr: Optional[Set[str]] = None,
                           **kwargs) -> FuncDefinition:
    """
    Create a definition for a function- this will allow quibbler to utilize Quibs with the function in a more
    specific manner (and not just use default behavior), for whichever parameters you give.
    """

    func_definition_cls = func_definition_cls or FuncDefinition
    quib_function_call_cls = quib_function_call_cls or get_default_quib_func_call()
    raw_data_source_arguments = raw_data_source_arguments or set()
    data_argument_designations = convert_raw_data_arguments_to_data_argument_designations(raw_data_source_arguments)
    return func_definition_cls(
        is_random=is_random,
        is_graphics=is_graphics,
        is_file_loading=is_file_loading,
        data_argument_designations=data_argument_designations,
        inverters=inverters or [],
        backwards_path_translators=backwards_path_translators or [],
        forwards_path_translators=forwards_path_translators or [],
        quib_function_call_cls=quib_function_call_cls,
        pass_quibs=pass_quibs,
        result_type_or_type_translators=result_type_or_type_translators or [],
        lazy=lazy,
        is_artist_setter=is_artist_setter,
        kwargs_to_ignore_in_repr=kwargs_to_ignore_in_repr,
        **kwargs
    )

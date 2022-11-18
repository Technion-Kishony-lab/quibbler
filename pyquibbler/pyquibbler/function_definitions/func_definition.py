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

    # inverse_funcs is a tuple specifying the inverse function for each argument of func
    inverse_funcs: Tuple[Optional[InverseFunc]] = field(repr=False, default_factory=tuple)


ElementWiseFuncDefinition.__hash__ = FuncDefinition.__hash__


def create_or_reuse_func_definition(base_func_definition: Optional[FuncDefinition] = None,
                                    raw_data_source_arguments: List[ArgId] = None,
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
                                    func_definition_cls: Optional[Type[FuncDefinition]] = None,
                                    kwargs_to_ignore_in_repr: Optional[Set[str]] = None,
                                    **kwargs) -> FuncDefinition:
    """
    Create a definition for a function from scratch or based on a specified `base_func_definition`.
    """
    raw_data_source_arguments = raw_data_source_arguments or []
    data_argument_designations = convert_raw_data_arguments_to_data_argument_designations(raw_data_source_arguments)
    if base_func_definition and (func_definition_cls is None or type(base_func_definition) == func_definition_cls):
        # use base_func_definition as the default upon which to make changes:
        bfd = base_func_definition
        func_definition = type(bfd)(
            is_random=is_random or bfd.is_random,
            is_graphics=is_graphics or bfd.is_graphics,
            is_file_loading=is_file_loading or bfd.is_file_loading,
            data_argument_designations=data_argument_designations or bfd.data_argument_designations,
            inverters=inverters or bfd.inverters,
            backwards_path_translators=backwards_path_translators or bfd.backwards_path_translators,
            forwards_path_translators=forwards_path_translators or bfd.forwards_path_translators,
            quib_function_call_cls=quib_function_call_cls or bfd.quib_function_call_cls,
            pass_quibs=pass_quibs or bfd.pass_quibs,
            result_type_or_type_translators=result_type_or_type_translators or bfd.result_type_or_type_translators,
            lazy=lazy or bfd.lazy,
            is_artist_setter=is_artist_setter or bfd.is_artist_setter,
            kwargs_to_ignore_in_repr=kwargs_to_ignore_in_repr or bfd.kwargs_to_ignore_in_repr,
            **kwargs
        )
        if func_definition == base_func_definition:
            return base_func_definition
        return func_definition
    else:
        # create a new definition from scratch:
        quib_function_call_cls = quib_function_call_cls or get_default_quib_func_call()
        func_definition_cls = func_definition_cls or FuncDefinition
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


FUNC_DEFINITION_DEFAULT = FuncDefinition(is_graphics=None)

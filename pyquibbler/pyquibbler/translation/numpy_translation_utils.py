import copy
from typing import Any, Union, Tuple, Dict

import numpy as np

from pyquibbler.function_definitions import KeywordArgument, SourceLocation
from pyquibbler.path import Path, deep_set, split_path_at_end_of_object, deep_get
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.types import Source
from pyquibbler.function_definitions.func_call import FuncCall, FuncArgsKwargs
from pyquibbler.utilities.general_utils import is_scalar_np, get_shared_shape, is_same_shapes
from pyquibbler.utilities.get_original_func import get_original_func
from pyquibbler.utilities.missing_value import missing, Missing

from pyquibbler.translation.translators.transpositional.types import IndexCode, is_focal_element
from pyquibbler.translation.translators.transpositional.exceptions import PyQuibblerRaggedArrayException

from numpy.typing import NDArray

IndexCodeArray = NDArray[Union[np.int64, IndexCode]]


def _convert_an_arg_to_array_of_source_index_codes(arg: Any,
                                                   focal_source: Union[Source, Missing] = missing,
                                                   path_to_source: Union[Path, Missing] = missing,
                                                   path_in_source: Union[Path, Missing] = missing,
                                                   convert_to_bool_mask: bool = False
                                                   ) -> Tuple[IndexCodeArray, Path, Path, Path]:
    """
    Convert a given arg to an array of int64 with values matching the linear indexing of focal_source,
    or specifying other elements according to IndexCode.
    returns:
     1. the array of index codes
     2. remaining path to source (if source is within an element in the array)
     3. path in source array
     4. remaining path in source (if the path_in_source includes deep referencing within an array element)
    """

    path_in_source_array = missing
    path_in_source_element = missing

    def _convert_obj_to_index_array(obj: Any, remaining_path_to_source: Path = missing) -> Tuple[IndexCodeArray, Path]:
        """
        convert obj to index array. returns the index array and the remaining path to the source.
        """
        nonlocal path_in_source_array, path_in_source_element

        is_focal_source = obj is focal_source
        if isinstance(obj, Source):
            obj = obj.value

        if is_focal_source:
            if is_scalar_np(obj):
                path_in_source_array, path_in_source_element = [], path_in_source
                return IndexCode.FOCAL_SOURCE_SCALAR, remaining_path_to_source

            full_index_array = np.arange(np.size(obj)).reshape(np.shape(obj))
            if path_in_source is missing:
                return full_index_array, remaining_path_to_source
            else:
                path_in_source_array, path_in_source_element, _ = split_path_at_end_of_object(full_index_array,
                                                                                              path_in_source)
                chosen_index_array = np.full(np.shape(obj), IndexCode.NON_CHOSEN_ELEMENT)
                deep_set(chosen_index_array, path_in_source_array, deep_get(full_index_array, path_in_source_array),
                         should_copy_objects_referenced=False)
                return chosen_index_array, remaining_path_to_source

        if is_scalar_np(obj):
            if remaining_path_to_source is missing:
                return IndexCode.SCALAR_NOT_CONTAINING_FOCAL_SOURCE, remaining_path_to_source
            path_in_source_array = []
            path_in_source_element = path_in_source
            return IndexCode.SCALAR_CONTAINING_FOCAL_SOURCE, remaining_path_to_source

        if isinstance(obj, np.ndarray):
            return np.full(np.shape(obj), IndexCode.OTHERS_ELEMENT), remaining_path_to_source

        if len(obj) == 0:
            return np.array(obj), remaining_path_to_source

        source_index = None if remaining_path_to_source is missing else remaining_path_to_source[0].component
        converted_sub_args = [None if source_index == sub_arg_index else
                              _convert_obj_to_index_array(sub_arg)[0] for sub_arg_index, sub_arg in enumerate(obj)]
        if remaining_path_to_source is not missing:
            converted_sub_args[source_index], remaining_path_to_source = \
                _convert_obj_to_index_array(obj[source_index], remaining_path_to_source[1:])

        shared_shape = get_shared_shape(converted_sub_args)

        for sub_arg_index, converted_sub_arg in enumerate(converted_sub_args):
            if converted_sub_arg.shape != shared_shape:
                if np.any(is_focal_element(converted_sub_arg)):
                    collapsed_sub_arg = np.full(shared_shape, IndexCode.LIST_CONTAINING_CHOSEN_ELEMENTS)
                    if path_in_source is not missing:
                        path_in_source_array, path_in_source_element, _ = \
                            split_path_at_end_of_object(collapsed_sub_arg, path_in_source)
                else:
                    collapsed_sub_arg = np.full(shared_shape, IndexCode.LIST_NOT_CONTAINING_CHOSEN_ELEMENTS)
                converted_sub_args[sub_arg_index] = collapsed_sub_arg
        return np.array(converted_sub_args), remaining_path_to_source

    arg_index_array, _remaining_path_to_source = _convert_obj_to_index_array(arg, path_to_source)
    if convert_to_bool_mask:
        arg_index_array = is_focal_element(arg_index_array)
    return arg_index_array, _remaining_path_to_source, path_in_source_array, path_in_source_element


def _convert_an_arg_or_multi_arg_to_array_of_source_index_codes(args: Union[Tuple[Any, ...], Any],
                                                                focal_source: Source = missing,
                                                                path_to_source: Path = missing,
                                                                path_in_source: Path = missing,
                                                                is_multi_arg: bool = False,
                                                                convert_to_bool_mask: bool = False) \
        -> Tuple[
            Union[Tuple[IndexCodeArray, ...], IndexCodeArray],
            Union[Path, Missing],
            Union[Path, Missing],
            Union[Path, Missing],
            ]:
    """
    Convert given arg(s) to an array of int64 with values matching the linear indexing of focal_source,
    or specifying other elements according to IndexCode.
    `args` can be a single data argument, or a list/tuple containing data arguments (for example, for np.concatenate)
    """
    if is_multi_arg:
        new_arg = []
        remaining_path_to_source, path_in_source_array, remaining_path_in_source = missing, missing, missing
        for index, arg in enumerate(args):
            if path_to_source[0].component == index:
                converted_arg, remaining_path_to_source, path_in_source_array, remaining_path_in_source = \
                    _convert_an_arg_to_array_of_source_index_codes(arg, focal_source,
                                                                   path_to_source[1:], path_in_source,
                                                                   convert_to_bool_mask=convert_to_bool_mask)
            else:
                converted_arg, _, _, _ = \
                    _convert_an_arg_to_array_of_source_index_codes(arg, convert_to_bool_mask=convert_to_bool_mask)
            new_arg.append(converted_arg)
        return tuple(new_arg), remaining_path_to_source, path_in_source_array, remaining_path_in_source
    return _convert_an_arg_to_array_of_source_index_codes(args, focal_source,
                                                          path_to_source, path_in_source,
                                                          convert_to_bool_mask=convert_to_bool_mask)


def convert_args_kwargs_to_source_index_codes(func_call: FuncCall,
                                              focal_source: Source,
                                              focal_source_location=SourceLocation,
                                              path_in_source: Path = missing,
                                              convert_to_bool_mask: bool = False,
                                              ) -> Tuple[FuncArgsKwargs, Path, Path, Path]:
    """
    Convert data arguments in args/kwargs to arrays of index codes for the indicated focal source.
    """
    args = list(func_call.args)
    kwargs = copy.copy(func_call.kwargs)
    is_concat = func_call.func is get_original_func(np.concatenate)
    remaining_path_to_source, path_in_source_array, remaining_path_in_source = missing, missing, missing
    for data_argument in func_call.func_definition.get_data_source_arguments(func_call.func_args_kwargs):
        if isinstance(data_argument, KeywordArgument):
            args_or_kwargs = kwargs
            element_in_args_or_kwargs = data_argument.keyword
        else:
            args_or_kwargs = args
            element_in_args_or_kwargs = data_argument.index
        if focal_source_location.argument == data_argument:
            index_array, remaining_path_to_source, path_in_source_array, remaining_path_in_source = \
                _convert_an_arg_or_multi_arg_to_array_of_source_index_codes(
                    args_or_kwargs[element_in_args_or_kwargs], focal_source,
                    path_to_source=focal_source_location.path, path_in_source=path_in_source,
                    is_multi_arg=is_concat, convert_to_bool_mask=convert_to_bool_mask)
        else:
            index_array, _, _, _ = \
                _convert_an_arg_or_multi_arg_to_array_of_source_index_codes(
                    args_or_kwargs[element_in_args_or_kwargs],
                    is_multi_arg=is_concat, convert_to_bool_mask=convert_to_bool_mask)

        args_or_kwargs[element_in_args_or_kwargs] = index_array

    return FuncArgsKwargs(func_call.func, tuple(args), kwargs), \
        remaining_path_to_source, path_in_source_array, remaining_path_in_source


def run_func_call_with_new_args_kwargs(func_call: FuncCall, func_args_kwargs: FuncArgsKwargs) -> np.ndarray:
    """
    Runs the function with the given args, kwargs
    """
    return SourceFuncCall.from_(func_args_kwargs.func, func_args_kwargs.args, func_args_kwargs.kwargs,
                                func_definition=func_call.func_definition,
                                data_source_locations=[],
                                parameter_source_locations=func_call.parameter_source_locations).run()

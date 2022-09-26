from typing import Any, Union, Tuple

import numpy as np

from pyquibbler.function_definitions import KeywordArgument, SourceLocation
from pyquibbler.path import Path
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.types import Source
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.utilities.general_utils import is_same_shapes, is_scalar_np
from pyquibbler.utilities.get_original_func import get_original_func
from pyquibbler.utilities.missing_value import missing

from .types import IndexCode, _non_focal_source_scalar, MAXIMAL_NON_FOCAL_SOURCE


def convert_arg_and_source_to_array_of_indices(arg: Any,
                                               focal_source: Source,
                                               path_to_source: Path,
                                               path_in_source: Any = missing) -> np.ndarray:
    """
    Convert arg to an array of int64 with values matching the linear indexing of focal_source,
    or specifying other elements according to IndexCode.
    """
    is_focal_source = arg is focal_source
    is_source = isinstance(arg, Source)
    if is_source:
        arg = arg.value

    if is_focal_source:
        if is_scalar_np(arg):
            return IndexCode.FOCAL_SOURCE_SCALAR
        if path_in_source is missing:
            return np.arange(np.size(arg)).reshape(np.shape(arg))
        else:
            val = np.full(np.shape(arg), IndexCode.NON_CHOSEN_ELEMENT)
            val[path_in_source] = IndexCode.CHOSEN_ELEMENT
            return val

    if is_scalar_np(arg):
        return _non_focal_source_scalar(focal_source is not missing)

    if isinstance(arg, np.ndarray):
        return np.full(np.shape(arg), IndexCode.OTHERS_ELEMENT)

    converted_sub_args = []
    for sub_arg_index, sub_arg in enumerate(arg):
        if path_to_source is missing or path_to_source[0].component != sub_arg_index:
            source_ = missing
            path_ = missing
        else:
            source_ = focal_source
            path_ = path_to_source[1:]
        converted_sub_args.append(
            convert_arg_and_source_to_array_of_indices(sub_arg, source_, path_, path_in_source))
    if is_same_shapes(converted_sub_args):
        return np.array(converted_sub_args)

    return np.array([
        _non_focal_source_scalar(np.any(sub_arg > MAXIMAL_NON_FOCAL_SOURCE))
        for sub_arg in converted_sub_args])


def convert_args_and_source_to_arrays_of_indices(args: Any,
                                                 focal_source: Source,
                                                 path_to_source: Path,
                                                 path_in_source: Any = missing,
                                                 is_multi_arg: bool = False) \
        -> Union[Tuple[np.ndarray, ...], np.ndarray]:

    if is_multi_arg:
        new_arg = []
        for index, arg in enumerate(args):
            if path_to_source[0].component == index:
                path_ = path_to_source[1:]
                source_ = focal_source
            else:
                path_ = missing
                source_ = missing
            new_arg.append(convert_arg_and_source_to_array_of_indices(arg, source_, path_, path_in_source))
        return tuple(new_arg)
    return convert_arg_and_source_to_array_of_indices(
        args, focal_source, path_to_source, path_in_source)


def get_data_source_indices(func_call: FuncCall,
                            focal_source: Source,
                            focal_source_location=SourceLocation,
                            path_in_source: Any = missing) -> np.ndarray:
    """
    Runs the function with the source replaced with array of linear indices
    """

    args = list(func_call.args)
    kwargs = func_call.kwargs
    is_concat = func_call.func is get_original_func(np.concatenate)
    path_to_source = focal_source_location
    for data_argument in func_call.func_definition.get_data_source_arguments(func_call.func_args_kwargs):
        if isinstance(data_argument, KeywordArgument):
            args_or_kwargs = kwargs
            element_in_args_or_kwargs = data_argument.keyword
        else:
            args_or_kwargs = args
            element_in_args_or_kwargs = data_argument.index
        if focal_source_location.argument == data_argument:
            path_to_source = focal_source_location.path
        else:
            path_to_source = missing
        args_or_kwargs[element_in_args_or_kwargs] = convert_args_and_source_to_arrays_of_indices(
            args_or_kwargs[element_in_args_or_kwargs],
            missing if path_to_source is missing else focal_source, path_to_source, path_in_source, is_concat)

    return SourceFuncCall.from_(func_call.func, args, kwargs,
                                func_definition=func_call.func_definition,
                                data_source_locations=[],
                                parameter_source_locations=func_call.parameter_source_locations).run()


def get_data_source_mask(func_call: FuncCall,
                         focal_source: Source,
                         focal_source_location: SourceLocation,
                         indices: np.ndarray) -> np.ndarray:
    """
    Runs the function with True at the source position
    """
    data_source_index_code = get_data_source_indices(func_call, focal_source, focal_source_location, indices)
    return data_source_index_code > MAXIMAL_NON_FOCAL_SOURCE

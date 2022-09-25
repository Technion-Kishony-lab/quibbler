from typing import Any, Union, Tuple

import numpy as np

from pyquibbler.function_definitions import KeywordArgument
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.types import Source
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.utilities.general_utils import is_same_shapes, is_scalar_np
from pyquibbler.utilities.get_original_func import get_original_func
from pyquibbler.utilities.iterators import is_focal_object_in_object, get_paths_for_object
from pyquibbler.utilities.missing_value import missing

from .types import IndexCode, _non_focal_source_scalar, MAXIMAL_NON_FOCAL_SOURCE


def convert_arg_and_source_to_array_of_indices(arg: Any,
                                               focal_source: Source,
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
        # a non-source scalar can contain the focal source (for example if arg is dict):
        # TODO: is_focal_object_in_object search could be avoided using the known source location
        return _non_focal_source_scalar(not is_source and is_focal_object_in_object(focal_source, arg))

    if isinstance(arg, np.ndarray):
        return np.full(np.shape(arg), IndexCode.OTHERS_ELEMENT)

    converted_sub_args = [convert_arg_and_source_to_array_of_indices(sub_arg, focal_source) for sub_arg in arg]
    if is_same_shapes(converted_sub_args):
        return np.array(converted_sub_args)

    return np.array([
        _non_focal_source_scalar(np.any(sub_arg > MAXIMAL_NON_FOCAL_SOURCE))
        for sub_arg in converted_sub_args])


def convert_args_and_source_to_arrays_of_indices(args: Any,
                                                 focal_source: Source,
                                                 path_in_source: Any = missing,
                                                 is_multi_arg: bool = False) \
        -> Union[Tuple[np.ndarray, ...], np.ndarray]:

    if is_multi_arg:
        return tuple(convert_arg_and_source_to_array_of_indices(arg, focal_source, path_in_source) for arg in args)
    return convert_arg_and_source_to_array_of_indices(args, focal_source, path_in_source)


def get_data_source_indices(func_call: FuncCall, focal_source: Source, path_in_source: Any = missing) -> np.ndarray:
    """
    Runs the function with the source replaced with array of linear indices
    """

    args = list(func_call.args)
    kwargs = func_call.kwargs
    is_concat = func_call.func is get_original_func(np.concatenate)

    for data_argument in func_call.func_definition.get_data_source_arguments(func_call.func_args_kwargs):
        if isinstance(data_argument, KeywordArgument):
            args_or_kwargs = kwargs
            element_in_args_or_kwargs = data_argument.keyword
        else:
            args_or_kwargs = args
            element_in_args_or_kwargs = data_argument.index
        args_or_kwargs[element_in_args_or_kwargs] = convert_args_and_source_to_arrays_of_indices(
            args_or_kwargs[element_in_args_or_kwargs], focal_source, path_in_source, is_concat)

    return SourceFuncCall.from_(func_call.func, args, kwargs,
                                func_definition=func_call.func_definition,
                                data_source_locations=[],
                                parameter_source_locations=func_call.parameter_source_locations).run()


def get_data_source_mask(func_call: FuncCall, focal_source: Source, indices: np.ndarray) -> np.ndarray:
    """
    Runs the function with True at the source position
    """
    data_source_index_code = get_data_source_indices(func_call, focal_source, indices)
    return data_source_index_code > MAXIMAL_NON_FOCAL_SOURCE

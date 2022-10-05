from typing import Any, Union, Tuple, Dict

import numpy as np

from pyquibbler.function_definitions import KeywordArgument, SourceLocation
from pyquibbler.path import Path
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.types import Source
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.utilities.general_utils import is_scalar_np, get_shared_shape
from pyquibbler.utilities.get_original_func import get_original_func
from pyquibbler.utilities.missing_value import missing, Missing

from .types import IndexCode, _non_focal_source_scalar, MAXIMAL_NON_FOCAL_SOURCE
from numpy.typing import NDArray


def _convert_an_arg_to_array_of_source_index_codes(arg: Any,
                                                   focal_source: Union[Source, Missing] = missing,
                                                   path_to_source: Union[Path, Missing] = missing,
                                                   path_in_source: Union[Any, Missing] = missing
                                                   ) -> Tuple[NDArray[Union[np.int64, IndexCode]], Path]:
    """
    Convert a given arg to an array of int64 with values matching the linear indexing of focal_source,
    or specifying other elements according to IndexCode.
    """
    is_focal_source = arg is focal_source
    is_source = isinstance(arg, Source)
    if is_source:
        arg = arg.value

    if is_focal_source:
        if is_scalar_np(arg):
            return IndexCode.FOCAL_SOURCE_SCALAR, path_to_source
        if path_in_source is missing:
            return np.arange(np.size(arg)).reshape(np.shape(arg)), path_to_source
        else:
            val = np.full(np.shape(arg), IndexCode.NON_CHOSEN_ELEMENT)
            val[path_in_source] = IndexCode.CHOSEN_ELEMENT
            return val, path_to_source

    if is_scalar_np(arg):
        return _non_focal_source_scalar(focal_source is not missing), path_to_source

    if isinstance(arg, np.ndarray):
        return np.full(np.shape(arg), IndexCode.OTHERS_ELEMENT), path_to_source

    converted_sub_args = []
    source_index = None if path_to_source is missing else path_to_source[0].component
    for sub_arg_index, sub_arg in enumerate(arg):
        if source_index != sub_arg_index:
            converted_sub_arg, _ = \
                _convert_an_arg_to_array_of_source_index_codes(sub_arg)
        else:
            converted_sub_arg, new_path_to_source = \
                _convert_an_arg_to_array_of_source_index_codes(sub_arg, focal_source, path_to_source[1:],
                                                               path_in_source)
        converted_sub_args.append(converted_sub_arg)

    shared_shape = get_shared_shape(converted_sub_args)

    if path_to_source is not missing:
        path_to_source = path_to_source[len(path_to_source) - len(new_path_to_source)
                                        - (len(shared_shape) - len(converted_sub_args[source_index].shape)):]
    for sub_arg_index, converted_sub_arg in enumerate(converted_sub_args):
        if converted_sub_arg.shape != shared_shape:
            converted_sub_args[sub_arg_index] = \
                np.full(shared_shape, _non_focal_source_scalar(np.any(converted_sub_arg > MAXIMAL_NON_FOCAL_SOURCE)))

    return np.array(converted_sub_args), path_to_source


def _convert_an_arg_or_multi_arg_to_array_of_source_index_codes(args: Any,
                                                                focal_source: Source,
                                                                path_to_source: Path,
                                                                path_in_source: Any = missing,
                                                                is_multi_arg: bool = False) \
        -> Tuple[Union[Tuple[np.ndarray, ...], np.ndarray], Path]:
    """
    Convert given arg(s) to an array of int64 with values matching the linear indexing of focal_source,
    or specifying other elements according to IndexCode.
    `args` can be a single data argument, or a list/tuple containing data arguments (for example, for np.concatenate)
    """
    if is_multi_arg:
        new_arg = []
        remaining_path = missing
        for index, arg in enumerate(args):
            if path_to_source[0].component == index:
                converted_arg, remaining_path = \
                    _convert_an_arg_to_array_of_source_index_codes(arg, focal_source, path_to_source[1:],
                                                                   path_in_source)
            else:
                converted_arg, _ = \
                    _convert_an_arg_to_array_of_source_index_codes(arg)
            new_arg.append(converted_arg)
        return tuple(new_arg), remaining_path
    return _convert_an_arg_to_array_of_source_index_codes(args, focal_source, path_to_source, path_in_source)


def convert_args_kwargs_to_source_index_codes(func_call: FuncCall,
                                              focal_source: Source,
                                              focal_source_location=SourceLocation,
                                              path_in_source: Any = missing,
                                              ) -> Tuple[Tuple[Any], Dict[str, Any], Path]:
    """
    Convert data arguments in args/kwargs to arrays of index codes for the indicated focal source.
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
        if focal_source_location.argument == data_argument:
            path_to_source = focal_source_location.path
        else:
            path_to_source = missing
        args_or_kwargs[element_in_args_or_kwargs], remaining_path = _convert_an_arg_or_multi_arg_to_array_of_source_index_codes(
            args_or_kwargs[element_in_args_or_kwargs], missing if path_to_source is missing else focal_source,
            path_to_source, path_in_source, is_concat)

        return tuple(args), kwargs, remaining_path


def run_func_call_with_new_args_kwargs(func_call: FuncCall, args: Tuple[Any], kwargs: Dict[str, Any]) -> np.ndarray:
    """
    Runs the function with the given args, kwargs
    """
    return SourceFuncCall.from_(func_call.func, args, kwargs,
                                func_definition=func_call.func_definition,
                                data_source_locations=[],
                                parameter_source_locations=func_call.parameter_source_locations).run()

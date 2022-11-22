import copy
from dataclasses import dataclass
import numpy as np

from functools import wraps

from typing import Any, Union, Tuple, Optional

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path import Path, deep_set, split_path_at_end_of_object, deep_get
from pyquibbler.function_definitions.func_call import FuncCall, FuncArgsKwargs
from pyquibbler.utilities.general_utils import get_shared_shape, is_same_shapes
from pyquibbler.assignment.utils import is_scalar_np

from .array_index_codes import INDEX_TYPE, IndexCode, is_focal_element, IndexCodeArray
from .exceptions import PyQuibblerRaggedArrayException
from .source_func_call import SourceFuncCall
from .types import Source

ALLOW_RAGGED_ARRAYS = True


def convert_an_arg_to_array_of_source_index_codes(arg: Any,
                                                  focal_source: Optional[Source] = None,
                                                  path_to_source: Optional[Path] = None,
                                                  path_in_source: Optional[Path] = None,
                                                  ) \
        -> Tuple[IndexCodeArray, Optional[Path], Optional[Path], Optional[Path], Optional[bool]]:
    """
    Convert a given arg to an IndexCodeArray, which is an array of INDEX_TYPE with values either matching
    the linear indexing of focal_source, or specifying other elements according to IndexCode.

    Parameters
    ----------
        `arg`: an object to convert to an index-code array, can be a scalar, an array,
        or array-like (nested lists, tuples, arrays). This is typically the data argument of a numpy function.
        `arg` can be, or contain Sources.

        focal_source: the source whose indexes we want to encode.
            If `None`, the array will be encoded fully as IndexCode.OTHERS_ELEMENT.

        path_to_source: the path to the focal source. `None` for no focal source.

        path_in_source: a path in the focal source specifying chosen array elements, to be encoded as
            linear indices.  Source elements not in the path_in_source, are encoded as IndexCode.NON_CHOSEN_ELEMENT
            If `None`, all elements are encoded as indices.

        convert_to_bool_mask: a bool indicating whether to convert the array to boolean mask designating True for
            chosen source array elements, False otherwise.

    Returns
    -------
     1. arg_index_array:
            The index-code array representing `arg`

     2. remaining_path_to_source
        Remaining path to the source. If source is part of the array, the remaining path is []. If the source is
        a minor source, not part of the array but rather included within an element of the array, then the
        remaining_path_to_source is the path from the array element to the source.

     3 and 4. path_in_source_array, path_in_source_element
        The input parameter path_in_source, is broken into path_in_source_array, path_in_source_element,
        representing the part of the path that is within the source array, and the part, if any, that is
        within an element of the source array.
    """

    path_in_source_array: Optional[Path] = None
    path_in_source_element: Optional[Path] = None
    is_extracting_element_out_of_source_array: Optional[bool] = None

    def _convert_obj_to_index_array(obj: Any, _remaining_path_to_source: Path = None) -> \
            Tuple[Union[IndexCode, IndexCodeArray], Optional[Path]]:
        """
        convert obj to index array. returns the index array and the remaining path to the source.
        """
        nonlocal path_in_source_array, path_in_source_element, is_extracting_element_out_of_source_array

        is_focal_source = obj is focal_source
        if isinstance(obj, Source):
            obj = obj.value

        if is_focal_source:
            if is_scalar_np(obj):
                path_in_source_array, path_in_source_element = [], path_in_source
                is_extracting_element_out_of_source_array = True
                return IndexCode.FOCAL_SOURCE_SCALAR, _remaining_path_to_source

            full_index_array = np.arange(np.size(obj), dtype=INDEX_TYPE).reshape(np.shape(obj))
            if path_in_source is None:
                chosen_index_array = full_index_array
            else:
                path_in_source_array, path_in_source_element, referenced_part_of_source_array = \
                    split_path_at_end_of_object(full_index_array, path_in_source)
                is_extracting_element_out_of_source_array = is_scalar_np(referenced_part_of_source_array)
                chosen_index_array = np.full(np.shape(obj), IndexCode.NON_CHOSEN_ELEMENT)
                deep_set(chosen_index_array, path_in_source_array, deep_get(full_index_array, path_in_source_array),
                         should_copy_objects_referenced=False)
            return chosen_index_array, _remaining_path_to_source
            # index_coded_source_value = de_array_by_template(chosen_index_array, obj)
            # return index_coded_source_value, _remaining_path_to_source

        if is_scalar_np(obj):
            if _remaining_path_to_source is None:
                return IndexCode.SCALAR_NOT_CONTAINING_FOCAL_SOURCE, _remaining_path_to_source
            path_in_source_array = []
            path_in_source_element = path_in_source
            return IndexCode.SCALAR_CONTAINING_FOCAL_SOURCE, _remaining_path_to_source

        if isinstance(obj, np.ndarray):
            return np.full(np.shape(obj), IndexCode.OTHERS_ELEMENT), _remaining_path_to_source

        if len(obj) == 0:
            return np.array(obj, dtype=INDEX_TYPE), _remaining_path_to_source

        source_index = None if _remaining_path_to_source is None else _remaining_path_to_source[0].component
        converted_sub_args = [None if source_index == sub_arg_index else
                              _convert_obj_to_index_array(sub_arg)[0] for sub_arg_index, sub_arg in enumerate(obj)]
        if _remaining_path_to_source is not None:
            converted_sub_args[source_index], _remaining_path_to_source = \
                _convert_obj_to_index_array(obj[source_index], _remaining_path_to_source[1:])

        if not is_same_shapes(converted_sub_args):
            # If the arrays are not same shape, their size will be squashed by numpy, yielding an object array
            # containing the squashed arrays.  We simulate that by an array with elements coded as
            # IndexCode.LIST_CONTAINING_CHOSEN_ELEMENTS, or IndexCode.LIST_NOT_CONTAINING_CHOSEN_ELEMENTS
            if not ALLOW_RAGGED_ARRAYS:
                raise PyQuibblerRaggedArrayException()

            shared_shape = get_shared_shape(converted_sub_args)

            for sub_arg_index, converted_sub_arg in enumerate(converted_sub_args):
                if np.shape(converted_sub_arg) != shared_shape:
                    if np.any(is_focal_element(converted_sub_arg)):
                        collapsed_sub_arg = np.full(shared_shape, IndexCode.LIST_CONTAINING_CHOSEN_ELEMENTS)
                        if path_in_source is not None:
                            path_in_source_array, path_in_source_element, _ = \
                                split_path_at_end_of_object(collapsed_sub_arg, path_in_source)
                    else:
                        collapsed_sub_arg = np.full(shared_shape, IndexCode.LIST_NOT_CONTAINING_CHOSEN_ELEMENTS)
                    converted_sub_args[sub_arg_index] = collapsed_sub_arg

        return np.array(converted_sub_args), _remaining_path_to_source

    arg_index_array, remaining_path_to_source = _convert_obj_to_index_array(arg, path_to_source)

    return arg_index_array, remaining_path_to_source, path_in_source_array, path_in_source_element, \
        is_extracting_element_out_of_source_array


def convert_args_before_run(func):

    @wraps(func)
    def wrapper(self, *arg, **kwargs):
        if self._func_args_kwargs is None:
            self.convert_data_arguments_to_source_index_codes()

        return func(self, *arg, **kwargs)

    return wrapper


@dataclass
class ArrayPathTranslator:
    """
    Convert the data arguments of a function call (func)call) to index code arrays (IndexCodeArray), representing
    the linear indexing of focal_source, or specifying other elements according to IndexCode.

    See more explanations in convert_an_arg_to_array_of_source_index_codes (above)
    """

    func_call: FuncCall
    focal_source: Source = None
    focal_source_location: SourceLocation = None
    path_in_source: Path = None
    convert_to_bool_mask: bool = False

    # Output:
    _remaining_path_to_source: Path = None
    _path_in_source_array: Path = None
    _path_in_source_element: Path = None
    _is_extracting_element_out_of_source_array: bool = None
    _func_args_kwargs: FuncArgsKwargs = None

    def _convert_an_arg_to_array_of_source_index_codes(self, arg: Any, path_to_source: Optional[Path] = None,
                                                       ) -> IndexCodeArray:
        arg_index_array, remaining_path_to_source, path_in_source_array, path_in_source_element,\
            is_extracting_element_out_of_source_array = \
            convert_an_arg_to_array_of_source_index_codes(arg, self.focal_source, path_to_source, self.path_in_source)
        if path_to_source is not None:
            self._path_in_source_array = path_in_source_array
            self._path_in_source_element = path_in_source_element
            self._remaining_path_to_source = remaining_path_to_source
            self._is_extracting_element_out_of_source_array = is_extracting_element_out_of_source_array

        if self.convert_to_bool_mask:
            arg_index_array = is_focal_element(arg_index_array)
        return arg_index_array

    def create_new_func_args_kwargs(self):
        self._func_args_kwargs = FuncArgsKwargs(self.func_call.func, args=list(self.func_call.args),
                                                kwargs=copy.copy(self.func_call.kwargs))
        return self._func_args_kwargs

    def convert_a_data_argument(self, data_argument):
        """
        Convert a given data argument in args/kwargs to arrays of index codes for the indicated focal source.
        """
        data_argument_value = self._func_args_kwargs.get_arg_value_by_argument(data_argument)
        path_to_source = self.focal_source_location.get_path_in_argument(data_argument)
        index_array = self._convert_an_arg_to_array_of_source_index_codes(data_argument_value, path_to_source)
        self._func_args_kwargs.set_arg_value_by_argument(index_array, data_argument)

    def convert_data_arguments_to_source_index_codes(self):
        """
        Convert all data arguments in args/kwargs to arrays of index codes for the indicated focal source.
        """
        self.create_new_func_args_kwargs()
        for data_argument in self.func_call.func_definition.get_data_arguments(self.func_call.func_args_kwargs):
            self.convert_a_data_argument(data_argument)

    @convert_args_before_run
    def get_func_args_kwargs(self) -> FuncArgsKwargs:
        return self._func_args_kwargs

    @convert_args_before_run
    def get_path_from_array_element_to_source(self):
        return self._remaining_path_to_source

    @convert_args_before_run
    def get_path_in_source_array(self):
        return self._path_in_source_array

    @convert_args_before_run
    def get_path_in_source_element(self):
        return self._path_in_source_element

    @convert_args_before_run
    def get_source_path_split_at_end_of_array(self):
        return self._path_in_source_array, self._path_in_source_element

    @convert_args_before_run
    def get_is_extracting_element_out_of_source_array(self):
        return self._is_extracting_element_out_of_source_array

    @convert_args_before_run
    def get_masked_data_arguments(self):
        """
        a list of the data arguments as masked arrays
        """
        return [
            self._func_args_kwargs.get_arg_value_by_argument(argument) for
            argument in self.func_call.func_definition.get_data_arguments(self.func_call.func_args_kwargs)
        ]

    @convert_args_before_run
    def get_masked_data_argument_of_source(self):
        """
        the index-converted data argument of the focal source
        """
        return self._func_args_kwargs.get_arg_value_by_argument(self.focal_source_location.argument)


def run_func_call_with_new_args_kwargs(func_call: FuncCall, func_args_kwargs: FuncArgsKwargs) -> np.ndarray:
    """
    Runs the function with the given args, kwargs
    """
    return SourceFuncCall.from_(func_args_kwargs.func, func_args_kwargs.args, func_args_kwargs.kwargs,
                                func_definition=func_call.func_definition,
                                data_source_locations=[],
                                parameter_source_locations=func_call.parameter_source_locations).run()

import functools
from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional, Type

import numpy as np
from numpy.typing import NDArray

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path import Path, Paths, PathComponent, split_path_at_end_of_object, deep_set, SpecialComponent
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices, Shape
from pyquibbler.utilities.numpy_original_functions import np_True, np_zeros, np_sum
from pyquibbler.assignment.utils import is_scalar_np

from ..source_func_call import SourceFuncCall
from ..array_index_codes import IndexCode, is_focal_element
from ..base_translators import BackwardsPathTranslator, ForwardsPathTranslator
from ..array_translation_utils import ArrayPathTranslator
from ..types import Source
from ..array_index_codes import INDEX_TYPE


@dataclass
class Arg:
    name: str

    def get_value(self, arg_dict: Dict[str, Any]) -> Any:
        return arg_dict[self.name]


@dataclass
class ArgWithDefault(Arg):
    default: Any

    def get_value(self, arg_dict: Dict[str, Any]) -> Any:
        return arg_dict.get(self.name, self.default)


def calculate_result_bool_mask_before_run(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._result_bool_mask is None:
            self._calculate_result_bool_mask_and_split_path()
        return func(self, *args, **kwargs)

    return wrapper


class NumpyBackwardsPathTranslator(BackwardsPathTranslator):
    """
    Holds basic logic for how to backwards translate a path for numpy functions- subclass this for any translator of a
    numpy function.
    Mainly concerns surrounding logic with deep paths
    """

    TRANSLATION_RELATED_ARGS: List[Arg] = []

    def __init__(self, func_call: SourceFuncCall, shape: Optional[Shape], type_: Optional[Type], path: Path):
        super().__init__(func_call, shape, type_, path)
        self._result_bool_mask: Optional[NDArray[bool]] = None
        self._path_in_array: Optional[Path] = None
        self._remaining_path: Optional[Path] = None
        self._is_getting_element_out_of_array: Optional[bool] = None

    @abstractmethod
    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[INDEX_TYPE], NDArray[bool]]:
        """
        Return two same-size nd-arrays:
        (1) an array of index codes of the source
        (2) a mask indicating chosen elements.
        These arrays must be of the same size but they do not need to be at the size of the function argument.
        For example, for some converters, like np.concat, it is easier to return these at the size of the result.
        """
        pass

    def _get_translation_related_arg_dict(self):
        arg_dict = {key: val for key, val in self._func_call.func_args_kwargs.get_arg_values_by_keyword().items()
                    if not isinstance(val, np._globals._NoValueType)}
        return {arg.name: arg.get_value(arg_dict) for arg in self.TRANSLATION_RELATED_ARGS}

    def _get_source_path(self, source: Source, location: SourceLocation) -> Path:

        data_argument_to_source_index_code_converter = \
            ArrayPathTranslator(func_call=self._func_call, focal_source=source,
                                focal_source_location=location, convert_to_bool_mask=False)

        source_index_array, chosen_elements = \
            self._get_indices_in_source(data_argument_to_source_index_code_converter, self._result_bool_mask)

        source_indices = source_index_array[chosen_elements & is_focal_element(source_index_array)]

        if np.size(source_indices) == 0:
            # Source not part of result
            return None

        if np.any(source_indices == IndexCode.SCALAR_CONTAINING_FOCAL_SOURCE):
            # The entire source is needed, contained in one element of the array (minor-source)
            return []

        if np.any(source_indices == IndexCode.FOCAL_SOURCE_SCALAR):
            # The entire source is needed as one element of the array (uni-source)
            return []

        mask = create_bool_mask_with_true_at_indices((np.size(source.value),), source_indices)
        mask = mask.reshape(np.shape(source.value))
        if np.array_equal(mask, np.array(True)):
            source_path = []
        else:
            if np_sum(mask) == 1 and self._is_getting_element_out_of_array:
                indices = tuple(x[0] for x in np.nonzero(mask))
                source_path = [PathComponent(indices)]
            else:
                source_path = [PathComponent(mask)]

        return source_path

    def _calculate_result_bool_mask_and_split_path(self):
        result_bool_mask = np_zeros(self._shape, dtype=bool)
        self._path_in_array, self._remaining_path, extracted_result = \
            split_path_at_end_of_object(result_bool_mask, self._path)
        deep_set(result_bool_mask, self._path_in_array, True, should_copy_objects_referenced=False)
        self._result_bool_mask = result_bool_mask
        self._is_getting_element_out_of_array = is_scalar_np(extracted_result)

    @calculate_result_bool_mask_before_run
    def get_result_bool_mask_and_split_path(self):
        return self._result_bool_mask, self._path_in_array, self._remaining_path

    @calculate_result_bool_mask_before_run
    def is_getting_element_out_of_array(self):
        return self._is_getting_element_out_of_array

    @calculate_result_bool_mask_before_run
    def _backwards_translate(self) -> Dict[Source, Path]:
        sources_to_paths = {}
        for source, location in zip(self._func_call.get_data_sources(), self._func_call.data_source_locations):
            source_path = self._get_source_path(source, location)
            if source_path is not None:
                sources_to_paths[source] = source_path + self._remaining_path

        return sources_to_paths


class NumpyForwardsPathTranslator(ForwardsPathTranslator):
    """
    Basic logic for forward translating a path for numpy functions.
    Converts the data arguments to boolean arrays with indicating the affected elements in the source.

    sub-classes should encode the mapping from this boolean mask of the data arguments to a boolean mask the shape
    of the target, indicating affected elements in the target.
    """

    ADD_OUT_OF_ARRAY_COMPONENT = False

    @abstractmethod
    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        Forward translate boolean masks of the data sources (indicating the affected element)
        to a boolean mask of the function output.

        sub-methods can use either masked_data_arguments, which is a list containing the masks of the data arguments,
        or the masked_func_args_kwargs, where the data args have been replaced with their boolean masks.
        """
        pass

    def _forward_translate(self) -> Paths:

        data_argument_to_mask_converter = \
            ArrayPathTranslator(func_call=self._func_call, focal_source=self._source,
                                focal_source_location=self._source_location, path_in_source=self._path,
                                convert_to_bool_mask=True)

        remaining_path_to_source = data_argument_to_mask_converter.get_path_from_array_element_to_source()
        path_in_source_array, path_in_source_element = \
            data_argument_to_mask_converter.get_source_path_split_at_end_of_array()

        result_mask = \
            self.forward_translate_masked_data_arguments_to_result_mask(data_argument_to_mask_converter)

        if not np.any(result_mask):
            return []

        if result_mask is True or result_mask is np_True:
            # our func has extracted an element out of the array
            within_target_array_path = []
            if len(path_in_source_element) > 0 and path_in_source_element[0].component is SpecialComponent.OUT_OF_ARRAY:
                path_in_source_element.pop(0)
        else:
            within_target_array_path = [
                PathComponent(result_mask)
            ]
            if self.ADD_OUT_OF_ARRAY_COMPONENT and \
                    data_argument_to_mask_converter.get_is_extracting_element_out_of_source_array():
                within_target_array_path += [PathComponent(SpecialComponent.OUT_OF_ARRAY)]
        return [within_target_array_path + remaining_path_to_source + path_in_source_element]

from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

import numpy as np
from numpy.typing import NDArray

from pyquibbler.path import Path, Paths, PathComponent, split_path_at_end_of_object, deep_set
from pyquibbler.translation.array_index_codes import IndexCode, is_focal_element
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_path, \
    create_bool_mask_with_true_at_indices, is_scalar_np
from pyquibbler.utilities.numpy_original_functions import np_True, np_zeros, np_sum

from pyquibbler.translation.base_translators import BackwardsPathTranslator, ForwardsPathTranslator
from pyquibbler.translation.array_translation_utils import ArrayPathTranslator
from pyquibbler.translation.types import Source


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


class NumpyBackwardsPathTranslator(BackwardsPathTranslator):
    """
    Holds basic logic for how to backwards translate a path for numpy functions- subclass this for any translator of a
    numpy function.
    Mainly concerns surrounding logic with deep paths
    """

    TRANSLATION_RELATED_ARGS: List[Arg] = []

    @abstractmethod
    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[np.int64], NDArray[bool]]:
        """
        Return two same-size nd-arrays:
        (1) an array of index codes of the source
        (2) a mask indicating chosen elements.
        """
        pass

    def _get_translation_related_arg_dict(self):
        arg_dict = {key: val for key, val in self._func_call.func_args_kwargs.get_arg_values_by_keyword().items()
                    if not isinstance(val, np._globals._NoValueType)}
        return {arg.name: arg.get_value(arg_dict) for arg in self.TRANSLATION_RELATED_ARGS}

    def backwards_translate(self) -> Dict[Source, Path]:
        sources_to_paths = {}
        for source, location in zip(self._func_call.get_data_sources(), self._func_call.data_source_locations):
            data_argument_to_source_index_code_converter = \
                ArrayPathTranslator(func_call=self._func_call, focal_source=source,
                                    focal_source_location=location, convert_to_bool_mask=False)

            result_bool_mask = np_zeros(self._shape, dtype=bool)
            path_in_array, path_within_array_element, extracted_result_mask = \
                split_path_at_end_of_object(result_bool_mask, self._path)
            deep_set(result_bool_mask, path_in_array, True, should_copy_objects_referenced=False)

            source_index_array, chosen_elements = \
                self._get_indices_in_source(data_argument_to_source_index_code_converter, result_bool_mask)

            source_indices = source_index_array[chosen_elements & is_focal_element(source_index_array)]

            if np.size(source_indices) == 0:
                # Source not part of result
                source_path = None

            elif np.any(source_indices == IndexCode.SCALAR_CONTAINING_FOCAL_SOURCE):
                # The entire source is needed, contained in one element of the array (minor-source)
                source_path = []

            elif np.any(source_indices == IndexCode.FOCAL_SOURCE_SCALAR):
                # The entire source is needed as one element of the array (uni-source)
                source_path = []

            else:
                mask = create_bool_mask_with_true_at_indices((np.size(source.value),), source_indices)
                mask = mask.reshape(np.shape(source.value))
                if np.array_equal(mask, np.array(True)):
                    source_path = []
                else:
                    if np_sum(mask) == 1 and is_scalar_np(extracted_result_mask):
                        indices = tuple(x[0] for x in np.nonzero(mask))
                        source_path = [PathComponent(indices)]
                    else:
                        source_path = [PathComponent(mask)]

            if source_path is not None:
                sources_to_paths[source] = source_path + path_within_array_element

        return sources_to_paths


class NumpyForwardsPathTranslator(ForwardsPathTranslator):
    """
    Basic logic for forward translating a path for numpy functions.
    Converts the data arguments to boolean arrays with indicating the affected elements in the source.

    sub-classes should encode the mapping from this boolean mask of the data arguments to a boolean mask the shape
    of the target, indicating affected elements in the target.
    """

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = False

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

    def forward_translate(self) -> Paths:

        data_argument_to_mask_converter = \
            ArrayPathTranslator(func_call=self._func_call, focal_source=self._source,
                                focal_source_location=self._source_location, path_in_source=self._path,
                                convert_to_bool_mask=True)

        remaining_path_to_source = data_argument_to_mask_converter.get_path_from_array_element_to_source()
        within_source_element_path = data_argument_to_mask_converter.get_path_in_source_element()

        result_mask = \
            self.forward_translate_masked_data_arguments_to_result_mask(data_argument_to_mask_converter)

        if not np.any(result_mask):
            return []

        if result_mask is True or result_mask is np_True:
            within_target_array_path = []
        else:
            within_target_array_path = [PathComponent(result_mask, extract_element_out_of_array=False)]
        return [within_target_array_path + remaining_path_to_source + within_source_element_path]

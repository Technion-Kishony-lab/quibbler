from typing import Any, List, Tuple

import numpy as np
from numpy.typing import NDArray

from pyquibbler.translation.array_index_codes import is_focal_element
from pyquibbler.translation.array_translation_utils import ArrayPathTranslator
from pyquibbler.translation.translators.numpy_translator import \
    NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator
from pyquibbler.utilities.general_utils import unbroadcast_bool_mask


class BackwardsElementwisePathTranslator(NumpyBackwardsPathTranslator):

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[np.int64], NDArray[bool]]:
        """
        Get the relevant indices for the argument quib that will need to be changed

        Even though the operation is element wise, this does not necessarily mean that the final results shape is
        the same as the arguments' shape, as their may have been broadcasting. Given this, we take our argument quib
        and broadcast it's index grid to the shape of the result, so we can see the corresponding quib indices for the
        result indices
        """
        data_argument_index_array = data_argument_to_source_index_code_converter.get_masked_data_argument_of_source()
        bool_mask_of_data_argument = unbroadcast_bool_mask(result_bool_mask, np.shape(data_argument_index_array))
        return data_argument_index_array, bool_mask_of_data_argument


class ForwardsElementwisePathTranslator(NumpyForwardsPathTranslator):

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        Create a boolean mask representing the affected data source elements in the output array.
        """
        masked_data_arguments = data_argument_to_mask_converter.get_masked_data_arguments()

        if len(masked_data_arguments) == 1:
            # single arg function
            return masked_data_arguments[0]

        # binary operators and dual arg functions:
        return np.logical_or(masked_data_arguments[0], masked_data_arguments[1])

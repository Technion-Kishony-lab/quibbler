from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from pyquibbler.utilities.general_utils import unbroadcast_or_broadcast_bool_mask

from ..array_translation_utils import ArrayPathTranslator
from .numpy_translator import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator


# BACKWARDS:

class BackwardsUnaryElementwisePathTranslator(NumpyBackwardsPathTranslator):

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[np.int64], NDArray[bool]]:
        """
        The argument data indices are identical to the target result indices
        """
        data_argument_index_array = data_argument_to_source_index_code_converter.get_masked_data_argument_of_source()
        return data_argument_index_array, result_bool_mask


class BackwardsBinaryElementwisePathTranslator(NumpyBackwardsPathTranslator):

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
        bool_mask_of_data_argument = unbroadcast_or_broadcast_bool_mask(result_bool_mask,
                                                                        np.shape(data_argument_index_array))
        return data_argument_index_array, bool_mask_of_data_argument


# FORWARD:

class ForwardsUnaryElementwisePathTranslator(NumpyForwardsPathTranslator):
    ADD_OUT_OF_ARRAY_COMPONENT = True

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        The target is affected exactly at the same indices that the source is affected.
        """
        masked_data_arguments = data_argument_to_mask_converter.get_masked_data_arguments()
        return masked_data_arguments[0]


class ForwardsBinaryElementwisePathTranslator(NumpyForwardsPathTranslator):
    ADD_OUT_OF_ARRAY_COMPONENT = True

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        The target is affected at the indices of the source, broadcasted by the shape of the other data argument.
        """
        masked_data_arguments = data_argument_to_mask_converter.get_masked_data_arguments()
        return np.logical_or(masked_data_arguments[0], masked_data_arguments[1])
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from pyquibbler.translation.translators.numpy_translator import NumpyBackwardsPathTranslator, \
    NumpyForwardsPathTranslator
from pyquibbler.translation.array_translation_utils import ArrayPathTranslator, \
    run_func_call_with_new_args_kwargs


class BackwardsTranspositionalTranslator(NumpyBackwardsPathTranslator):

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[np.int64], NDArray[bool]]:
        """
        We transform the indices of the source to the target by applying the transposition function.
        """
        func_args_kwargs = data_argument_to_source_index_code_converter.get_func_args_kwargs()
        result = run_func_call_with_new_args_kwargs(self._func_call, func_args_kwargs)

        return result, result_bool_mask


class ForwardsTranspositionalTranslator(NumpyForwardsPathTranslator):
    """
    Forward translate numpy transpositional functions (like array, rot90, flip).
    Works by applying the function to the data args replaced with bool mask
    """
    ADD_OUT_OF_ARRAY_COMPONENT = True

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        # We simply apply the quib function to the boolean-transformed arguments
        masked_func_args_kwargs = data_argument_to_mask_converter.get_func_args_kwargs()
        return run_func_call_with_new_args_kwargs(self._func_call, masked_func_args_kwargs)

from typing import Tuple

from numpy.typing import NDArray

from pyquibbler.path_translation.translators.numpy import NumpyBackwardsPathTranslator, \
    NumpyForwardsPathTranslator
from pyquibbler.path_translation.array_translation_utils import ArrayPathTranslator, \
    run_func_call_with_new_args_kwargs
from ..array_index_codes import INDEX_TYPE


class TranspositionalPathTranslator:
    def _get_result_mask(self, data_argument_to_source_index_code_converter: ArrayPathTranslator):
        func_args_kwargs = data_argument_to_source_index_code_converter.get_func_args_kwargs()
        return run_func_call_with_new_args_kwargs(self._func_call, func_args_kwargs)


class TranspositionalBackwardsPathTranslator(NumpyBackwardsPathTranslator, TranspositionalPathTranslator):
    """
    Backward translate numpy transpositional functions (like array, rot90, flip).
    Works by applying the function to the data args replaced with index codes.
    """

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[INDEX_TYPE], NDArray[bool]]:
        """
        We transform the indices of the source to the target by applying the transposition function.
        """
        result = self._get_result_mask(data_argument_to_source_index_code_converter)
        return result, result_bool_mask


class TranspositionalForwardsPathTranslator(NumpyForwardsPathTranslator, TranspositionalPathTranslator):
    """
    Forward translate numpy transpositional functions (like array, rot90, flip).
    Works by applying the function to the data args replaced with bool mask
    """
    ADD_OUT_OF_ARRAY_COMPONENT = True

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        We simply apply the quib function to the boolean-transformed arguments
        """
        result = self._get_result_mask(data_argument_to_mask_converter)
        return result

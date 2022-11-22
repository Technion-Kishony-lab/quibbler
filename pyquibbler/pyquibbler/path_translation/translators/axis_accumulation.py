from typing import List, Tuple

import numpy as np
from numpy.typing import NDArray

from pyquibbler.utilities.numpy_original_functions import np_logical_or, np_cumsum

from ..array_index_codes import INDEX_TYPE
from ..array_translation_utils import run_func_call_with_new_args_kwargs, ArrayPathTranslator
from .numpy import NumpyBackwardsPathTranslator, NumpyForwardsPathTranslator, Arg


class AxisAccumulationBackwardsPathTranslator(NumpyBackwardsPathTranslator):

    TRANSLATION_RELATED_ARGS: List[Arg] = [Arg('axis')]

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[INDEX_TYPE], NDArray[bool]]:
        """
        In accumulation functions, like cumsum, the value of an element j depends on all elements up to j in
        the data argument.
        To find all elements before the last requested element along the accumulation axis,
        we flip the target mask along accumulation axis, then use np_logical_or.accumulate and flip back.
        """
        data_argument_index_array = data_argument_to_source_index_code_converter.get_masked_data_argument_of_source()
        args_dict = self._get_translation_related_arg_dict()
        result_core_axis = args_dict.pop('axis')
        need_reshape = result_core_axis is None
        if need_reshape:
            result_core_axis = 0
        bool_mask = np.flip(result_bool_mask, axis=result_core_axis)
        bool_mask = np_logical_or.accumulate(bool_mask, axis=result_core_axis, **args_dict)
        bool_mask = np.flip(bool_mask, axis=result_core_axis)
        if need_reshape:
            bool_mask = np.reshape(bool_mask, np.shape(data_argument_index_array))
        return data_argument_index_array, bool_mask


class AxisAccumulationForwardsPathTranslator(NumpyForwardsPathTranslator):

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        # To find accumulated effect, we use np.cumsum on the bool mask and then test for >0.
        # (cumsum, unlike np.logical_or.accumulate, knows how to deal with axis=None)
        masked_func_args_kwargs = data_argument_to_mask_converter.get_func_args_kwargs()
        masked_func_args_kwargs.func = np_cumsum
        return run_func_call_with_new_args_kwargs(self._func_call, masked_func_args_kwargs) > 0

from typing import List, Tuple

import numpy as np
from numpy.typing import NDArray

from pyquibbler.utilities.numpy_original_functions import np_logical_and, np_sum

from ..array_index_codes import INDEX_TYPE
from ..array_translation_utils import run_func_call_with_new_args_kwargs, ArrayPathTranslator
from .numpy import NumpyBackwardsPathTranslator, NumpyForwardsPathTranslator, Arg, ArgWithDefault


class AxisReductionBackwardsPathTranslator(NumpyBackwardsPathTranslator):

    TRANSLATION_RELATED_ARGS: List[Arg] = \
        [ArgWithDefault('axis', None), ArgWithDefault('keepdims', False), ArgWithDefault('where', True)]

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[INDEX_TYPE], NDArray[bool]]:
        """
        """
        data_argument_index_array = data_argument_to_source_index_code_converter.get_masked_data_argument_of_source()
        args_dict = self._get_translation_related_arg_dict()
        keepdims = args_dict['keepdims']
        if not keepdims:
            input_core_dims = args_dict['axis']
            if input_core_dims is not None:
                result_bool_mask = np.expand_dims(result_bool_mask, input_core_dims)
        result_bool_mask = np.broadcast_to(result_bool_mask, np.shape(data_argument_index_array))
        return data_argument_index_array, np_logical_and(result_bool_mask, args_dict['where'])


class AxisReductionForwardsPathTranslator(NumpyForwardsPathTranslator):

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        # to find accumulated effect, we use np.sum on the bool mask and then test for >0.
        masked_func_args_kwargs = data_argument_to_mask_converter.get_func_args_kwargs()
        masked_func_args_kwargs.func = np_sum
        return run_func_call_with_new_args_kwargs(self._func_call, masked_func_args_kwargs) > 0

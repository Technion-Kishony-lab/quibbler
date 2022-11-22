from typing import List, Tuple

import numpy as np
from numpy.typing import NDArray

from pyquibbler.utilities.numpy_original_functions import np_any

from ..array_index_codes import INDEX_TYPE
from ..array_translation_utils import run_func_call_with_new_args_kwargs, ArrayPathTranslator
from .numpy import Arg, NumpyBackwardsPathTranslator, NumpyForwardsPathTranslator


class AxisAllToAllBackwardsPathTranslator(NumpyBackwardsPathTranslator):

    TRANSLATION_RELATED_ARGS: List[Arg] = [Arg('axis')]

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[INDEX_TYPE], NDArray[bool]]:
        """
        In axiswise functions, like np.sort, the value of an element j depends on all elements along the axis.
        We therefore use np.any and broadasting to the shape of the argument
        """
        data_argument_index_array = data_argument_to_source_index_code_converter.get_masked_data_argument_of_source()
        args_dict = self._get_translation_related_arg_dict()
        result_core_axis = args_dict.pop('axis')
        bool_mask = np_any(result_bool_mask, axis=result_core_axis, keepdims=True)
        bool_mask = np.broadcast_to(bool_mask, np.shape(data_argument_index_array))
        return data_argument_index_array, bool_mask


class AxisAllToAllForwardsPathTranslator(NumpyForwardsPathTranslator):

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        # a change in an argument element affects result along the entire axis.
        # we find this extended effect using np.any with keep_dims=True and broadcasting
        masked_func_args_kwargs = data_argument_to_mask_converter.get_func_args_kwargs()
        masked_func_args_kwargs.func = np_any
        masked_func_args_kwargs.kwargs['keepdims'] = True
        affected = run_func_call_with_new_args_kwargs(self._func_call, masked_func_args_kwargs) > 0
        return np.broadcast_to(affected, self._shape)

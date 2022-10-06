from typing import List

import numpy as np
from numpy._typing import NDArray

from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.path import Path
from pyquibbler.utilities.numpy_original_functions import np_logical_or, np_cum_sum
from .axiswise_translator import AxiswiseBackwardsPathTranslator, Arg
from ...numpy_translation_utils import run_func_call_with_new_args_kwargs
from ...numpy_translator import NewNumpyForwardsPathTranslator
from ...types import Source

ACCUMULATION_ARGS = [Arg('axis')]


class AccumulationBackwardsPathTranslator(AxiswiseBackwardsPathTranslator):

    TRANSLATION_RELATED_ARGS = ACCUMULATION_ARGS

    def _backwards_translate_bool_mask(self, args_dict, source: Source, component: np.ndarray) -> np.ndarray:
        result_core_axis = args_dict.pop('axis')
        need_reshape = False
        if result_core_axis is None:
            result_core_axis = 0
            need_reshape = True
        bool_mask = np.flip(component, axis=result_core_axis)
        bool_mask = np_logical_or.accumulate(bool_mask, axis=result_core_axis, **args_dict)
        bool_mask = np.flip(bool_mask, axis=result_core_axis)
        if need_reshape:
            bool_mask = np.reshape(bool_mask, np.shape(source.value))
        return bool_mask


class AccumulationForwardsPathTranslator(NewNumpyForwardsPathTranslator):

    def _should_extract_element_out_of_array(self, within_source_array_path: Path) -> bool:
        return False

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               masked_func_args_kwargs: FuncArgsKwargs,
                                                               masked_data_arguments: List[NDArray[bool]]
                                                               ) -> NDArray[bool]:
        # to find accumulated effect, we use cumsum on the bool mask and then test for >0.
        # cumsum, unlike np.logical_or.accumulate, knows how to deal with axis=None
        masked_func_args_kwargs.func = np_cum_sum
        return run_func_call_with_new_args_kwargs(self._func_call, masked_func_args_kwargs) > 0

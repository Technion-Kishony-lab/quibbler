from typing import List

import numpy as np
from numpy._typing import NDArray

from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.path import Path
from pyquibbler.utilities.numpy_original_functions import np_logical_or, np_cumsum
from pyquibbler.translation.translators.axiswise_translator import AxiswiseBackwardsPathTranslator, Arg
from pyquibbler.translation.array_translation_utils import run_func_call_with_new_args_kwargs, ArrayPathTranslator
from pyquibbler.translation.translators.numpy_translator import NumpyForwardsPathTranslator
from pyquibbler.translation.types import Source

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


class AccumulationForwardsPathTranslator(NumpyForwardsPathTranslator):

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        # To find accumulated effect, we use np.cumsum on the bool mask and then test for >0.
        # (cumsum, unlike np.logical_or.accumulate, knows how to deal with axis=None)
        masked_func_args_kwargs = data_argument_to_mask_converter.get_func_args_kwargs()
        masked_func_args_kwargs.func = np_cumsum
        return run_func_call_with_new_args_kwargs(self._func_call, masked_func_args_kwargs) > 0

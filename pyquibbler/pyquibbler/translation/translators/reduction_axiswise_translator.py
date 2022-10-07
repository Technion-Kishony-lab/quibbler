import numpy as np
from numpy.typing import NDArray

from pyquibbler.utilities.numpy_original_functions import np_sum
from pyquibbler.translation.array_translation_utils import run_func_call_with_new_args_kwargs, ArrayPathTranslator
from pyquibbler.translation.types import Source
from .numpy_translator import NumpyForwardsPathTranslator
from .axiswise_translator import Arg, ArgWithDefault, AxiswiseBackwardsPathTranslator

REDUCTION_ARGS = [Arg('axis'), ArgWithDefault('keepdims', False), ArgWithDefault('where', True)]


class ReductionAxiswiseBackwardsPathTranslator(AxiswiseBackwardsPathTranslator):

    TRANSLATION_RELATED_ARGS = REDUCTION_ARGS

    def _backwards_translate_bool_mask(self, args_dict, source: Source, bool_mask: np.ndarray) -> np.ndarray:
        from pyquibbler.utilities.numpy_original_functions import np_logical_and
        keepdims = args_dict['keepdims']
        if not keepdims:
            input_core_dims = args_dict['axis']
            if input_core_dims is not None:
                bool_mask = np.expand_dims(bool_mask, input_core_dims)
        bool_mask = np.broadcast_to(bool_mask, np.shape(source.value))
        return np_logical_and(bool_mask, args_dict['where'])


class ReductionAxiswiseForwardsPathTranslator(NumpyForwardsPathTranslator):

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        # to find accumulated effect, we use np.sum on the bool mask and then test for >0.
        masked_func_args_kwargs = data_argument_to_mask_converter.get_func_args_kwargs()
        masked_func_args_kwargs.func = np_sum
        return run_func_call_with_new_args_kwargs(self._func_call, masked_func_args_kwargs) > 0

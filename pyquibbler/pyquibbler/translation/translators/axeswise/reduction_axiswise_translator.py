import numpy as np

from pyquibbler.translation.translators.axeswise.axiswise_translator import AxiswiseForwardsPathTranslator, \
    Arg, ArgWithDefault, AxiswiseBackwardsPathTranslator
from pyquibbler.translation.types import Source

REDUCTION_ARGS = [Arg('axis'), ArgWithDefault('keepdims', False), ArgWithDefault('where', True)]


class ReductionAxiswiseForwardsPathTranslator(AxiswiseForwardsPathTranslator):

    TRANSLATION_RELATED_ARGS = REDUCTION_ARGS

    def _forward_translate_bool_mask(self, args_dict, boolean_mask, source: Source):
        """
        Calculate forward index translation for reduction functions by reducing the boolean arrays
        with the same reduction params.
        """
        from pyquibbler.utilities.numpy_original_functions import np_logical_or
        return np_logical_or.reduce(boolean_mask, **args_dict)


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

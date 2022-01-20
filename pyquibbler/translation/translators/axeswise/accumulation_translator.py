import numpy as np

from .axiswise_translator import AxiswiseBackwardsPathTranslator, AxiswiseForwardsPathTranslator, Arg
from ...types import Source

ACCUMULATION_ARGS = [Arg('axis')]


class AccumulationForwardsPathTranslator(AxiswiseForwardsPathTranslator):

    TRANSLATION_RELATED_ARGS = ACCUMULATION_ARGS

    def _forward_translate_bool_mask(self, args_dict, boolean_mask, source: Source):
        """
        Calculate forward index translation for reduction functions by accumulating the boolean arrays
        with the same accumulation params.
        """
        axis = args_dict.pop('axis')
        if axis is None:
            boolean_mask = boolean_mask.flat
            axis = 0
        return np.logical_or.accumulate(boolean_mask, axis=axis, **args_dict)


class AccumulationBackwardsPathTranslator(AxiswiseBackwardsPathTranslator):

    TRANSLATION_RELATED_ARGS = ACCUMULATION_ARGS

    def _backwards_translate_bool_mask(self, args_dict, source: Source, component: np.ndarray) -> np.ndarray:
        result_core_axis = args_dict.pop('axis')
        need_reshape = False
        if result_core_axis is None:
            result_core_axis = 0
            need_reshape = True
        bool_mask = np.flip(component, axis=result_core_axis)
        bool_mask = np.logical_or.accumulate(bool_mask, axis=result_core_axis, **args_dict)
        bool_mask = np.flip(bool_mask, axis=result_core_axis)
        if need_reshape:
            bool_mask = np.reshape(bool_mask, np.shape(source.value))
        return bool_mask

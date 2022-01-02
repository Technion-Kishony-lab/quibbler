from dataclasses import dataclass
from typing import Dict, Tuple, Any

import numpy as np

from pyquibbler.quib.assignment import Path
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues, create_empty_array_with_values_at_indices
from pyquibbler.quib.graphics.axiswise_function_quibs.axiswise_function_quib import Arg
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.refactor.translation.translators.axeswise.axiswise_translator import AxiswiseBackwardsTranslator
from pyquibbler.refactor.translation.types import Source


@dataclass
class ApplyAlongAxis:
    func_with_args_values: FuncWithArgsValues
    result_shape: Tuple[int, ...]

    @property
    def arr(self):
        return self.func_with_args_values.args_values['arr']

    @property
    def axis(self):
        return self.func_with_args_values.args_values['axis']

    def get_expanded_dims(self):
        func_result_ndim = len(self.result_shape) - len(np.shape(self.arr)) + 1
        assert func_result_ndim >= 0, func_result_ndim
        return tuple(range(self.axis, self.axis + func_result_ndim) if self.axis >= 0 else
                     range(self.axis, self.axis - func_result_ndim, -1))


class ApplyAlongAxisBackwardsTranslator(AxiswiseBackwardsTranslator):

    def _backwards_translate_bool_mask(self, source: Source, component: np.ndarray) -> np.ndarray:
        expanded_dims = self.apply_along_axis.get_expanded_dims()
        mask = np.expand_dims(np.any(component,
                                     axis=expanded_dims),
                              self.apply_along_axis.axis)
        return np.broadcast_to(mask, np.shape(source.value))

    @property
    def apply_along_axis(self):
        return ApplyAlongAxis(
            func_with_args_values=self._func_with_args_values,
            result_shape=self._shape
        )


class ApplyAlongAxisForwardsTranslator(ForwardsPathTranslator):
    TRANSLATION_RELATED_ARGS = [Arg('axis')]

    def _get_translation_related_arg_dict(self):
        arg_dict = {key: val for key, val in self._func_with_args_values.args_values.arg_values_by_name.items()
                    if not isinstance(val, np._globals._NoValueType)}
        return {arg.name: arg.get_value(arg_dict) for arg in self.TRANSLATION_RELATED_ARGS}

    @property
    def apply_along_axis(self):
        return ApplyAlongAxis(
            func_with_args_values=self._func_with_args_values,
            result_shape=self._shape
        )

    def _get_expanded_dims(self, axis, source_shape):
        func_result_ndim = len(self._shape) - len(source_shape) + 1
        assert func_result_ndim >= 0, func_result_ndim
        return tuple(range(axis, axis + func_result_ndim) if axis >= 0 else
                     range(axis, axis - func_result_ndim, -1))

    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: np.ndarray):
        """
        Calculate forward index translation for apply_along_axis by applying np.any on the boolean mask.
        After that we expand and broadcast the reduced mask to match the actual result shape, which is dependent
        on the applied function return type.
        """
        boolean_mask = create_empty_array_with_values_at_indices(
            value=True,
            empty_value=False,
            indices=indices,
            shape=np.shape(source.value)
        )
        args_dict = self._get_translation_related_arg_dict()
        axis = args_dict.pop('axis')
        dims_to_expand = self._get_expanded_dims(axis, np.shape(source.value))
        applied = np.apply_along_axis(np.any,
                                      axis,
                                      boolean_mask,
                                      **args_dict)
        expanded = np.expand_dims(applied, dims_to_expand)
        broadcast = np.broadcast_to(expanded, self._shape)
        return broadcast
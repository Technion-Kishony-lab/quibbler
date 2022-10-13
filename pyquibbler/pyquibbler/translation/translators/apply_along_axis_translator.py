from dataclasses import dataclass

import numpy as np

from typing import List
from numpy.typing import NDArray

from pyquibbler.translation.array_translation_utils import ArrayPathTranslator
from pyquibbler.translation.translators.numpy_translator import NumpyForwardsPathTranslator, Arg
from pyquibbler.utilities.general_utils import Shape
from pyquibbler.function_definitions.func_call import FuncCall


@dataclass
class ApplyAlongAxis:
    func_call: FuncCall
    result_shape: Shape

    @property
    def arr(self):
        return self.func_call.func_args_kwargs['arr']

    @property
    def axis(self):
        return self.func_call.func_args_kwargs['axis']

    def get_expanded_dims(self):
        func_result_ndim = len(self.result_shape) - len(np.shape(self.arr)) + 1
        assert func_result_ndim >= 0, func_result_ndim
        return tuple(range(self.axis, self.axis + func_result_ndim) if self.axis >= 0 else
                     range(self.axis, self.axis - func_result_ndim, -1))


class ApplyAlongAxisForwardsTranslator(NumpyForwardsPathTranslator):
    TRANSLATION_RELATED_ARGS: List[Arg] = [Arg('axis')]

    def _get_translation_related_arg_dict(self):
        arg_dict = {key: val for key, val in self._func_call.func_args_kwargs.get_arg_values_by_keyword().items()
                    if not isinstance(val, np._globals._NoValueType)}
        return {arg.name: arg.get_value(arg_dict) for arg in self.TRANSLATION_RELATED_ARGS}

    @property
    def apply_along_axis(self):
        return ApplyAlongAxis(
            func_call=self._func_call,
            result_shape=self._shape
        )

    def _get_expanded_dims(self, axis, source_shape):
        func_result_ndim = len(self._shape) - len(source_shape) + 1
        assert func_result_ndim >= 0, func_result_ndim
        return tuple(range(axis, axis + func_result_ndim) if axis >= 0 else
                     range(axis, axis - func_result_ndim, -1))

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        Calculate forward index translation for apply_along_axis by applying np.any on the boolean mask.
        After that we expand and broadcast the reduced mask to match the actual result shape, which is dependent
        on the applied function return type.
        """
        boolean_mask = data_argument_to_mask_converter.get_masked_data_arguments()[0]
        args_dict = self._get_translation_related_arg_dict()
        axis = args_dict.pop('axis')
        dims_to_expand = self._get_expanded_dims(axis, np.shape(self._source.value))
        applied = np.any(boolean_mask, axis)
        expanded = np.expand_dims(applied, dims_to_expand)
        broadcast = np.broadcast_to(expanded, self._shape)
        return broadcast

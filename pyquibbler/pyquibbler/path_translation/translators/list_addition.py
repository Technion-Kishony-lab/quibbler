from abc import ABC
from typing import Tuple, Dict

import numpy as np
from numpy.typing import NDArray

from pyquibbler.path import Path, Paths
from pyquibbler.utilities.multiple_instance_runner import ConditionalRunner

from ..array_translation_utils import ArrayPathTranslator, run_func_call_with_new_args_kwargs

from .numpy import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator
from ..source_func_call import Source


def replace_list_with_object_array(arg):
    def _replace(obj):
        if isinstance(obj, list):
            return np.array(obj + [None], dtype=object)[:-1]
        return obj

    if isinstance(arg, Source):
        arg.value = _replace(arg.value)
    else:
        arg = _replace(arg)
    return arg


class ListAdditionPathTranslator(ConditionalRunner, ABC):

    def can_try(self) -> bool:
        return issubclass(self._type, list)

    def translate_list_args_to_object_arrays(self):
        self._func_call.func_args_kwargs.args = tuple(replace_list_with_object_array(arg)
                                                      for arg in self._func_call.func_args_kwargs.args)


class ListAdditionBackwardsPathTranslator(NumpyBackwardsPathTranslator, ListAdditionPathTranslator):

    def _backwards_translate(self) -> Dict[Source, Path]:
        self.translate_list_args_to_object_arrays()
        return super()._backwards_translate()

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[np.int64], NDArray[bool]]:
        """
        We transform the indices of the source to the target by transferring the object arrays back to lists
        and applying the list addiiton/multiplication function.
        """
        func_args_kwargs = data_argument_to_source_index_code_converter.get_func_args_kwargs()
        func_args_kwargs.args = [arg.tolist() for arg in func_args_kwargs.args]
        result = run_func_call_with_new_args_kwargs(self._func_call, func_args_kwargs)
        result = np.array(result)
        return result, result_bool_mask


class ListAdditionForwardsPathTranslator(NumpyForwardsPathTranslator, ListAdditionPathTranslator):

    ADD_OUT_OF_ARRAY_COMPONENT = False

    def _forward_translate(self) -> Paths:
        self.translate_list_args_to_object_arrays()
        return super()._forward_translate()

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        # We simply apply the quib function to the boolean-transformed arguments
        masked_func_args_kwargs = data_argument_to_mask_converter.get_func_args_kwargs()
        masked_func_args_kwargs.args = [arg.tolist() for arg in masked_func_args_kwargs.args]
        result = run_func_call_with_new_args_kwargs(self._func_call, masked_func_args_kwargs)
        result = np.array(result)
        return result


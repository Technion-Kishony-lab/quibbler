from abc import ABC
from typing import Tuple, Dict

import numbers
import numpy as np
from numpy.typing import NDArray

from pyquibbler.path import Path
from pyquibbler.utilities.general_utils import unbroadcast_or_broadcast_bool_mask
from pyquibbler.utilities.multiple_instance_runner import ConditionalRunner

from ..source_func_call import Source
from ..array_translation_utils import ArrayPathTranslator
from ..base_translators import BackwardsTranslationRunCondition, BackwardsPathTranslator
from ..array_index_codes import INDEX_TYPE
from .numpy import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator


class ElementwisePathTranslator(ConditionalRunner, ABC):
    def can_try(self) -> bool:
        # If we are an operator, we check that the result is numeric or ndarray.
        # For example, if we are the `+` operator acting on two lists, then the result is a concatenated list
        # which we cannot translate using this translator.
        if self._func_call.func_definition.is_operator:
            # we are an operator. to know whether we can run, we need the type of the function result
            if self._type is None:
                # we don't have the type, so we cannot run
                return False
            return issubclass(self._type, numbers.Number) or issubclass(self._type, np.ndarray)
        return True


# BACKWARDS:


class UnaryElementwiseNoShapeBackwardsPathTranslator(BackwardsPathTranslator):
    """
    If the argument is a source, it is very easy to translate: the source data indices are simply
    identical to the target result indices.
    """

    RUN_CONDITIONS = [BackwardsTranslationRunCondition.NO_SHAPE_AND_TYPE,
                      BackwardsTranslationRunCondition.WITH_SHAPE_AND_TYPE]

    @property
    def source_to_change(self):
        return self._func_call.args[0]

    def can_try(self) -> bool:
        return isinstance(self.source_to_change, Source)

    def _backwards_translate(self) -> Dict[Source, Path]:
        return {self.source_to_change: self._path}


class UnaryElementwiseBackwardsPathTranslator(ElementwisePathTranslator, NumpyBackwardsPathTranslator):

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[INDEX_TYPE], NDArray[bool]]:
        """
        The argument data indices are identical to the target result indices
        """
        data_argument_index_array = data_argument_to_source_index_code_converter.get_masked_data_argument_of_source()
        return data_argument_index_array, result_bool_mask


class BinaryElementwiseBackwardsPathTranslator(ElementwisePathTranslator, NumpyBackwardsPathTranslator):

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[INDEX_TYPE], NDArray[bool]]:
        """
        Get the relevant indices for the argument quib that will need to be changed

        Even though the operation is element wise, this does not necessarily mean that the final results shape is
        the same as the arguments' shape, as their may have been broadcasting. Given this, we take our argument quib
        and broadcast it's index grid to the shape of the result, so we can see the corresponding quib indices for the
        result indices
        """
        data_argument_index_array = data_argument_to_source_index_code_converter.get_masked_data_argument_of_source()
        bool_mask_of_data_argument = unbroadcast_or_broadcast_bool_mask(result_bool_mask,
                                                                        np.shape(data_argument_index_array))
        return data_argument_index_array, bool_mask_of_data_argument


# FORWARD:

class UnaryElementwiseForwardsPathTranslator(ElementwisePathTranslator, NumpyForwardsPathTranslator):
    ADD_OUT_OF_ARRAY_COMPONENT = True

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        The target is affected exactly at the same indices that the source is affected.
        """
        masked_data_arguments = data_argument_to_mask_converter.get_masked_data_arguments()
        return masked_data_arguments[0]


class BinaryElementwiseForwardsPathTranslator(ElementwisePathTranslator, NumpyForwardsPathTranslator):
    ADD_OUT_OF_ARRAY_COMPONENT = True

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        The target is affected at the indices of the source, broadcasted by the shape of the other data argument.
        """
        masked_data_arguments = data_argument_to_mask_converter.get_masked_data_arguments()
        return np.logical_or(masked_data_arguments[0], masked_data_arguments[1])

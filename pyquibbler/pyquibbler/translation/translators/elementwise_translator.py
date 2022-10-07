from typing import Any, List

import numpy as np
from numpy.typing import NDArray

from pyquibbler.function_definitions import SourceLocation, FuncArgsKwargs
from pyquibbler.path.path_component import PathComponent
from pyquibbler.translation.array_translation_utils import ArrayPathTranslator
from pyquibbler.translation.translators.numpy_translator import NumpyBackwardsPathTranslator, NumpyForwardsPathTranslator
from pyquibbler.utilities.general_utils import unbroadcast_bool_mask, create_bool_mask_with_true_at_path
from pyquibbler.translation.types import Source


class BackwardsElementwisePathTranslator(NumpyBackwardsPathTranslator):

    def _get_indices_to_change(self, source: Source) -> Any:
        """
        Get the relevant indices for the argument quib that will need to be changed

        Even though the operation is element wise, this does not necessarily mean that the final results shape is
        the same as the arguments' shape, as their may have been broadcasting. Given this, we take our argument quib
        and broadcast it's index grid to the shape of the result, so we can see the corresponding quib indices for the
        result indices
        """
        result_bool_mask = create_bool_mask_with_true_at_path(self._shape, self._working_path)

        return unbroadcast_bool_mask(result_bool_mask, np.shape(source.value))

    def _get_path_in_source(self, source: Source, location: SourceLocation):
        changed_indices = self._get_indices_to_change(source)
        new_path = [] if changed_indices.ndim == 0 else [PathComponent(changed_indices)]
        return new_path


class ForwardsElementwisePathTranslator(NumpyForwardsPathTranslator):

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        Create a boolean mask representing the affected data source elements in the output array.
        """
        masked_data_arguments = data_argument_to_mask_converter.get_masked_data_arguments()

        if len(masked_data_arguments) == 1:
            # single arg function
            return masked_data_arguments[0]

        # binary operators and dual arg functions:
        return np.logical_or(masked_data_arguments[0], masked_data_arguments[1])

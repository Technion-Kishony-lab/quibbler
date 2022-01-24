from typing import Any

import numpy as np

from pyquibbler.path.path_component import PathComponent
from pyquibbler.translation.numpy_translator import NumpyBackwardsPathTranslator
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices, unbroadcast_bool_mask
from pyquibbler.translation.numpy_translator import NumpyForwardsPathTranslator
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
        result_bool_mask = create_bool_mask_with_true_at_indices(self._shape, self._working_component)

        return unbroadcast_bool_mask(result_bool_mask, np.shape(source.value))

    def _get_path_in_source(self, source: Source):
        changed_indices = self._get_indices_to_change(source)
        new_path = [] if changed_indices.ndim == 0 else [PathComponent(self._type, changed_indices)]
        return new_path


class ForwardsElementwisePathTranslator(NumpyForwardsPathTranslator):

    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: Any):
        """
        Create a boolean mask representing the source at certain indices in the result.
        For a simple operation (eg `source=[1, 2, 3]`, `source + [2, 3, 4]`, and we forward path `(0, 0)`),
        the `True`'s will be in the location of the indices (`[True, False, False]`)- but if
        the source was broadcasted, we need to make sure we get a boolean mask representing where the indices
        were in the entire result.

        For example- if we have
        ```
        source = [[1, 2, 3]]
        sum_ = source + [[1], [2], [3]]
        ```
        and we forward at (0, 0), we need to create a mask broadcasted like the argument was, ie
        [[True, False, False],
         [True, False, False],
         [True, False, False]]
                """
        bool_mask = create_bool_mask_with_true_at_indices(np.shape(source.value), indices)

        return np.broadcast_to(bool_mask, self._shape)

from typing import Dict, Any

import numpy as np

from pyquibbler.refactor.path.path_component import PathComponent, Path
from pyquibbler.refactor.path.utils import get_nd_working_component_value_from_path
from pyquibbler.refactor.translation.numpy_translator import NumpyBackwardsPathTranslator
from pyquibbler.refactor.utilities.general_utils import create_empty_array_with_values_at_indices, unbroadcast_bool_mask
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.numpy_forwards_path_translator import NumpyForwardsPathTranslator
from pyquibbler.refactor.translation.types import Source


class BackwardsElementwisePathTranslator(NumpyBackwardsPathTranslator):

    def _get_indices_to_change(self, source: Source, working_indices) -> Any:
        """
        Get the relevant indices for the argument quib that will need to be changed

        Even though the operation is element wise, this does not necessarily mean that the final results shape is
        the same as the arguments' shape, as their may have been broadcasting. Given this, we take our argument quib
        and broadcast it's index grid to the shape of the result, so we can see the corresponding quib indices for the
        result indices
        """
        result_bool_mask = create_empty_array_with_values_at_indices(self._shape,
                                                                     indices=working_indices, value=True,
                                                                     empty_value=False)

        return unbroadcast_bool_mask(result_bool_mask, np.shape(source.value))

    def _get_path_in_source(self, source: Source, path_in_result: Path):
        working_component = get_nd_working_component_value_from_path(self._path)
        changed_indices = self._get_indices_to_change(source, working_component)
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
        bool_mask = create_empty_array_with_values_at_indices(
            value=True,
            empty_value=False,
            indices=indices,
            shape=np.shape(source.value)
        )

        return np.broadcast_to(bool_mask, self._shape)

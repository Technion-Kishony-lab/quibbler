from abc import abstractmethod
from typing import Dict, Optional, Tuple, Type, Any

import numpy as np

from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment.assignment import working_component, path_beyond_working_component
from pyquibbler.refactor.translation.path_translator import Translator
from pyquibbler.refactor.translation.types import Source
from pyquibbler.quib.assignment import Path


class ForwardsPathTranslator(Translator):

    def __init__(self,
                 func_with_args_values, sources_to_paths: Dict[Source, Path],
                 shape: Optional[Tuple[int, ...]],
                 type_: Optional[Type]):
        super(ForwardsPathTranslator, self).__init__(func_with_args_values)
        self._sources_to_paths = sources_to_paths
        self._shape = shape
        self._type = type_

    @abstractmethod
    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: Any):
        pass

    def _forward_translate_source(self, source: Source, path: Path):
        bool_mask_in_output_array = self._forward_translate_indices_to_bool_mask(source, working_component(path))
        if np.any(bool_mask_in_output_array):
            # If there exist both True's and False's in the boolean mask,
            # this function's quib result must be an ndarray- if it were a single item (say a PyObj, int, dict, list)
            # we'd expect it to be completely True (as it is ONE single object). If it is not a single item, it is by
            # definitely an ndarray
            assert issubclass(self._type, np.ndarray) or np.all(bool_mask_in_output_array)
            assert issubclass(self._type, np.ndarray) or isinstance(bool_mask_in_output_array, np.bool_) \
                   or (bool_mask_in_output_array.shape == () and bool_mask_in_output_array.dtype == np.bool_)

            if not np.all(bool_mask_in_output_array) and issubclass(self._type, np.ndarray):
                return [[PathComponent(self._type, bool_mask_in_output_array),
                         *path_beyond_working_component(path)]]
            return [path_beyond_working_component(path)]
        return []

    def translate(self):
        return {
            source: self._forward_translate_source(source, path)
            for source, path in self._sources_to_paths.items()
        }


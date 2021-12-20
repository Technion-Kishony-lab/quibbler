from typing import Dict

import numpy as np

from pyquibbler.quib.assignment import Path
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.types import Source


class ApplyAlongAxisBackwardsTranslator(BackwardsPathTranslator):

    def _backwards_translate_bool_mask(self, args_dict, bool_mask, source: Source):
        axis = args_dict.pop('axis')
        source_shape = quib.get_shape()
        expanded_dims = self._get_expanded_dims(axis, bool_mask.shape, source_shape)
        mask = np.expand_dims(np.any(bool_mask, axis=expanded_dims), axis)
        return np.broadcast_to(mask, source_shape)

    def translate(self) -> Dict[Source, Path]:
        pass


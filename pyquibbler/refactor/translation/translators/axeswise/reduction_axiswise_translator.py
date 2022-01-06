from typing import Any

import numpy as np

from pyquibbler.refactor.translation.numpy_translator import NumpyForwardsPathTranslator
from pyquibbler.refactor.translation.types import Source


class ReductionAxiswiseTranslator(NumpyForwardsPathTranslator):

    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: Any):
        """
        Calculate forward index translation for reduction functions by reducing the boolean arrays
        with the same reduction params.
        """
        return np.logical_or.reduce(boolean_mask, **args_dict)


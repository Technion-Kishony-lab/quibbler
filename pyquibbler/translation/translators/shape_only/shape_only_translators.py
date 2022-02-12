from typing import Any, List, Dict

import numpy as np

from pyquibbler.path.path_component import PathComponent, Path
from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.translation.numpy_translator import NumpyBackwardsPathTranslator
from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices, unbroadcast_bool_mask
from pyquibbler.translation.numpy_translator import NumpyForwardsPathTranslator
from pyquibbler.translation.types import Source


class BackwardsShapeOnlyPathTranslator(BackwardsPathTranslator):
    """
    We only need the shape of sources. Not their value.
    """
    def translate(self) -> Dict[Source, Path]:
        sources_to_paths = {}
        for source in self._func_call.get_data_sources():
            sources_to_paths[source] = [PathComponent(np.ndarray, None)]
        return sources_to_paths


class ForwardsShapeOnlyPathTranslator(ForwardsPathTranslator):
    """
    We are only affected if sources change their shape. Element-wise changes are not affecting us.
    """
    def _forward_translate_source(self, source: Source, path: Path) -> List[Path]:
        return [] if len(path) else [[]]
    
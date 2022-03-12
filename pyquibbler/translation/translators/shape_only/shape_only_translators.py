from typing import List, Dict

import numpy as np

from pyquibbler.path.path_component import PathComponent, Path, Paths
from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
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
    We need to take care of lists that can change their size due to assignment.
    """
    def _forward_translate_source(self, source: Source, path: Path) -> Paths:
        is_list_extension_possible = len(path) \
                            and path[0].indexed_cls is list \
                            and isinstance(path[0].component, slice)
        return [] if len(path) and not is_list_extension_possible else [[]]

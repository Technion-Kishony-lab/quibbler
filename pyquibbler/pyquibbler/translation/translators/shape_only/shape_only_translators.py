from typing import Dict

import numpy as np

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path.path_component import PathComponent, Path, Paths

from ...forwards_path_translator import ForwardsPathTranslator
from ...backwards_path_translator import BackwardsPathTranslator
from ...types import Source


class BackwardsShapeOnlyPathTranslator(BackwardsPathTranslator):
    """
    We only need the shape of sources. Not their value.
    """
    def backwards_translate(self) -> Dict[Source, Path]:
        sources_to_paths = {}
        for source in self._func_call.get_data_sources():
            sources_to_paths[source] = [PathComponent(None)]
        return sources_to_paths


class ForwardsShapeOnlyPathTranslator(ForwardsPathTranslator):
    """
    We are only affected if sources change their shape. Element-wise changes are not affecting us.
    We need to take care of lists that can change their size due to assignment.
    """
    def forward_translate(self) -> Paths:
        path = self._path
        is_list_extension_possible = len(path) \
                            and self._source_type() is list \
                            and isinstance(path[0].component, slice)
        return [] if len(path) and not is_list_extension_possible else [[]]

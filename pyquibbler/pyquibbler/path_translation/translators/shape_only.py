from typing import Dict

from pyquibbler.path.path_component import PathComponent, Path, Paths

from pyquibbler.path_translation.base_translators import ForwardsPathTranslator, BackwardsPathTranslator
from pyquibbler.path_translation.types import Source


class ShapeOnlyBackwardsPathTranslator(BackwardsPathTranslator):
    """
    For functions like, np.ones_like, np.zeros_like, np.shape,
    we only need the shape of sources. Not their value.
    """
    def _backwards_translate(self) -> Dict[Source, Path]:
        sources_to_paths = {}
        for source in self._func_call.get_data_sources():
            sources_to_paths[source] = [PathComponent(None)]
        return sources_to_paths


class ShapeOnlyForwardsPathTranslator(ForwardsPathTranslator):
    """
    We are only affected if sources change their shape. Element-wise changes are not affecting us.
    We need to take care of lists that can change their size due to assignment.
    """
    def _forward_translate(self) -> Paths:
        path = self._path
        is_list_extension_possible = \
            len(path) \
            and self._get_source_type() is list \
            and isinstance(path[0].component, slice)
        return [] if len(path) and not is_list_extension_possible else [[]]

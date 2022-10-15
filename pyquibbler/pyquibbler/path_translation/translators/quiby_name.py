from typing import Dict

from pyquibbler.path.path_component import Path, Paths

from pyquibbler.path_translation.base_translators import ForwardsPathTranslator, BackwardsPathTranslator
from pyquibbler.path_translation.types import Source


class QuibyNameBackwardsPathTranslator(BackwardsPathTranslator):
    """
    We need no data from the sources.
    """
    def _backwards_translate(self) -> Dict[Source, Path]:
        sources_to_paths = {}
        for source in self._func_call.get_data_sources():
            sources_to_paths[source] = []
        return sources_to_paths


class QuibyNameForwardsPathTranslator(ForwardsPathTranslator):
    """
    We are not affected by change the sources.
    """
    def _forward_translate(self) -> Paths:
        return []

from typing import Dict

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path.path_component import Path, Paths

from ...forwards_path_translator import ForwardsPathTranslator
from ...backwards_path_translator import BackwardsPathTranslator
from ...types import Source


class BackwardsQuibyNameTranslator(BackwardsPathTranslator):
    """
    We need no data from the sources.
    """
    def backwards_translate(self) -> Dict[Source, Path]:
        sources_to_paths = {}
        for source in self._func_call.get_data_sources():
            sources_to_paths[source] = []
        return sources_to_paths


class ForwardsQuibyNameTranslator(ForwardsPathTranslator):
    """
    We are not affected by change the sources.
    """
    def forward_translate(self) -> Paths:
        return []

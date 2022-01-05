from abc import abstractmethod
from typing import Dict, Optional, Tuple, Type, Any, List

import numpy as np

from pyquibbler.refactor.translation.path_translator import Translator
from pyquibbler.refactor.translation.types import Source
from pyquibbler.refactor.path.path_component import Path
from pyquibbler.refactor.path.utils import working_component, path_beyond_working_component


class ForwardsPathTranslator(Translator):

    def __init__(self,
                 func_call, sources_to_paths: Dict[Source, Path],
                 shape: Optional[Tuple[int, ...]],
                 type_: Optional[Type]):
        super(ForwardsPathTranslator, self).__init__(func_call)
        self._sources_to_paths = sources_to_paths
        self._shape = shape
        self._type = type_

    @abstractmethod
    def _forward_translate_source(self, source: Source, path: Path) -> List[Path]:
        pass

    def translate(self) -> Dict[Source, List[Path]]:
        return {
            source: self._forward_translate_source(source, path)
            for source, path in self._sources_to_paths.items()
        }

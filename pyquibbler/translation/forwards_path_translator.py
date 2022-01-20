from abc import abstractmethod
from typing import Dict, Optional, Tuple, Type, List


from pyquibbler.translation.path_translator import PathTranslator
from pyquibbler.translation.types import Source
from pyquibbler.path.path_component import Path


class ForwardsPathTranslator(PathTranslator):

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

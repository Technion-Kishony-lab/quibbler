import operator

from typing import Dict

import numpy as np

from pyquibbler.translation.translators.transpositional.transpositional_path_translator import \
    BackwardsTranspositionalTranslator
from pyquibbler.translation.types import Source
from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment import Path


class BackwardsGetItemTranslator(BackwardsTranspositionalTranslator):

    SUPPORTING_FUNCS = {operator.getitem}
    PRIORITY = 1

    @property
    def _getitem_path_component(self):
        component = self._args[1]
        return PathComponent(indexed_cls=s, component=component)

    def _can_squash_start_of_path(self):
        return issubclass(self._type, np.ndarray) \
               and not self._getitem_path_component.references_field_in_field_array() \
               and len(self._path) > 0 \
               and not self._path[0].references_field_in_field_array() \
               and isinstance(self._args[0], np.ndarray)

    def translate(self) -> Dict[Source, Path]:
        if self._can_squash_start_of_path():
            return super(BackwardsGetItemTranslator, self).translate()
        return {
            self._args[0]: [self._getitem_path_component, *self._path]
        }

from abc import ABC, abstractmethod
from typing import List, Dict, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib, Quib

from pyquibbler.quib.assignment.assignment import AssignmentPath


class Invalidator(ABC):

    def __init__(self, function_quib, invalidator_quib: 'Quib', path_component_changed: AssignmentPath):
        self._function_quib = function_quib
        self._invalidator_quib = invalidator_quib
        self._path_component_changed = path_component_changed

    @property
    def _func(self):
        return self._function_quib.func

    @property
    def _args(self):
        return self._function_quib.args

    @property
    def _kwargs(self):
        return self._function_quib.kwargs

    @abstractmethod
    def get_boolean_mask_for_invalidation(self):
        pass

    def invalidate_relevant_children(self):
        mask = self.get_boolean_mask_for_invalidation()
        if np.any(mask):
            self._function_quib._invalidate_with_children(self, mask)

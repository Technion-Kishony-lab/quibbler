import operator

from typing import List

import numpy as np

from .transpositional_inverter import TranspositionalInverter
from ..types import Inversal
from ...quib import PathComponent


class GetItemInverter(TranspositionalInverter):

    PRIORITY = 1

    SUPPORTING_FUNCS = {operator.getitem}

    @property
    def _getitem_path_component(self):
        component = self._args[1]
        return PathComponent(indexed_cls=type(self._args[0]), component=component)

    def _can_squash_start_of_path(self):
        return isinstance(self._previous_result, np.ndarray) \
               and not self._getitem_path_component.references_field_in_field_array() \
               and len(self._assignment.path) > 0 \
               and not self._assignment.path[0].references_field_in_field_array() \
               and isinstance(self._args[0], np.ndarray)

    def get_inversals(self):
        from pyquibbler import Assignment
        if self._can_squash_start_of_path():
            return super(GetItemInverter, self).get_inversals()
        return [
            Inversal(
                assignment=Assignment(
                    path=[self._getitem_path_component, *self._assignment.path],
                    value=self._assignment.value
                ),
                source=self._args[0]
            )
        ]

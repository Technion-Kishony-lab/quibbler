from __future__ import annotations
from abc import ABC, abstractmethod

from pyquibbler.path.data_accessing import deep_assign_data_in_path
from pyquibbler.translation.source_func_call import SourceFuncCall


class Inverter(ABC):

    def __init__(self, func_call: SourceFuncCall, assignment, previous_result):
        self._func_call = func_call
        self._assignment = assignment
        self._previous_result = previous_result

    @abstractmethod
    def get_inversals(self):
        pass

    def _get_result_with_assignment_set(self):
        return deep_assign_data_in_path(self._previous_result,
                                        self._assignment.path,
                                        self._assignment.value,
                                        should_copy_objects_referenced=True)

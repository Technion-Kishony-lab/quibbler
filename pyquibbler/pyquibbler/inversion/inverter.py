from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Union, Any, Tuple, List

from pyquibbler.assignment import Assignment, AssignmentWithTolerance
from pyquibbler.function_definitions import FuncCall
from pyquibbler.path.data_accessing import deep_set
from pyquibbler.path_translation.types import Inversal
from pyquibbler.path_translation.source_func_call import SourceFuncCall
from pyquibbler.utilities.multiple_instance_runner import ConditionalRunner


class Inverter(ConditionalRunner, ABC):

    def __init__(self, func_call: Union[FuncCall, SourceFuncCall],
                 assignment: Assignment,
                 previous_result: Any):
        self._func_call = func_call
        self._assignment = assignment
        self._previous_result = previous_result

    def try_run(self):
        return self.get_inversals()

    @abstractmethod
    def get_inversals(self) -> List[Inversal]:
        pass

    def _get_assignment_nominal_down_up_values(self) -> Tuple[Any]:
        """
        Returns a tuple of size=1 or size=3 with the nominal assignment value (for regular Assignment),
        or the (nominal, down, up) values for AssignmentWithTolerance.
        """
        assignment = self._assignment
        assignment_values = (assignment.value,)
        if isinstance(assignment, AssignmentWithTolerance):
            assignment_values += (assignment.value_down, assignment.value_up)
        return assignment_values

    def _get_result_with_assignment_nominal_down_up(self) -> Tuple[Any]:
        """
        Assign the assignment value into the current result and return the result with the new result

        For regular Assignment, we return a tuple of len=1 containing the result with assignment.
        For AssignmentWithTolerance, we return a tuple of len=3 containing the result with
        (nominal, down, up) assignment values.
        """
        assignment_values = self._get_assignment_nominal_down_up_values()
        return tuple(
            deep_set(self._previous_result, self._assignment.path, assignment_value,
                     should_copy_objects_referenced=True)
            for assignment_value in assignment_values)

from __future__ import annotations
from typing import Any, List, Type, Union, Optional

from pyquibbler.assignment import AssignmentWithTolerance, Assignment, default
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.path import deep_get
from pyquibbler.path_translation.source_func_call import SourceFuncCall
from pyquibbler.path_translation.translate import MultipleFuncCallInstanceRunner
from pyquibbler.path_translation.types import Inversal


class MultipleInverterRunner(MultipleFuncCallInstanceRunner):

    def __init__(self,
                 func_call: SourceFuncCall,
                 assignment: Union[Assignment, AssignmentWithTolerance],
                 previous_result: Any):
        super().__init__(None, func_call)
        self._assignment = assignment
        self._previous_result = previous_result

    def _get_all_runners(self) -> List[Type[Inverter]]:
        return self._func_call.func_definition.inverters

    def _get_inversals_from_tolerance_assignment(self, runner: Type[Inverter]) -> List[Inversal]:
        """
        Run the inverter 3 times to get the nominal inverted value and the plus/minus tolerance
        """

        # TODO: will be better to implement this up/down tolerance within each inverter.
        #  For example, in the transpositional inverter there is no need to get the path 3 times.

        inversals_nominal_up_down = \
            (runner(
                func_call=self._func_call,
                assignment=assignment,
                previous_result=self._previous_result
            ).get_inversals()
             for assignment in
             self._assignment.get_assignments_nominal_up_down())

        inversals = []
        for inversal, inversal_up, inversal_down in zip(*inversals_nominal_up_down):
            inversals.append(
                Inversal(source=inversal.source,
                         assignment=AssignmentWithTolerance.from_assignment_and_up_down_values(
                             assignment=inversal.assignment,
                             value_up=inversal_up.assignment.value,
                             value_down=inversal_down.assignment.value,
                         )
                         )
            )
        return inversals

    def _run_runner(self, runner: Type[Inverter]) -> List[Inversal]:
        if isinstance(self._assignment, AssignmentWithTolerance):
            return self._get_inversals_from_tolerance_assignment(runner)

        return runner(
            func_call=self._func_call,
            assignment=self._assignment,
            previous_result=self._previous_result
        ).get_inversals()


def invert(func_call: SourceFuncCall, assignment: Assignment, previous_result):
    """
    Get all the inversions for a given assignment on the result of a funccall
    """

    is_default = assignment.is_default()
    if is_default:
        actual_assignment = Assignment(value=deep_get(previous_result, assignment.path),
                                       path=assignment.path)
    else:
        actual_assignment = assignment

    inversals = MultipleInverterRunner(func_call, actual_assignment, previous_result).run()

    for inversal in inversals:
        if is_default:
            inversal.assignment.value = default
        else:
            inversal.cast_assigned_value_by_source_value()

    return inversals

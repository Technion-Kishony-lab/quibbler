from __future__ import annotations
from typing import Any, List, Type, Union

from pyquibbler.assignment import AssignmentWithTolerance
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.inversion.exceptions import NoInvertersFoundException, FailedToInvertException
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.path import deep_get
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.types import Inversal
from pyquibbler.utilities.multiple_instance_runner import MultipleInstanceRunner

from pyquibbler import Assignment, default


class MultipleInverterRunner(MultipleInstanceRunner):

    exception_to_raise_on_none_found = NoInvertersFoundException
    expected_runner_exception = FailedToInvertException

    def __init__(self, func_call: SourceFuncCall, assignment: Union[Assignment, AssignmentWithTolerance],
                 previous_result: Any):
        super().__init__(func_call)
        self._assignment = assignment
        self._previous_result = previous_result

    def _get_runners_from_definition(self, definition: FuncDefinition) -> List[Type[Inverter]]:
        return definition.inverters

    def _get_inversals_from_tolerance_assignment(self, runner: Type[Inverter]) -> List[Inversal]:
        """
        Run the inverter 3 times to get the nominal inverted value and the plus/minus tolerance
        """

        # TODO: will be better to implement this within each inverter. For example, in the transpositional inverter
        #  there is no need to get the path 3 times.

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

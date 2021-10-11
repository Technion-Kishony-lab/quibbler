from typing import TYPE_CHECKING

from .default_function_quib import DefaultFunctionQuib
from pyquibbler.quib.assignment.reverse_assignment import ElementWiseReverser

if TYPE_CHECKING:
    from pyquibbler import Assignment


class ElementWiseQuib(DefaultFunctionQuib):

    def get_reversals_for_assignment(self, assignment: 'Assignment'):
        return ElementWiseReverser(
            assignment=assignment,
            function_quib=self
        ).get_reversed_quibs_with_assignments()

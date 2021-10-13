from typing import TYPE_CHECKING

from .default_function_quib import DefaultFunctionQuib
from pyquibbler.quib.assignment.inverse_assignment import ElementWiseInverser

if TYPE_CHECKING:
    from pyquibbler import Assignment


class ElementWiseFunctionQuib(DefaultFunctionQuib):
    """
    A quib representing an element wise mathematical operation- this includes any op that can map an output element
    back to an input element, and the operation can be inversed per element
    """

    def get_inversals_for_assignment(self, assignment: 'Assignment'):
        return ElementWiseInverser(
            assignment=assignment,
            function_quib=self
        ).get_inversed_quibs_with_assignments()

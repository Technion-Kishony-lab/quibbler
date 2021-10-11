from typing import TYPE_CHECKING

import numpy as np


from pyquibbler.quib.assignment.assignment import AssignmentPath
from pyquibbler.quib.assignment.reverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.utils import recursively_run_func_on_object, call_func_with_quib_values

if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib, Quib


def get_boolean_mask_of_quib_indices_in_result(invalidator_quib: 'Quib', assignment_path: 'AssignmentPath',
                                               function_quib: 'FunctionQuib'):
    invalidator_indices = create_empty_array_with_values_at_indices(
        invalidator_quib.get_shape().get_value(),
        indices=assignment_path,
        value=True,
        empty_value=False
    )

    def replace_quib_with_truthiness(q):
        if q in function_quib.get_quibs_which_can_change():
            if q is invalidator_quib:
                return invalidator_indices
            else:
                return np.full(q.get_shape().get_value(), False)
        return q

    new_arguments = recursively_run_func_on_object(
        func=replace_quib_with_truthiness,
        obj=function_quib.args
    )

    return call_func_with_quib_values(function_quib.func, new_arguments, function_quib.kwargs)


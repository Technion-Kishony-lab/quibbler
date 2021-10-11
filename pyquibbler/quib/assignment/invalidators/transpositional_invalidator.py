import numpy as np

from pyquibbler.quib import Quib
from pyquibbler.quib.assignment.invalidators.invalidator import Invalidator
from pyquibbler.quib.assignment.reverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.function_quibs.transpositional_quib import TranspositionalQuib
from pyquibbler.quib.utils import recursively_run_func_on_object, call_func_with_quib_values


class TranspositionalInvalidator(Invalidator):

    def __init__(self, function_quib: TranspositionalQuib, invalidator_quib: Quib, path_component_changed):
        super().__init__(function_quib, invalidator_quib, path_component_changed)

    def invalidate_relevant_children(self):
        invalidator_indices = create_empty_array_with_values_at_indices(
            self._invalidator_quib.get_shape().get_value(),
            indices=self._path_component_changed,
            value=True,
            empty_value=False
        )

        def replace_quib_with_truthiness(q):
            if q in self._function_quib.get_quibs_which_can_change():
                if q is self._invalidator_quib:
                    return invalidator_indices
                else:
                    return np.full(q.get_shape().get_value(), False)
            return q

        new_arguments = recursively_run_func_on_object(
            func=replace_quib_with_truthiness,
            obj=self._args
        )

        return call_func_with_quib_values(self._func, new_arguments, self._kwargs)


import functools
from operator import getitem
from typing import TYPE_CHECKING

import numpy as np

from pyquibbler.quib.assignment import Assignment
from .default_function_quib import DefaultFunctionQuib
from pyquibbler.quib.assignment.reverse_assignment import TranspositionalReverser
from pyquibbler.quib.assignment.reverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.utils import iter_objects_of_type_in_object_shallowly, recursively_run_func_on_object, \
    call_func_with_quib_values
from ..assignment.assignment import PathComponent

if TYPE_CHECKING:
    from .. import Quib


class TranspositionalQuib(DefaultFunctionQuib):
    """
    A quib that represents any transposition function- a function that moves elements (but commits no operation on
    them)
    """

    # A mapping between functions and indices of args that can change
    SUPPORTED_FUNCTIONS_TO_POTENTIALLY_CHANGED_QUIB_INDICES = {
        np.rot90: {0},
        np.concatenate: {0},
        np.repeat: {0},
        np.full: {1},
        getitem: {0},
        np.reshape: {0}
    }

    def _get_boolean_mask_representing_new_indices_of_quib(self, quib: 'Quib', path_component: PathComponent) -> np.ndarray:
        """
        Get a boolean mask representing all new indices of the quib after having passed through the function.
        The boolean mask will be in the shape of the final result of the function
        """
        def _replace_arg_with_corresponding_mask_or_arg(q):
            if q in self.get_quibs_which_can_change():
                if q is quib:
                    return create_empty_array_with_values_at_indices(
                        quib.get_shape().get_value(),
                        indices=path_component.component,
                        value=True,
                        empty_value=False
                    )
                else:
                    return np.full(q.get_shape().get_value(), False)
            return q

        new_arguments = recursively_run_func_on_object(
            func=_replace_arg_with_corresponding_mask_or_arg,
            obj=self._args
        )
        return call_func_with_quib_values(self._func, new_arguments, self._kwargs)

    def _invalidate_with_children(self, invalidator_quib, path):
        if self.func == getitem and isinstance(self._args[1], str):
            # We can't run normal our operation to get a boolean mask representing new indices, since our key is a
            # string- this may mean we're a dict, in which case we can't run the boolean mask op,
            # or we're in a field array, in which case we can't create a boolean mask to work with our key unless we
            # have the dtype (which we dont')
            super(TranspositionalQuib, self)._invalidate_with_children(invalidator_quib=self,
                                                                       path=path)
            return

        boolean_mask = self._get_boolean_mask_representing_new_indices_of_quib(invalidator_quib, path[0])
        if np.any(boolean_mask):
            new_path = [boolean_mask, *path[1:]]
            super(TranspositionalQuib, self)._invalidate_with_children(invalidator_quib=self,
                                                                       path=new_path)

    @functools.lru_cache()
    def get_quibs_which_can_change(self):
        """
        Return a list of quibs that can potentially change as a result of the transpositional function- this does NOT
        necessarily mean these quibs will in fact be changed.

        For example, in `np.repeat(q1, q2)`, where q1 is a numpy array quib
        and q2 is a number quib with amount of times to repeat, q2 cannot in any
        situation be changed by a change in `np.repeat`'s result. So only `q1` would be returned.
        """
        from pyquibbler.quib import Quib
        potentially_changed_quib_indices = self.SUPPORTED_FUNCTIONS_TO_POTENTIALLY_CHANGED_QUIB_INDICES[self._func]
        quibs = []
        for i, arg in enumerate(self._args):
            if i in potentially_changed_quib_indices:
                quibs.extend(iter_objects_of_type_in_object_shallowly(Quib, arg))
        return quibs

    def get_reversals_for_assignment(self, assignment: Assignment):
        return TranspositionalReverser(
            assignment=assignment,
            function_quib=self
        ).get_reversed_quibs_with_assignments()

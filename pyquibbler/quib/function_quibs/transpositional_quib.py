import functools
from operator import getitem
from typing import TYPE_CHECKING, List

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

    def _represent_non_numpy_indexing(self, component):
        return not issubclass(component.indexed_cls, np.ndarray) or component.references_field_in_field_array()

    def _represents_translatable_numpy_indexing(self, component):
        return issubclass(component.indexed_cls, np.ndarray) and not component.references_field_in_field_array()

    def _translate_and_invalidate(self, invalidator_quib, path):
        boolean_mask = self._get_boolean_mask_representing_new_indices_of_quib(invalidator_quib, path[0])
        if np.any(boolean_mask):
            new_path = [PathComponent(indexed_cls=self.get_type(), component=boolean_mask), *path[1:]]
            super(TranspositionalQuib, self)._invalidate_with_children(invalidator_quib=self,
                                                                       path=new_path)

    def _check_first_components_equality_and_invalidate(self, path):
        working_component = path[0]
        if self.args[1] == working_component.component:
            super(TranspositionalQuib, self)._invalidate_with_children(invalidator_quib=self,
                                                                       path=path[1:])

    def _handle_invalidation_on_get_item(self, invalidator_quib, path_to_invalidate):
        """
        Handle invalidation on a getitem quib, correctly choosing whether or not and at what indices to invalidate
        child quibs
        """
        working_component = path_to_invalidate[0]
        getitem_path_component = PathComponent(component=self._args[1], indexed_cls=invalidator_quib.get_type())
        if (
                issubclass(invalidator_quib.get_type(), np.ndarray)
        ):
            if (
                    not getitem_path_component.references_field_in_field_array()
                    and
                    not working_component.references_field_in_field_array()
            ):
                # This means:
                # 1. The invalidator quib's result is an ndarray,
                # 2. Both the path to invalidate and the `item` of the getitem are translatable indices
                #
                # Therefore, we translate the indices and invalidate our children with the new indices (which are an
                # intersection between our getitem and the path to invalidate- if this intersections yields nothing,
                # we do NOT invalidate our children)
                return self._translate_and_invalidate(invalidator_quib, path_to_invalidate)
            elif (
                    getitem_path_component.references_field_in_field_array()
                    !=
                    working_component.references_field_in_field_array()
                    and
                    issubclass(self.get_type(), np.ndarray)
            ):
                # This means
                # 1. Both this function quib's result and the invalidator's result are ndarrays
                # 2. One of the paths references a field in a field array, the other does not
                #
                # Therefore, we want to pass on this invalidation path to our children since indices and field names are
                # interchangeable when indexing structured ndarrays
                super(TranspositionalQuib, self)._invalidate_with_children(invalidator_quib=self,
                                                                           path=path_to_invalidate)
        # We come to our default scenario- if
        # 1. The invalidator quib is not an ndarray
        # or
        # 2. The current getitem is not an ndarray
        # or
        # 3. The invalidation is for a field and the current getitem is for a field
        #
        # We want to only check equality of the invalidation path and our getitem - essentially saying we don't have
        # anything to interpret in the invalidation more than simply checking it's equality.
        # For example, if we have a getitem on a dict, and we are invalidated at the a certain item on the dict,
        # we simply want to check if the paths are equal (ie if the invalidation is equal to the item in our getitem)
        #
        # Number 3 (above) is relavent as well since if we have two keys one after the other,
        return self._check_first_components_equality_and_invalidate(path_to_invalidate)

    def _invalidate_with_children(self, invalidator_quib, path: List[PathComponent]):
        """
        There are three things we can potentially do: 
        1. If we're getitem, equalize where our invalidator quib (which is the quib we're getitem'ing) was invalidated
        and our indices. If they're the same, drop it from the path and invalidate our children
        2. If we're getitem, take where our invalidator quib was invalidated and pass it on to our children
        3. Translate the indices if possible
        """
        if len(path) == 0:
            return super(TranspositionalQuib, self)._invalidate_with_children(invalidator_quib=self, path=[])

        working_component = path[0]
        if self.func == getitem:
            self._handle_invalidation_on_get_item(invalidator_quib, path)
        else:
            # Any other situation ->
            assert issubclass(self.get_type(), np.ndarray)
            if not self._represents_translatable_numpy_indexing(working_component):
                return super(TranspositionalQuib, self)._invalidate_with_children(invalidator_quib=self,
                                                                                  path=path)
            return self._translate_and_invalidate(invalidator_quib, path)

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
        return TranspositionalReverser.create_and_get_reversed_quibs_with_assignments(
            assignment=assignment,
            function_quib=self
        )

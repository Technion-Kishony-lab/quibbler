import numpy as np
import functools
from operator import getitem
from typing import TYPE_CHECKING, List, Optional

from pyquibbler.quib.assignment import Assignment
from .default_function_quib import DefaultFunctionQuib
from pyquibbler.quib.assignment.inverse_assignment import TranspositionalInverser
from pyquibbler.quib.assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.utils import iter_objects_of_type_in_object_shallowly, recursively_run_func_on_object, \
    call_func_with_quib_values
from ..assignment.assignment import PathComponent

if TYPE_CHECKING:
    from .. import Quib


class TranspositionalFunctionQuib(DefaultFunctionQuib):
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
        np.reshape: {0},
        np.ravel: {0}
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

    def _get_translated_path(self, invalidator_quib, path):
        """
        Translate the invalidation path to it's location after passing through the current function quib.
        If that path represents anything (ie any indices intersecting with the invalidation exist in the result),
        invalidate the children with the resulting indices.

        For example, if we have a rotate function, replace the arguments with a grid representing
        the arguments' indices that intersect with the invalidation path, and see where those indices land in the result
        If any indices exist in the result, invalidate all children with the resulting indices (or, in this
        implementation, a boolean mask representing them)
        """
        boolean_mask = self._get_boolean_mask_representing_new_indices_of_quib(invalidator_quib, path[0])
        if np.any(boolean_mask):
            new_path = path[1:]
            assert np.all(boolean_mask) or issubclass(self.get_type(), np.ndarray)
            if not np.all(boolean_mask) and issubclass(self.get_type(), np.ndarray):
                new_path = [PathComponent(indexed_cls=self.get_type(), component=boolean_mask), *path[1:]]
            if len(new_path) == 0:
                new_path = [PathComponent(indexed_cls=self.get_type(), component=...)]
            return new_path
        return None

    def _get_path_for_invalidation_on_get_item(self, invalidator_quib: 'Quib',
                                               path_to_invalidate: List[PathComponent]):
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
                return self._get_translated_path(invalidator_quib, path_to_invalidate)
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
                return path_to_invalidate

        # We come to our default scenario- if
        # 1. The invalidator quib is not an ndarray
        # or
        # 2. The current getitem is not an ndarray
        # or
        # 3. The invalidation is for a field and the current getitem is for a field
        #
        # We want to check equality of the invalidation path and our getitem - essentially saying we don't have
        # anything to interpret in the invalidation path more than simply checking it's equality to our current
        # getitem's `item`.
        # For example, if we have a getitem on a dict, and we are requested to be
        # invalidated at a certain item on the dict,
        # we simply want to check if our getitem's item is equal to the invalidations item (ie it's path).
        # If so, invalidate. This is true for field arrays as well (We do need to
        # add support for indexing multiple fields).
        if self.args[1] == working_component.component:
            rest_of_path = path_to_invalidate[1:]
            if len(rest_of_path) == 0:
                return [PathComponent(indexed_cls=self.get_type(), component=...)]
            return path_to_invalidate[1:]

        return []

    def _quib_in_data_quibs(self, quib: 'Quib'):
        """
        Whether or not the current function quib can change the given quib
        """
        return quib in self.get_quibs_which_can_change()

    def _get_path_for_children_invalidation(self, invalidator_quib: 'Quib',
                                            path: List[PathComponent]) -> Optional[List[PathComponent]]:
        """
        There are three things we can potentially do:
        1. Translate the invalidation path given the current function quib (eg if this function quib is rotate,
        take the invalidated indices, rotate them and invalidate children with the resulting indices)
        2. In getitem, check equality of indices and invalidation path- if so, continue with path[1:]
        3. Pass on the current path to all our children
        """
        if self.func == getitem:
            return self._get_path_for_invalidation_on_get_item(invalidator_quib, path)
        else:
            if path[0].references_field_in_field_array():
                # The path at the first component references a field, and therefore we cannot translate it given a
                # normal transpositional function
                return path
            if not self._quib_in_data_quibs(invalidator_quib):
                # Any param quib should invalidate ALL children- it is not simply the data being changed, but how the
                # data is processed by the transpositional function
                return [PathComponent(indexed_cls=self.get_type(), component=...)]
            return self._get_translated_path(invalidator_quib, path)

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

    def get_inversals_for_assignment(self, assignment: Assignment):
        return TranspositionalInverser.create_and_get_inversed_quibs_with_assignments(
            assignment=assignment,
            function_quib=self
        )

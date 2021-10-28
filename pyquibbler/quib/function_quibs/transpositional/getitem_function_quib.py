from __future__ import annotations
from typing import List, Optional

import numpy as np

from pyquibbler.quib import TranspositionalFunctionQuib, Quib
from pyquibbler.quib.assignment import PathComponent


class GetItemFunctionQuib(TranspositionalFunctionQuib):

    def _get_paths_for_children_invalidation(self, invalidator_quib: Quib,
                                             path: List[PathComponent]) -> List[Optional[List[PathComponent]]]:
        """
        Handle invalidation on a getitem quib, correctly choosing whether or not and at what indices to invalidate
        child quibs
        """
        working_component, *rest_of_path = path
        getitem_path_component = PathComponent(component=self._args[1], indexed_cls=invalidator_quib.get_type())
        if issubclass(invalidator_quib.get_type(), np.ndarray):
            if (not getitem_path_component.references_field_in_field_array()
                    and not working_component.references_field_in_field_array()):
                # This means:
                # 1. The invalidator quib's result is an ndarray, (We're a getitem on that said ndarray)
                # 2. Both the path to invalidate and the `item` of the getitem are translatable indices
                #
                # Therefore, we translate the indices and invalidate our children with the new indices (which are an
                # intersection between our getitem and the path to invalidate- if this intersections yields nothing,
                # we do NOT invalidate our children)
                return [self._forward_translate_invalidation_path(invalidator_quib, path)]
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
                return [path]

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
            return [rest_of_path]

        # The item in our getitem was not equal to the path to invalidate
        return [None]

    @property
    def _getitem_path_component(self):
        component = self._args[1]
        # We can't have a quib in our path, as this would mean we wouldn't be able to understand where it's necessary
        # to get_value's/reverse assign
        if isinstance(component, Quib):
            component = component.get_value()
        return PathComponent(indexed_cls=self._args[0].get_type(), component=component)

    def _can_squash_start_of_path(self, filtered_path_in_result: List[PathComponent]):
        return issubclass(self.get_type(), np.ndarray) \
               and not self._getitem_path_component.references_field_in_field_array() \
               and len(filtered_path_in_result) > 0 \
               and not filtered_path_in_result[0].references_field_in_field_array() \
               and issubclass(self._args[0].get_type(), np.ndarray)

    def _get_quibs_to_relevant_result_values(self, assignment):
        if self._can_squash_start_of_path(assignment.path):
            return super(GetItemFunctionQuib, self)._get_quibs_to_relevant_result_values(assignment)
        return {
            self._args[0]: assignment.value
        }

    def _get_source_paths_of_quibs_given_path(self, filtered_path_in_result: List[PathComponent]):
        if self._can_squash_start_of_path(filtered_path_in_result):
            # Translate the indices
            return super(GetItemFunctionQuib, self)._get_source_paths_of_quibs_given_path(filtered_path_in_result)
        return {
            self._args[0]: [self._getitem_path_component, *filtered_path_in_result]
        }

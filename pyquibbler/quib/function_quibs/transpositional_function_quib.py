import numpy as np
from operator import getitem
from typing import List, Optional, Any

from pyquibbler.quib.quib import Quib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.inverse_assignment import TranspositionalInverter
from pyquibbler.quib.utils import recursively_run_func_on_object, call_func_with_quib_values

from .default_function_quib import DefaultFunctionQuib
from .indices_translator_function_quib import IndicesTranslatorFunctionQuib, SupportedFunction
from ..assignment.assignment import PathComponent


class TranspositionalFunctionQuib(DefaultFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    A quib that represents any transposition function- a function that moves elements (but commits no operation on
    them)
    """
    SUPPORTED_FUNCTIONS = {
        np.rot90: SupportedFunction({0}),
        np.concatenate: SupportedFunction({0}),
        np.repeat: SupportedFunction({0}),
        np.full: SupportedFunction({1}),
        getitem: SupportedFunction({0}),
        np.reshape: SupportedFunction({0}),
        np.ravel: SupportedFunction({0}),
    }

    def _forward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        """
        Translate the invalidation path to it's location after passing through the current function quib.
        If that path represents anything (ie any indices intersecting with the invalidation exist in the result),
        invalidate the children with the resulting indices.

        For example, if we have a rotate function, replace the arguments with a grid representing
        the arguments' indices that intersect with the invalidation path, and see where those indices land in the result
        If any indices exist in the result, invalidate all children with the resulting indices (or, in this
        implementation, a boolean mask representing them)
        """

        def _replace_arg_with_corresponding_mask_or_arg(q):
            if isinstance(q, Quib) and q in self.get_data_source_quibs():
                if q is quib:
                    return self._get_source_shaped_bool_mask(q, indices)
                else:
                    return np.full(q.get_shape().get_value(), False)
            return q

        new_arguments = recursively_run_func_on_object(
            func=_replace_arg_with_corresponding_mask_or_arg,
            obj=self._args
        )
        return call_func_with_quib_values(self._func, new_arguments, self._kwargs)

    def _get_path_for_invalidation_on_get_item(self, invalidator_quib: 'Quib', path_to_invalidate: List[PathComponent]):
        """
        Handle invalidation on a getitem quib, correctly choosing whether or not and at what indices to invalidate
        child quibs
        """
        working_component, *rest_of_path = path_to_invalidate
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
                return self._forward_translate_invalidation_path(invalidator_quib, path_to_invalidate)
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
            return rest_of_path

        # The item in our getitem was not equal to the path to invalidate
        return None

    def _get_path_for_children_invalidation(self, invalidator_quib: 'Quib',
                                            path: List[PathComponent]) -> Optional[List[PathComponent]]:
        """
        There are three things we can potentially do:
        1. Translate the invalidation path given the current function quib (eg if this function quib is rotate,
        take the invalidated indices, rotate them and invalidate children with the resulting indices)
        2. In getitem, if the source quib is a list or a dict, check equality of indices and invalidation path-
           if so, continue with path[1:]
        3. Pass on the current path to all our children
        """
        if self.func is getitem:
            return self._get_path_for_invalidation_on_get_item(invalidator_quib, path)
        if path[0].references_field_in_field_array():
            # The path at the first component references a field, and therefore we cannot translate it given a
            # normal transpositional function (neither does it make any difference, as transpositional functions
            # don't change fields)
            return path
        return super()._get_path_for_children_invalidation(invalidator_quib, path)

    def get_inversions_for_assignment(self, assignment: Assignment):
        return TranspositionalInverter.create_and_get_inversed_quibs_with_assignments(
            assignment=assignment,
            function_quib=self
        )

from typing import Dict, Type

import numpy as np

from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.translation.numpy_translator import OldNumpyForwardsPathTranslator
from pyquibbler.translation.translators.transpositional.transpositional_path_translator import \
    BackwardsTranspositionalTranslator
from pyquibbler.translation.translators.transpositional.types import is_focal_element
from pyquibbler.translation.numpy_translation_utils import convert_args_kwargs_to_source_index_codes, \
    run_func_call_with_new_args_kwargs
from pyquibbler.translation.types import Source
from pyquibbler.path import PathComponent
from pyquibbler.path.path_component import Path, Paths
from pyquibbler.translation.utils import copy_and_replace_sources_with_vals


def _getitem_path_component(func_call: FuncCall) -> PathComponent:
    component = func_call.args[1]
    component = copy_and_replace_sources_with_vals(component)
    return PathComponent(component)


def _type_of_referenced_object(func_call: FuncCall) -> Type:
    data = func_call.args[0]
    return type(data.value) if isinstance(data, Source) else type(data)


def _referencing_field_in_field_array(func_call: FuncCall) -> bool:
    return _getitem_path_component(func_call).referencing_field_in_field_array(_type_of_referenced_object(func_call))


class BackwardsGetItemTranslator(BackwardsTranspositionalTranslator):

    def _referenced_value(self):
        return copy_and_replace_sources_with_vals(self._func_call.args[0])

    def _getitem_component(self):
        return copy_and_replace_sources_with_vals(self._func_call.args[1])

    def _can_squash_start_of_path(self) -> bool:
        data = self._referenced_value()
        component = self._getitem_component()
        return issubclass(self._type, np.ndarray) \
            and not _referencing_field_in_field_array(self._func_call) \
            and len(self._path) > 0 \
            and not self._path[0].referencing_field_in_field_array(_type_of_referenced_object(self._func_call)) \
            and isinstance(data, np.ndarray) \
            and not (data.dtype.type is np.object_ and isinstance(data[component], np.ndarray))
        # TODO: The above line is an ad hoc solution to the test_array_of_arrays bug

    def backwards_translate(self) -> Dict[Source, Path]:
        if self._can_squash_start_of_path():
            return super(BackwardsGetItemTranslator, self).backwards_translate()
        return {
            self._func_call.args[0]: [_getitem_path_component(self._func_call), *self._path]
        }


class ForwardsGetItemTranslator(OldNumpyForwardsPathTranslator):

    def forward_translate_initial_path_to_bool_mask(self, path: Path):
        func_args_kwargs, _, _, _ = \
            convert_args_kwargs_to_source_index_codes(self._func_call, self._source, self._source_location, self._path)
        result_index_code = run_func_call_with_new_args_kwargs(self._func_call, func_args_kwargs)
        return is_focal_element(result_index_code)

    def forward_translate(self) -> Paths:

        path = self._path
        if len(path) == 0:
            return [[]]

        working_component, *rest_of_path = self._path
        is_working_component_referencing_field_in_field_array = \
            working_component.referencing_field_in_field_array(_type_of_referenced_object(self._func_call))
        if isinstance(self._source.value, np.ndarray):
            if (not _referencing_field_in_field_array(self._func_call)
                    and not is_working_component_referencing_field_in_field_array):
                # This means:
                # 1. The invalidator quib's result is an ndarray, (We're a getitem on that said ndarray)
                # 2. Both the path to invalidate and the `item` of the getitem are translatable indices
                #
                # Therefore, we translate the indices and invalidate our children with the new indices (which are an
                # intersection between our getitem and the path to invalidate- if this intersections yields nothing,
                # we do NOT invalidate our children)
                return super(ForwardsGetItemTranslator, self).forward_translate()

            elif (
                    _referencing_field_in_field_array(self._func_call)
                    !=
                    is_working_component_referencing_field_in_field_array
                    and
                    issubclass(self._type, np.ndarray)
            ):
                # This means
                # 1. Both this function quib's result and the invalidator's result are ndarrays
                # 2. One of the paths references a field in a field array, the other does not
                #
                # Therefore, we want to pass on this invalidation path to our children since indices and field names are
                # interchangeable when indexing structured ndarrays
                return [path]

        if isinstance(self._source.value, list) and len(path) == 1:
            return super(ForwardsGetItemTranslator, self).forward_translate()

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
        assert not isinstance(working_component.component, np.ndarray)
        if _getitem_path_component(self._func_call).component == working_component.component:
            return [rest_of_path]

        # The item in our getitem was not equal to the path to invalidate
        return []

from typing import Dict

import numpy as np

from pyquibbler.refactor.translation.translators.transpositional.transpositional_path_translator import \
    BackwardsTranspositionalTranslator, ForwardsTranspositionalTranslator
from pyquibbler.refactor.translation.types import Source
from pyquibbler.refactor.path import PathComponent
from pyquibbler.refactor.path.path_component import Path
from pyquibbler.refactor.translation.utils import copy_and_replace_sources_with_vals


class BackwardsGetItemTranslator(BackwardsTranspositionalTranslator):

    PRIORITY = 1

    @property
    def _getitem_path_component(self):
        component = self._args[1]
        return PathComponent(indexed_cls=type(self._args[0].value), component=component)

    def _can_squash_start_of_path(self):
        return issubclass(self._type, np.ndarray) \
               and not self._getitem_path_component.references_field_in_field_array() \
               and len(self._path) > 0 \
               and not self._path[0].references_field_in_field_array() \
               and isinstance(self._args[0].value, np.ndarray)

    def translate_in_order(self) -> Dict[Source, Path]:
        if self._can_squash_start_of_path():
            return super(BackwardsGetItemTranslator, self).translate_in_order()
        return {
            self._args[0]: [self._getitem_path_component, *self._path]
        }


class ForwardsGetItemTranslator(ForwardsTranspositionalTranslator):

    @property
    def _getitem_path_component(self):
        component = self._args[1]
        # We can't have a quib in our path, as this would mean we wouldn't be able to understand where it's necessary
        # to get_value's/reverse assign
        component = copy_and_replace_sources_with_vals(component)
        return PathComponent(indexed_cls=self._type, component=component)

    def _forward_translate_source(self, source: Source, path: Path):
        working_component, *rest_of_path = path
        if isinstance(source.value, np.ndarray):
            if (not self._getitem_path_component.references_field_in_field_array()
                    and not working_component.references_field_in_field_array()):
                # This means:
                # 1. The invalidator quib's result is an ndarray, (We're a getitem on that said ndarray)
                # 2. Both the path to invalidate and the `item` of the getitem are translatable indices
                #
                # Therefore, we translate the indices and invalidate our children with the new indices (which are an
                # intersection between our getitem and the path to invalidate- if this intersections yields nothing,
                # we do NOT invalidate our children)
                return super(ForwardsGetItemTranslator, self)._forward_translate_source(source=source, path=path)
            elif (
                    self._getitem_path_component.references_field_in_field_array()
                    !=
                    working_component.references_field_in_field_array()
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
        if self._getitem_path_component.component == working_component.component:
            return [rest_of_path]

        # The item in our getitem was not equal to the path to invalidate
        return []

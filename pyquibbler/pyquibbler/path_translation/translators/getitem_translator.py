from abc import abstractmethod
from typing import Dict, Type

import numpy as np

from pyquibbler.path import PathComponent, Path, Paths
from pyquibbler.utilities.multiple_instance_runner import ConditionalRunner

from ..base_translators import BackwardsPathTranslator, ForwardsPathTranslator
from ..utils import copy_and_replace_sources_with_vals
from ..types import Source


class BaseGetItemTranslator(ConditionalRunner):

    @property
    def _referenced_object(self):
        return self._func_call.args[0]

    @property
    def _referenced_value(self):
        return copy_and_replace_sources_with_vals(self._referenced_object)

    @property
    def _getitem_component(self):
        return copy_and_replace_sources_with_vals(self._func_call.args[1])

    def _get_getitem_path_component(self) -> PathComponent:
        return PathComponent(self._getitem_component)

    def _get_type_of_referenced_value(self) -> Type:
        return type(self._referenced_value)

    def _getitem_of_a_field_in_array(self) -> bool:
        return self._get_getitem_path_component().referencing_field_in_field_array(self._get_type_of_referenced_value())

    def _getitem_of_array(self) -> bool:
        return issubclass(self._get_type_of_referenced_value(), np.ndarray)

    def _getitem_of_list_to_list(self) -> bool:
        return issubclass(self._get_type_of_referenced_value(), (list, tuple)) \
            and self._get_getitem_path_component().is_list_to_list_reference()

    @abstractmethod
    def _is_path_referencing_field_in_field_array(self) -> bool:
        pass

    def can_try(self) -> bool:
        """
        We do not use this translator if we are referring an array, with indices (not field).
        In this case, the TranspositionalBackwardsPathTranslator will be used.
        """
        return not (len(self._path) > 0
                    and (self._getitem_of_array() or self._getitem_of_list_to_list())
                    and not self._getitem_of_a_field_in_array()
                    and not self._is_path_referencing_field_in_field_array())


class GetItemBackwardsPathTranslator(BackwardsPathTranslator, BaseGetItemTranslator):

    def _is_path_referencing_field_in_field_array(self) -> bool:
        return self._path[0].referencing_field_in_field_array(self._type)

    def _backwards_translate(self) -> Dict[Source, Path]:
        return {self._referenced_object: [self._get_getitem_path_component(), *self._path]}


class GetItemForwardsPathTranslator(ForwardsPathTranslator, BaseGetItemTranslator):

    def _is_path_referencing_field_in_field_array(self) -> bool:
        return self._path[0].referencing_field_in_field_array(self._get_type_of_referenced_value())

    def _forward_translate(self) -> Paths:

        path = self._path
        if len(path) == 0:
            return [[]]

        if self._getitem_of_a_field_in_array() ^ self._is_path_referencing_field_in_field_array():
            return [path]

        working_component, *rest_of_path = self._path
        if self._get_getitem_path_component().component == working_component.component:
            return [rest_of_path]

        # The item in our getitem was not equal to the path to invalidate
        return []

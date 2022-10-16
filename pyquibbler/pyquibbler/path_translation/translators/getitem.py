from abc import abstractmethod
from typing import Dict, Type

import numpy as np

from pyquibbler.path import PathComponent, Path, Paths
from pyquibbler.utilities.multiple_instance_runner import ConditionalRunner

from ..base_translators import BackwardsPathTranslator, ForwardsPathTranslator
from ..utils import copy_and_replace_sources_with_vals
from ..types import Source
from ...utilities.numpy_original_functions import np_all, np_any


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


def get_shared_component(component1, component2):
    is_bool_array1 = isinstance(component1, np.ndarray) and component1.dtype.type is np.bool_
    is_bool_array2 = isinstance(component2, np.ndarray) and component2.dtype.type is np.bool_

    if not is_bool_array1 and not is_bool_array2:
        # TODO: this is not right for complex indexing
        return np.array_equal(component1, component2)
    if is_bool_array1 and is_bool_array2:
        return component1 & component2

    # One is a bool array. the other not.
    if is_bool_array1:
        return component1[component2]
    else:
        return component2[component1]


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
        shared_component = get_shared_component(self._get_getitem_path_component().component,
                                                working_component.component)
        if np_all(shared_component):
            return [rest_of_path]
        if np_any(shared_component):
            return [[PathComponent(shared_component)] + rest_of_path]

        # The item in our getitem was not equal to the path to invalidate
        return []

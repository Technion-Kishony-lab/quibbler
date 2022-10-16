import warnings
from typing import List

import numpy as np
from abc import ABC, abstractmethod

from pyquibbler.assignment.assignment import create_assignment_from_nominal_down_up_values
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.path_translation.types import Source, Inversal


class CastingInverter(Inverter, ABC):

    @staticmethod
    @abstractmethod
    def _get_value_to_set(source_to_change_value, assigned_value):
        pass

    def get_inversals(self) -> List[Inversal]:
        if len(self._func_call.args) != 1 \
                or not isinstance(self._func_call.args[0], Source) \
                or len(self._assignment.path) > 0:
            self._raise_run_failed_exception()

        source_to_change = self._func_call.args[0]
        assigned_nominal_down_up_values = self._get_assignment_nominal_down_up_values()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                type_ = self._func_call.func
                assigned_nominal_down_up_values = [type_(assigned_value)
                                                   for assigned_value in assigned_nominal_down_up_values]
                nominal_down_up_values_to_set = [self._get_value_to_set(
                    source_to_change_value=source_to_change.value,
                    assigned_value=assigned_value,
                ) for assigned_value in assigned_nominal_down_up_values]
            except TypeError:
                self._raise_run_failed_exception()
        new_assignment = create_assignment_from_nominal_down_up_values(
            nominal_down_up_values=nominal_down_up_values_to_set,
            path=[])

        return [Inversal(source=source_to_change, assignment=new_assignment)]


class NumericCastingInverter(CastingInverter):

    @staticmethod
    def _get_value_to_set(source_to_change_value, assigned_value):

        source_to_change_type = type(source_to_change_value)
        if source_to_change_type is np.ndarray:
            assert len(source_to_change_value) == 1
            return np.array([assigned_value], dtype=source_to_change_value.dtype).reshape(source_to_change_value.shape)

        return source_to_change_type(assigned_value)


class BoolCastingInverter(NumericCastingInverter):

    @staticmethod
    def _get_value_to_set(source_to_change_value, assigned_value):
        if isinstance(source_to_change_value, str):
            raise TypeError
        return super(BoolCastingInverter, BoolCastingInverter)._get_value_to_set(source_to_change_value, assigned_value)


class StrCastingInverter(CastingInverter):

    @staticmethod
    def _get_value_to_set(source_to_change_value, assigned_value):
        source_to_change_type = type(source_to_change_value)
        if source_to_change_type is list \
                or source_to_change_type is np.ndarray:
            value_to_set = eval(assigned_value)
            if not isinstance(value_to_set, list):
                raise TypeError
            if source_to_change_type is np.ndarray:
                value_to_set = np.array(value_to_set)
            return value_to_set

        else:
            return source_to_change_type(assigned_value)

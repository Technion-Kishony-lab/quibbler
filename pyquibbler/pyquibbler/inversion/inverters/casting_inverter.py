import warnings

import numpy as np

from pyquibbler import Assignment
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.translation.types import Source, Inversal
from abc import ABC, abstractmethod


class CastingInverter(Inverter, ABC):

    @staticmethod
    @abstractmethod
    def _get_value_to_set(source_to_change_value, assigned_value):
        pass

    def get_inversals(self):
        if len(self._func_call.args) != 1 \
                or not isinstance(self._func_call.args[0], Source) \
                or len(self._assignment.path) > 0:
            raise self._raise_faile_to_invert_exception()

        source_to_change = self._func_call.args[0]

        assignment_path = []

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                assigned_value = self._assignment.value
                type_ = self._func_call.func
                if not isinstance(assigned_value, type_):
                    assigned_value = type_(assigned_value)
                value_to_set = self._get_value_to_set(
                    source_to_change_value=source_to_change.value,
                    assigned_value=assigned_value,
                )
            except Exception:
                self._raise_faile_to_invert_exception()
        return [
            Inversal(
                source=source_to_change,
                assignment=Assignment(
                    path=assignment_path,
                    value=value_to_set
                )
            )
        ]


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
            raise Exception
        return super(BoolCastingInverter, BoolCastingInverter)._get_value_to_set(source_to_change_value, assigned_value)


class StrCastingInverter(CastingInverter):

    @staticmethod
    def _get_value_to_set(source_to_change_value, assigned_value):
        source_to_change_type = type(source_to_change_value)
        if source_to_change_type is list \
                or source_to_change_type is np.ndarray:
            value_to_set = eval(assigned_value)
            assert isinstance(value_to_set, list)
            if source_to_change_type is np.ndarray:
                value_to_set = np.array(value_to_set)
            return value_to_set

        else:
            return source_to_change_type(assigned_value)

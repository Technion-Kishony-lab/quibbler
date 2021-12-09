from operator import __pow__

import numpy as np
import pytest
from typing import Callable, Tuple, Any, Mapping

from pyquibbler import iquib, Assignment
from pyquibbler.path_translators.inversal_types import Source
from pyquibbler.path_translators.transpositional_path_translator import TranspositionalInverter
from pyquibbler.path_translators.utils import call_func_with_values
from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_in_path
from pyquibbler.quib.function_quibs.utils import ArgsValues, FuncWithArgsValues



def inverse(func: Callable, indices: Any, value: Any, args: Tuple[Any, ...] = None, kwargs: Mapping[str, Any] = None):
    args = args or tuple()
    kwargs = kwargs or {}
    previous_value = call_func_with_values(func, args, kwargs)
    inversals = TranspositionalInverter(
        func_with_args_values=FuncWithArgsValues.from_function_call(func, args=args,
                                                                    kwargs=kwargs, include_defaults=True),
        previous_value=previous_value,
        assignment=Assignment(path=[PathComponent(indexed_cls=np.ndarray, component=indices)], value=value)
    ).get_inversals()

    return {
        inversal.source: deep_assign_data_in_path(inversal.source.value,
                                                  inversal.assignment.path,
                                                  inversal.assignment.value)
        for inversal in inversals
    }


def test_inverse_rot90():
    source = Source(np.array([[1, 2, 3]]))
    new_value = 200

    sources_to_results = inverse(func=np.rot90, args=(source,), value=np.array([new_value]), indices=[0])

    assert np.array_equal(sources_to_results[source], np.array([[1, 2, new_value]]))


def test_inverse_concat():
    first_source_arg = Source(np.array([[1, 2, 3]]))
    second_source_arg = Source(np.array([[8, 12, 14]]))
    new_value = 20

    sources_to_results = inverse(func=np.concatenate, args=((first_source_arg, second_source_arg),), indices=(0, 0),
                                 value=np.array([new_value]))

    assert np.array_equal(sources_to_results[first_source_arg], np.array([[new_value, 2, 3]]))

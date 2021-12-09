from operator import __pow__

import numpy as np
import pytest

from pyquibbler import iquib, Assignment
from pyquibbler.path_translators.inversal_types import Source
from pyquibbler.path_translators.transpositional_path_translator import TranspositionalInverter
from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_in_path
from pyquibbler.quib.function_quibs.utils import ArgsValues, FuncWithArgsValues




def test_inverse_rot90():
    new_value = 200
    source = Source([[1, 2, 3]])
    assignment = Assignment(
        path=[PathComponent(indexed_cls=np.ndarray, component=[0])],
        value=np.array([new_value])
    )
    inversals = TranspositionalInverter(
        keyword_arguments_which_can_be_inverted=[""],
        index_arguments_which_can_be_inverted=[],
        func_with_args_values=FuncWithArgsValues.from_function_call(np.rot90, args=(source,),
                                                                    kwargs={}, include_defaults=True),
        previous_value=np.array([[3], [2], [1]]),
        assignment=assignment
    ).get_inversals()

    assert len(inversals) == 1
    inversal = inversals[0]
    assert inversal.source is source
    value = deep_assign_data_in_path(source.value, inversal.assignment.path, inversal.assignment.value)
    assert np.array_equal(value, np.array([[1, 2, new_value]]))


#
# def test_inverse_rot90():
#     quib_arg = iquib(np.array([[1, 2, 3]]))
#     new_value = 200
#
#     inverse(func=np.rot90, args=(quib_arg,), value=np.array([new_value]), indices=[0])
#
#     assert np.array_equal(quib_arg.get_value(), np.array([[1, 2, new_value]]))
#

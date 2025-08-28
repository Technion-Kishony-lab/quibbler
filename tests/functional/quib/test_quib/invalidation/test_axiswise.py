import numpy as np
import pytest

from pyquibbler import quiby
from pyquibbler.function_definitions.types import DataArgumentDesignation, \
    convert_raw_data_arguments_to_data_argument_designations
from pyquibbler.path_translation.translators import AxisAllToAllBackwardsPathTranslator, AxisAllToAllForwardsPathTranslator
from tests.functional.quib.test_quib.get_value.test_apply_along_axis import parametrize_indices_to_invalidate, \
    parametrize_data
from tests.functional.quib.test_quib.invalidation.utils import check_invalidation

# we can't use np.sort, because some element changes may not lead to changes in all elements in the axis
# (the actual change depends on the newly assigned value)

def axiswise_func(arr, axis):
    return np.broadcast_to(np.sum(arr, axis, keepdims=True), np.shape(arr))


axiswise_func = quiby(axiswise_func,
                      raw_data_source_arguments=[0],
                      backwards_path_translators=[AxisAllToAllBackwardsPathTranslator],
                      forwards_path_translators=[AxisAllToAllForwardsPathTranslator])


@parametrize_indices_to_invalidate
@parametrize_data
@pytest.mark.parametrize('axis', [-1, 0, 1, 2, None])
def test_axiswise_invalidation(indices_to_invalidate, axis, data):
    check_invalidation(lambda quib: axiswise_func(quib, axis=axis), data, indices_to_invalidate)

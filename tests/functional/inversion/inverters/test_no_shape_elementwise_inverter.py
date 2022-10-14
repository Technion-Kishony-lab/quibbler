import numpy as np
import pytest
from typing import Iterable

from pyquibbler.path_translation.types import Source
from tests.functional.inversion.inverters.utils import inverse


@pytest.mark.parametrize("func,func_arg,indices,value,expected_value", [
    (np.log2, Source(np.array([4, 4, 4])), slice(None, None, None), 3, np.array([8, 8, 8])),
    (np.log2, Source(np.array([[4, 4], [4, 4]])), (0, slice(0, None, None)), 3, np.array([[8, 8], [4, 4]])),
], ids=[
    "log2: array[:]",
    "log2: array[0, 0:]",
])
def test_inverse_elementwise_no_shape_single_argument(func, func_arg, indices, value, expected_value):
    sources_to_results, inversals = inverse(func, indices=indices, value=value, args=(func_arg,), empty_path=indices is None)
    assert inversals[0].assignment.path[0].component == indices
    value = sources_to_results[func_arg]
    if isinstance(expected_value, Iterable):
        assert np.array_equal(value, expected_value)
    else:
        assert value == expected_value

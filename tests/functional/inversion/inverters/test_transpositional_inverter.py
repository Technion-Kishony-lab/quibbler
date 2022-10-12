import numpy as np
import pytest

from pyquibbler import Assignment
from pyquibbler.path import PathComponent
from pyquibbler.translation.types import Source
from pyquibbler.user_utils.obj2quib import identity_function_list2quib, identity_function_tuple2quib
from pyquibbler.utilities.iterators import recursively_compare_objects
from tests.functional.inversion.inverters.utils import inverse


def test_inverse_rot90():
    source = Source(np.array([[1, 2, 3]]))
    new_value = 200

    sources_to_results, _ = inverse(func=np.rot90, args=(source,), value=np.array([new_value]), indices=[0])

    assert np.array_equal(sources_to_results[source], np.array([[1, 2, new_value]]))


def test_inverse_concat():
    first_source_arg = Source(np.array([[1, 2, 3]]))
    second_source_arg = Source(np.array([[8, 12, 14]]))
    new_value = 20

    sources_to_results, _ = inverse(func=np.concatenate, args=((first_source_arg, second_source_arg),), indices=(0, 0),
                                    value=np.array([new_value]))

    assert np.array_equal(sources_to_results[first_source_arg], np.array([[new_value, 2, 3]]))


@pytest.mark.regression
def test_inverse_concat_second_arg_non_source_returns_no_inversions():
    sources_to_results, _ = inverse(func=np.concatenate, args=((Source([1]), [0]),), indices=1,
                                    value=np.array([100]))

    assert sources_to_results == {}


def test_inverse_concat_in_both_arguments():
    first_source = Source(np.array([[1, 2, 3]]))
    second_source = Source(np.array([[8, 12, 14]]))
    first_new_value = 200
    second_new_value = 300

    sources_to_results, _ = inverse(func=np.concatenate, args=((first_source, second_source),),
                                    indices=([0, 1], [0, 0]),
                                    value=np.array([first_new_value, second_new_value]))

    assert np.array_equal(sources_to_results[first_source], np.array([[first_new_value, 2, 3]]))
    assert np.array_equal(sources_to_results[second_source], np.array([[second_new_value, 12, 14]]))


@pytest.mark.regression
def test_inverse_repeat_with_source_as_parameter():
    arg_arr = np.array([1, 2, 3, 4])
    repeat_count = Source(3)

    sources_to_results, _ = inverse(func=np.repeat, args=(arg_arr, repeat_count, 0), indices=(np.array([0]),),
                                    value=[120])

    assert sources_to_results == {}


@pytest.mark.regression
def test_inverse_repeat_with_sources_as_data_and_param():
    new_value = 120
    data_source = Source(np.array([1, 2, 3, 4]))
    paramater_source = Source(3)

    sources_to_results, _ = inverse(func=np.repeat, args=(data_source, paramater_source, 0),
                                    indices=(np.array([4]),),
                                    value=[new_value])

    assert np.array_equal(sources_to_results[data_source], np.array([
        1, new_value, 3, 4
    ]))


def test_inverse_assign_full():
    data_source = Source(5)

    sources_to_results, _ = inverse(func=np.full, args=((1, 3), data_source),
                                    indices=([0], [1]),
                                    value=10)

    assert sources_to_results[data_source] == 10


def test_inverse_assign_reshape():
    data_source = Source(np.arange(9))

    sources_to_results, _ = inverse(func=np.reshape, args=(data_source, (3, 3)), value=10, indices=(0, 0))

    assert np.array_equal(sources_to_results[data_source], np.array([10, 1, 2, 3, 4, 5, 6, 7, 8]))


def test_inverse_assign_list_within_list():
    data_source = Source([[1, 2, 3, 4]])

    sources_to_results, _ = inverse(func=np.array, args=(data_source,), value=10, indices=(0, 0))

    assert sources_to_results[data_source] == [[10, 2, 3, 4]]


def test_inverse_assign_list2quib():
    data_source = Source([1, 2, 3, 4])

    sources_to_results, _ = inverse(func=identity_function_list2quib, args=(data_source,), value=10, indices=2)

    assert recursively_compare_objects(sources_to_results[data_source], [1, 2, 10, 4])


def test_inverse_assign_tuple2quib():
    data_source = Source((1, 2, 3, 4))

    sources_to_results, _ = inverse(func=identity_function_tuple2quib, args=(data_source,), value=10, indices=2)

    assert recursively_compare_objects(sources_to_results[data_source], (1, 2, 10, 4))

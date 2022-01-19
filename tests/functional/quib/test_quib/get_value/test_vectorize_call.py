import functools
from unittest import mock

import numpy as np
import pytest
from matplotlib import pyplot as plt

from pyquibbler import CacheBehavior, iquib, Assignment
from pyquibbler.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.assignment import AssignmentToQuib, Override
from pyquibbler.path.path_component import PathComponent
from pyquibbler.assignment import get_override_group_for_change
from tests.functional.utils import PathBuilder, get_func_mock
from tests.functional.quib.test_quib.get_value.test_apply_along_axis import parametrize_data
from tests.functional.quib.test_quib.get_value.utils import check_get_value_valid_at_path, collecting_quib


@parametrize_data
@pytest.mark.parametrize('func', [lambda x: np.sum(x)])
@pytest.mark.parametrize('indices_to_get_value_at', [0, (0, 0), (-1, ...)])
def test_vectorize_get_value_valid_at_path(data, func, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(np.vectorize(func), data, path_to_get_value_at)


@pytest.mark.parametrize('pass_quibs', [True])
def test_vectorize_get_value_valid_at_path_with_excluded_quib(pass_quibs):
    excluded = collecting_quib(np.array([1, 2, 3]))

    @functools.partial(np.vectorize, excluded={1}, signature='(n)->(m)', pass_quibs=pass_quibs)
    def func(_a, b):
        if pass_quibs:
            assert b.args[0] is excluded
        return b

    fquib = func([0, 1], excluded)
    fquib.cache_behavior = CacheBehavior.OFF
    path = PathBuilder(fquib)[0].path

    with excluded.collect_valid_paths() as valid_paths:
        fquib.get_value_valid_at_path(path)

    assert valid_paths == [[]]


@pytest.mark.parametrize(['quib_data', 'non_quib_data'], [
    (np.zeros((2, 3)), np.zeros((4, 2, 3))),
    (np.zeros((3, 3)), np.zeros((1, 3))),
    (np.zeros((1, 3, 3)), np.zeros((4, 1, 3))),
    (np.zeros((4, 2, 3)), np.zeros((2, 3))),
])
def test_vectorize_get_value_valid_at_path_when_args_have_different_loop_dimensions(quib_data, non_quib_data):
    func = lambda quib: np.vectorize(lambda x, y: x + y)(quib, quib_data)
    check_get_value_valid_at_path(func, non_quib_data, [PathComponent(np.ndarray, 0)])


@pytest.mark.parametrize('indices_to_get_value_at', [0, (1, 1), (1, ..., 2)])
def test_vectorize_get_value_at_path_with_core_dims(indices_to_get_value_at):
    quib_data = np.zeros((2, 2, 3, 4))
    non_quib_data = np.zeros((2, 3, 4, 5))
    func = lambda a, b: np.array([np.sum(a) + np.sum(b)] * 6)
    vec = np.vectorize(func, signature='(a,b),(c)->(d)')
    check_get_value_valid_at_path(lambda quib: vec(non_quib_data, quib), quib_data,
                                  [PathComponent(np.ndarray, indices_to_get_value_at)])


def test_vectorize_partial_calculation():
    def f(x):
        return x

    func_mock = get_func_mock(f)
    with GRAPHICS_EVALUATE_NOW.temporary_set(True):
        quib = np.vectorize(func_mock)(iquib(np.arange(3)))
    # Should call func_mock twice
    quib.get_value_valid_at_path(PathBuilder(quib)[0].path)
    assert func_mock.call_count == 2, func_mock.mock_calls
    # Should call func_mock one time
    quib.get_value_valid_at_path(PathBuilder(quib)[1].path)
    assert func_mock.call_count == 3, func_mock.mock_calls[2:]
    # Should not call func_mock
    quib.get_value_valid_at_path(PathBuilder(quib)[0].path)
    assert func_mock.call_count == 3, func_mock.mock_calls[3:]


def test_vectorize_get_value_valid_at_path_none():
    quib = np.vectorize(lambda x: x)(iquib([1, 2, 3]))

    value = quib.get_value_valid_at_path(None)

    assert len(value) == 3


def test_vectorize_with_pass_quibs():
    @functools.partial(np.vectorize, pass_quibs=True)
    def vectorized(x):
        return iquib(x.get_value() + 1)

    result = vectorized(iquib(np.arange(2)))
    assert np.array_equal(result.get_value(), [1, 2])


def test_vectorize_with_pass_quibs_and_core_dims():
    @functools.partial(np.vectorize, pass_quibs=True, signature='(a)->(x)')
    def vectorized(x):
        return iquib(x.get_value() + 1)[:-1]

    result = vectorized(iquib(np.zeros((2, 3))))
    assert np.array_equal(result.get_value(), np.ones((2, 2)))


def test_lazy_vectorize():
    func_mock = mock.Mock(return_value=5)
    parent = iquib([0, 1, 2, 3])
    reference_to_vectorize = np.vectorize(func_mock, update_type="never")(parent)
    func_mock.assert_not_called()

    parent[0] = 100
    parent[1] = 101
    parent[2] = 102
    func_mock.assert_called_once()


def test_vectorize_doesnt_evaluate_sample_when_getting_value():
    func_mock = mock.Mock(return_value=5)
    parent = iquib([0, 1, 2])
    result = np.vectorize(func_mock, otypes=[np.int32])(parent)

    result[1].get_value()

    func_mock.assert_called_once_with(1)


def test_vectorize_with_unknown_shape_doesnt_evaluate_sample_when_getting_value():
    func_mock = mock.Mock(return_value=[4, 6])
    parent = iquib([0, 1, 2])
    result = np.vectorize(func_mock, signature='()->(n)', otypes=[np.int32])(parent)

    result[1].get_value()

    func_mock.assert_called_once_with(1)


def test_vectorize_with_data_with_zero_dims():
    data = iquib(np.array(np.zeros((3, 0, 2))))
    mock_func = mock.Mock()

    result = np.vectorize(mock_func, otypes=[np.int32])(data).get_value()

    assert np.array_equal(result, np.empty((3, 0, 2), dtype=np.int32))
    mock_func.assert_not_called()


@pytest.fixture
def temp_axes():
    ax = plt.gca()
    ax.clear()
    yield ax
    ax.clear()


@pytest.mark.parametrize('pass_quibs', [True, False])
def test_vectorize_does_not_redraw_valid_artists(temp_axes, pass_quibs):
    parent = iquib([[1, 2], [3, 4]])
    vectorized_plot = np.vectorize(plt.plot, signature='(x)->()', otypes=[np.object], pass_quibs=pass_quibs,
                                   evaluate_now=True)
    boy = vectorized_plot(parent)

    assert len(temp_axes.lines) == 2
    ids = list(map(id, temp_axes.lines))

    parent[0] = [5, 6]

    assert len(temp_axes.lines) == 2
    assert id(temp_axes.lines[0]) != ids[0]
    assert id(temp_axes.lines[1]) == ids[1]


@pytest.mark.parametrize('data', [[], [[]]])
# The tests without quibs are for sanity
@pytest.mark.parametrize('use_quib', [True, False])
def test_vectorize_with_empty_data_and_no_otypes(data, use_quib):
    data = iquib(data) if use_quib else data
    vectorized = np.vectorize(lambda x: x, evaluate_now=True)
    with pytest.raises(ValueError) as exc_info:
        vectorized(data)

    assert exc_info.value.args[0] == 'cannot call `vectorize` on size 0 inputs unless `otypes` is set'


def test_vectorize_array_and_scalar(uncached_array_quib, uncached_scalar_quib):
    a = uncached_array_quib
    b = uncached_scalar_quib
    v_add = np.vectorize(np.add)
    c = v_add(a, b)

    assert np.array_equal(c.get_value(), v_add(a.get_value(), b.get_value()))


def test_vectorize_array_and_scalar_with_invalidation(uncached_array_quib, uncached_scalar_quib):
    a = uncached_array_quib
    b = uncached_scalar_quib
    v_add = np.vectorize(np.add)
    c = v_add(a, b)
    a[0] = 2

    assert np.array_equal(c.get_value(), v_add(a.get_value(), b.get_value()))


# TODO: Move to appropriate place
def test_assignment_to_quib_within_vectorize_is_translated_to_override_on_vectorize():
    parent = iquib(0)

    @functools.partial(np.vectorize, pass_quibs=True, excluded={0}, otypes=[object])
    def get_override_group_for_assignment_to_child(quib):
        child = quib + iquib(1)
        child.allow_overriding = True
        return get_override_group_for_change(AssignmentToQuib(child, Assignment(2, [])))

    override_group = get_override_group_for_assignment_to_child(parent).get_value()[()]

    assert override_group.quib_changes == [Override(parent, Assignment(1, []))]

import numpy as np
import pytest

from pyquibbler import iquib
from tests.functional.quib.test_quib.get_value.test_apply_along_axis import parametrize_indices_to_invalidate, \
    parametrize_data, parametrize_path_to_invalidate
from tests.functional.quib.test_quib.invalidation.utils import check_invalidation


@parametrize_indices_to_invalidate
@parametrize_data
@pytest.mark.parametrize('excluded', [{0}, set(), None])
@pytest.mark.parametrize('func', [lambda x: np.sum(x), lambda x: (np.sum(x), np.sum(x))])
def test_vectorize_invalidation(indices_to_invalidate, data, excluded, func):
    kwargs = {}
    if excluded is not None:
        kwargs['excluded'] = excluded

    check_invalidation(np.vectorize(func, **kwargs), data, indices_to_invalidate)


@parametrize_path_to_invalidate
@parametrize_data
@pytest.mark.parametrize('excluded', [{0}, set(), None])
@pytest.mark.parametrize('func', [lambda x: np.sum(x), lambda x: (np.sum(x), np.sum(x))])
def test_vectorize_invalidation_with_list_arg(path_to_invalidate, data, excluded, func):
    data = data.tolist()
    kwargs = {}
    if excluded is not None:
        kwargs['excluded'] = excluded

    check_invalidation(np.vectorize(func, **kwargs), data, path_to_invalidate)


def test_vectorize_invalidation_with_non_numpy_return_value():
    vec = np.vectorize(lambda a: int(np.sum(a)), signature='(a)->()')
    check_invalidation(lambda quib: vec(quib), [1, 2, 3], [0])


@parametrize_indices_to_invalidate
@parametrize_data
def test_vectorize_invalidation_with_multiple_params(data, indices_to_invalidate):
    quib_arg = iquib(np.arange(12).reshape((3, 4)))
    non_quib_arg = np.arange(8).reshape((2, 1, 4))
    quib_kwarg = iquib(3)
    non_quib_kwarg = np.arange(3).reshape((3, 1))

    vec = np.vectorize(lambda a, b, c, d, e=0: a + b + c + d + e)
    check_invalidation(lambda quib: vec(quib, quib_arg, non_quib_arg, d=quib_kwarg, e=non_quib_kwarg),
                       data, indices_to_invalidate)


@pytest.mark.parametrize('excluded', [{1}, {'b'}, set(), None])
def test_vectorize_invalidation_with_quib_as_kwarg(excluded):
    kwargs = {}
    if excluded is not None:
        kwargs['excluded'] = excluded
    vec = np.vectorize(lambda a, b: a + b)
    check_invalidation(lambda quib: vec(5, b=quib), [1, 2, 3], [0])


@parametrize_indices_to_invalidate
@parametrize_data
def test_vectorize_invalidation_with_different_core_dims(data, indices_to_invalidate):
    data2 = np.arange(100, 122).reshape(1, 22)
    func = lambda a, b: (np.array([np.sum(a) + np.sum(b)] * 4), np.sum(a) + np.sum(b))
    vec = np.vectorize(func, signature='(a,b),(c)->(d),()')
    check_invalidation(lambda quib: vec(quib, data2), data, indices_to_invalidate)

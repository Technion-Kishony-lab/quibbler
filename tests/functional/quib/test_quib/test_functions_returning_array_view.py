import pytest

import numpy as np
from pyquibbler import iquib, quiby, CacheStatus


@pytest.mark.regression
def test_assignment_into_array_view():
    a = iquib(np.array([0, 0]))
    b = np.ravel(a).setp(cache_mode='on')
    b.get_value()

    a[0] = 7
    assert a.args[0][0] == 0, "sanity"

    b.get_value()
    assert a.args[0][0] == 0


@pytest.mark.regression
def test_view_should_be_able_to_cache():
    @quiby(create_quib=True)
    def get_a_view():
        # this simulates functions like np.genfromtxt which returns a view
        # of an internal array they create
        # when this bug exists we get very slow dragging in `quibdemo_fit_stock`
        return np.ravel(np.array([1, 2, 3]))

    view_quib = get_a_view()
    view_quib.cache_mode = 'on'
    view_quib.get_value()

    assert view_quib.cache_status == CacheStatus.ALL_VALID

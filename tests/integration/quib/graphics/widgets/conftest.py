import gc

import pytest
from matplotlib.widgets import AxesWidget

from pyquibbler.refactor.utilities.performance_utils import track_instances_of_class, \
    get_all_instances_in_tracked_class, TRACKED_CLASSES_TO_WEAKREFS


@pytest.fixture()
def get_only_live_widget(get_live_widgets):
    def _get():
        live = get_live_widgets()
        assert len(live) == 1
        return live[0]

    return _get


@pytest.fixture()
def get_live_widgets():
    track_instances_of_class(AxesWidget)

    def _get():
        gc.collect()
        return list(get_all_instances_in_tracked_class(AxesWidget))

    yield _get

    TRACKED_CLASSES_TO_WEAKREFS[AxesWidget] = set()

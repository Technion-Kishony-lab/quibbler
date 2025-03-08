import pytest
from matplotlib.widgets import AxesWidget

from pyquibbler.debug_utils.track_instances import track_instances_of_class


@pytest.fixture()
def get_only_live_widget(live_widgets):
    def _get():
        assert len(live_widgets) == 1
        return list(live_widgets)[0]

    return _get


@pytest.fixture()
def live_widgets():
    with track_instances_of_class(AxesWidget, False) as tracker:
        yield tracker

import contextlib
from dataclasses import dataclass, field
from typing import List, Set, Dict

from matplotlib.artist import Artist
from matplotlib.widgets import AxesWidget

from pyquibbler.graphics.update_new_artists import update_new_artists_from_previous_artists
from pyquibbler.graphics.global_collecting import ArtistsCollector, AxesWidgetsCollector, AxesCreationPreventor, \
    ColorCyclerIndexCollector
from pyquibbler.graphics.utils import get_artist_array, \
    get_axeses_to_array_names_to_starting_indices_and_artists, remove_artist,\
    get_axeses_to_array_names_to_artists
from pyquibbler.utilities.settable_cycle import SettableColorCycle


@dataclass
class GraphicsCollection:
    widgets: List[AxesWidget] = field(default_factory=list)
    artists: List[Artist] = field(default_factory=list)
    color_cyclers_to_index: Dict[SettableColorCycle, int] = field(default_factory=dict)

    def _get_artists_still_in_axes(self):
        """
        Remove any artists that we created that were removed by another means other than us (for example, cla())
        """
        return [artist for artist in self.artists if artist in get_artist_array(artist)]

    def remove_artists(self):
        for artist in self.artists:
            remove_artist(artist)
        self.artists = []

    def _handle_new_artists(self,
                            previous_axeses_to_array_names_to_indices_and_artists,
                            new_artists: Set[Artist],
                            should_copy_artist_attributes: bool):
        """
        Handle new artists and update graphics collection appropriately
        """
        self.artists = list(new_artists)
        current_axeses_to_array_names_to_artists = get_axeses_to_array_names_to_artists(new_artists)
        update_new_artists_from_previous_artists(previous_axeses_to_array_names_to_indices_and_artists,
                                                 current_axeses_to_array_names_to_artists,
                                                 should_copy_artist_attributes)

    def _handle_new_widgets(self, new_widgets: List[AxesWidget]):
        """
        Handle new widgets and update the graphics collection appropriately
        """
        from .widget_utils import destroy_widgets, transfer_data_from_new_widgets_to_previous_widgets
        if len(self.widgets) > 0:
            destroy_widgets(new_widgets)
            transfer_data_from_new_widgets_to_previous_widgets(previous_widgets=self.widgets,
                                                               new_widgets=new_widgets)
        else:
            self.widgets = new_widgets

    def _handle_called_color_cyclers(self, color_cyclers_to_index: Dict[SettableColorCycle, int]):
        """
        Handle color_cyclers that were used during the function call
        """
        self.color_cyclers_to_index = color_cyclers_to_index

    def set_color_cyclers_back_to_pre_run_index(self):
        for color_cycler, index in self.color_cyclers_to_index.items():
            color_cycler.current_index = index

    @contextlib.contextmanager
    def track_and_handle_new_graphics(self):
        self.artists = self._get_artists_still_in_axes()

        # Get the *current* artists together with their starting indices (per axes per artists array) so we can
        # place the new artists we create in their correct locations
        previous_axeses_to_array_names_to_indices_and_artists = \
            get_axeses_to_array_names_to_starting_indices_and_artists(self.artists)
        self.remove_artists()

        with ArtistsCollector() as artists_collector, \
                AxesWidgetsCollector() as widgets_collector, \
                ColorCyclerIndexCollector() as color_cycler_index_collector, \
                AxesCreationPreventor():
            yield

        self._handle_new_widgets(new_widgets=widgets_collector.objects_collected)

        self._handle_new_artists(previous_axeses_to_array_names_to_indices_and_artists,
                                 new_artists=artists_collector.objects_collected,
                                 should_copy_artist_attributes=len(widgets_collector.objects_collected) == 0)

        self._handle_called_color_cyclers(color_cycler_index_collector.color_cyclers_to_index)

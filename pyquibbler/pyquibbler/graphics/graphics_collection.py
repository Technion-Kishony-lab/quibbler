import contextlib
from dataclasses import dataclass, field
from typing import List, Dict

from matplotlib.artist import Artist
from matplotlib.widgets import AxesWidget

from pyquibbler.utilities.settable_cycle import SettableColorCycle

from .update_new_artists import update_new_artists_from_previous_artists, \
    add_new_axesless_patches_to_axes, copy_attributes_from_new_to_previous_artists
from .global_collecting import ArtistsCollector, AxesWidgetsCollector, AxesCreationPreventor, \
    ColorCyclerIndexCollector
from .utils import get_axeses_to_starting_indices, get_axeses_to_artists, remove_artists


@dataclass
class GraphicsCollection:
    widgets: List[AxesWidget] = field(default_factory=list)
    artists: List[Artist] = field(default_factory=list)
    color_cyclers_to_index: Dict[SettableColorCycle, int] = field(default_factory=dict)

    def _get_artists_still_in_axes(self):
        """
        Remove any artists that we created that were removed by another means other than us (for example, cla())
        """
        res = [artist for artist in self.artists if artist.axes is not None and artist in artist.axes._children]
        return res

    def remove_artists(self):
        remove_artists(self.artists)
        self.artists = []

    def _handle_new_artists(self,
                            previous_artists: List[Artist],
                            new_artists: List[Artist],
                            should_keep_previous_artists: bool):
        """
        Handle new artists and update graphics collection appropriately
        """

        if should_keep_previous_artists:
            copy_attributes_from_new_to_previous_artists(previous_artists, new_artists)
            remove_artists(new_artists)
        else:
            # Get the starting indices of the previous artists (per axes), so that we can
            # place the new artists in the correct drawing layer
            previous_axeses_to_starting_indices = get_axeses_to_starting_indices(previous_artists)

            current_axeses_to_artists = get_axeses_to_artists(new_artists)
            add_new_axesless_patches_to_axes(previous_artists, new_artists)
            self.remove_artists()
            self.artists = new_artists

            update_new_artists_from_previous_artists(previous_axeses_to_starting_indices,
                                                     current_axeses_to_artists)

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
        with ArtistsCollector() as artists_collector, \
                AxesWidgetsCollector() as widgets_collector, \
                ColorCyclerIndexCollector() as color_cycler_index_collector, \
                AxesCreationPreventor():
            yield

        should_keep_previous_artists = len(widgets_collector.objects_collected) > 0 and len(self.widgets) > 0

        self._handle_new_widgets(new_widgets=widgets_collector.objects_collected)

        self._handle_new_artists(previous_artists=self._get_artists_still_in_axes(),
                                 new_artists=artists_collector.objects_collected,
                                 should_keep_previous_artists=should_keep_previous_artists)

        self._handle_called_color_cyclers(color_cycler_index_collector.color_cyclers_to_index)

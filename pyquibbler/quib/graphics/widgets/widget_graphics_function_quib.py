from typing import Type
from matplotlib.widgets import Widget

from pyquibbler.quib import GraphicsFunctionQuib


class WidgetGraphicsFunctionQuib(GraphicsFunctionQuib):

    WIDGET_CLS: Type[Widget]

    def get_axeses(self):
        return {self.get_args_values()['ax']}

    def _copy_attributes(self, new_artists, previous_artists):
        # For widgets we don't want to copy an attributes as the widget can change colors of artists
        pass

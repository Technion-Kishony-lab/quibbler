from typing import Type
from matplotlib.widgets import Widget

from pyquibbler.quib import GraphicsFunctionQuib


class WidgetGraphicsFunctionQuib(GraphicsFunctionQuib):

    def get_axeses(self):
        return {self._get_args_values()['ax']}

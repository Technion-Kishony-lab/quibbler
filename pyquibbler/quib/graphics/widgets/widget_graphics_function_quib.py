from typing import Type
from matplotlib.widgets import Widget

from pyquibbler.quib import GraphicsFunctionQuib


class WidgetGraphicsFunctionQuib(GraphicsFunctionQuib):

    WIDGET_CLS: Type[Widget]

    def get_axeses(self):
        return {self.get_args_values()['ax']}

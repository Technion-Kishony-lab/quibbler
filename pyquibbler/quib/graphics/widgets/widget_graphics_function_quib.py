from typing import Type, Optional, Callable
from matplotlib.widgets import Widget

from pyquibbler.quib import GraphicsFunctionQuib


class WidgetGraphicsFunctionQuib(GraphicsFunctionQuib):
    WIDGET_CLS: Type[Widget]
    REPLACEMENT_CLS: Optional[Type[Widget]] = None

    @classmethod
    def create_wrapper(cls, func: Callable):
        assert func.__wrapped__ is cls.WIDGET_CLS
        return super().create_wrapper(cls.REPLACEMENT_CLS if cls.REPLACEMENT_CLS is not None else func)

    def get_axeses(self):
        return {self._get_all_args_dict()['ax']}

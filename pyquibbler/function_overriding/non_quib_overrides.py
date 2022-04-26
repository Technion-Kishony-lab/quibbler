import functools
from typing import Callable, Type

import matplotlib.widgets

from pyquibbler.graphics.utils import TYPES_TO_ARTIST_ARRAY_NAMES
from pyquibbler.graphics.widgets import QRadioButtons, QSlider, QRectangleSelector
from pyquibbler.quib.graphics.artist_wrapper import QuibblerArtistWrapper

widget_class_names_to_quib_supporting_widget = {
    'RadioButtons': QRadioButtons,
    'Slider': QSlider,
    'RectangleSelector': QRectangleSelector
}


def switch_widgets_to_quib_supporting_widgets():
    for widget_class_name, quib_supporting_widget in widget_class_names_to_quib_supporting_widget.items():
        setattr(matplotlib.widgets, widget_class_name, quib_supporting_widget)


def get_clear_axes_wrapper(func: Callable):

    @functools.wraps(func)
    def _wrapper(self, *args, **kwargs):
        QuibblerArtistWrapper(self).clear_all_quibs()
        for array_name in TYPES_TO_ARTIST_ARRAY_NAMES.values():
            if hasattr(self, array_name):
                for artist in getattr(self, array_name):
                    QuibblerArtistWrapper(artist).clear_all_quibs()
        return func(self, *args, **kwargs)

    return _wrapper


def wrap_method(cls: Type, method_name: str, get_wrapper: Callable):
    func = getattr(cls, method_name)
    setattr(cls, method_name, get_wrapper(func))


def override_clear_axes():
    from matplotlib.axis import Axis
    wrap_method(Axis, 'clear', get_clear_axes_wrapper)

    from matplotlib.axes._base import _AxesBase
    wrap_method(_AxesBase, 'cla', get_clear_axes_wrapper)

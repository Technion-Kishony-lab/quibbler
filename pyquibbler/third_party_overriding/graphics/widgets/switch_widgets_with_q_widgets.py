import functools

from typing import Callable

import matplotlib.widgets

from pyquibbler.graphics import global_collecting
from pyquibbler.graphics.widgets import QSlider
from pyquibbler.graphics.widgets import QRadioButtons


widget_class_names_to_quib_supporting_widget = {
    'RadioButtons': QRadioButtons,
    'Slider': QSlider,
}


def switch_widgets_to_quib_supporting_widgets():
    for widget_class_name, quib_supporting_widget in widget_class_names_to_quib_supporting_widget.items():
        setattr(matplotlib.widgets, widget_class_name, quib_supporting_widget)

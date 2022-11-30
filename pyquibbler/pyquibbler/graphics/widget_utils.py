from dataclasses import dataclass
from typing import List

from matplotlib.widgets import AxesWidget, Button

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.graphics.widgets import QRangeSlider, QSlider


ATTRIBUTES_TO_TRANSFER_PER_WIDGET = {
    Button: {"hovercolor"},
    QSlider: {'val'},
    QRangeSlider: {'val'}
}


class DifferentNumberOfWidgetsException(PyQuibblerException):

    def __str__(self):
        return "You cannot have a graphics function create a different number of widgets"


@dataclass
class WidgetsDontMatchException(PyQuibblerException):
    previous_widget: AxesWidget
    new_widget: AxesWidget

    def __str__(self):
        return f"{self.previous_widget} does not match {self.new_widget} in type"


def update_previous_widget_from_new_widget(previous_widget, new_widget):
    if type(previous_widget) is not type(new_widget):
        raise WidgetsDontMatchException(previous_widget=previous_widget, new_widget=new_widget)

    attributes = ATTRIBUTES_TO_TRANSFER_PER_WIDGET.get(type(previous_widget), set())
    for attr in attributes:
        setattr(previous_widget, attr, getattr(new_widget, attr))


def transfer_data_from_new_widgets_to_previous_widgets(previous_widgets: List[AxesWidget],
                                                       new_widgets: List[AxesWidget]):
    if len(previous_widgets) != len(new_widgets):
        raise DifferentNumberOfWidgetsException()

    for previous_widget, new_widget in zip(previous_widgets, new_widgets):
        update_previous_widget_from_new_widget(previous_widget, new_widget)


def destroy_widgets(widgets: List[AxesWidget]):
    for widget in widgets:
        widget.disconnect_events()

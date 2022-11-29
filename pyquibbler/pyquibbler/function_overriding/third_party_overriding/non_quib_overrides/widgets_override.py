import matplotlib.widgets

from pyquibbler.graphics.widgets import QRadioButtons, QSlider, QRangeSlider, \
    QRectangleSelector, QTextBox

widget_class_names_to_quib_supporting_widget = {
    'RadioButtons': QRadioButtons,
    'Slider': QSlider,
    'RangeSlider': QRangeSlider,
    'RectangleSelector': QRectangleSelector,
    'TextBox': QTextBox,
}


def switch_widgets_to_quib_supporting_widgets():
    for widget_class_name, quib_supporting_widget in widget_class_names_to_quib_supporting_widget.items():
        setattr(matplotlib.widgets, widget_class_name, quib_supporting_widget)

import functools
from dataclasses import dataclass

import matplotlib.widgets
from typing import Callable

from pyquibbler.refactor.function_overriding.third_party_overriding.graphics.graphics_overriding import GraphicsOverride
from pyquibbler.refactor.graphics import global_collecting
from pyquibbler.refactor.path import PathComponent
from pyquibbler.refactor.function_definitions.func_call import ArgsValues


# # TODO: MOVE ALL TO FUNCTION RUNNERS
#
# def on_change_radio_buttons(widget, args_values, new_value):
#     from pyquibbler.refactor.quib.quib import Quib
#     active = args_values.get('active')
#     if isinstance(active, Quib):
#         active.assign_value(args_values.get('labels').index(new_value))
#
#
# def on_change_slider(widget, args_values, new_value):
#     from pyquibbler.refactor.quib.quib import Quib
#     val = args_values.get('valinit')
#     if isinstance(val, Quib):
#         val.assign_value(new_value)
#
#
# def on_change_checkbuttons(widget, args_values, new_value):
#     from pyquibbler import Assignment
#     from pyquibbler.refactor.quib.quib import Quib
#     actives = args_values.get('actives')
#     if isinstance(actives, Quib):
#         buttons_checked = widget.get_status()
#         labels = args_values.get('labels')
#         new_value_index = labels.index(new_value)
#         actives.assign(Assignment(value=buttons_checked[new_value_index],
#                                   path=[PathComponent(indexed_cls=list, component=new_value_index)]))
#
#
# def set_change_slider(res, callback):
#     res.on_changed(callback)
#     res.on_release = callback
#

def widget_override(func, on_change=None, set_on_change=None):
    from pyquibbler.refactor.function_definitions.function_definition import create_function_definition
    from pyquibbler.refactor.quib.function_running.function_runners.known_graphics.widgets.radio_buttons_runner import \
        RadioButtonsRunner

    return GraphicsOverride("RadioButtons", module_or_cls=matplotlib.widgets,
                                    function_definition=create_function_definition(
                                        function_runner_cls=RadioButtonsRunner
                                    )
                                    )


def create_widget_overrides():
    return [
        widget_override(matplotlib.widgets.RadioButtons),
        # widget_override(matplotlib.widgets.Slider,
        #                 on_change=on_change_slider,
        #                 set_on_change=set_change_slider),
        # widget_override(matplotlib.widgets.CheckButtons),
    ]

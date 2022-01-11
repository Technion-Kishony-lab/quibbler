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

def widget_override(func_name, runner):
    from pyquibbler.refactor.function_definitions.function_definition import create_function_definition

    return GraphicsOverride(func_name, module_or_cls=matplotlib.widgets,
                                    function_definition=create_function_definition(
                                        function_runner_cls=runner
                                    )
                                    )


def create_widget_overrides():
    from pyquibbler.refactor.quib.function_running.function_runners import RadioButtonsRunner, SliderRunner
    return [
        widget_override("RadioButtons", RadioButtonsRunner),
        widget_override("Slider", SliderRunner),
        # widget_override(matplotlib.widgets.CheckButtons),
    ]

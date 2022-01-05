import functools
from dataclasses import dataclass

import matplotlib.widgets
from typing import Callable

from pyquibbler.refactor.function_overriding.third_party_overriding.graphics.graphics_overriding import GraphicsOverride
from pyquibbler.refactor.graphics import global_collecting
from pyquibbler.refactor.path import PathComponent
from pyquibbler.refactor.function_definitions.func_call import ArgsValues


def on_change_radio_buttons(widget, args_values, new_value):
    from pyquibbler.refactor.quib.quib import Quib
    active = args_values.get('active')
    if isinstance(active, Quib):
        active.assign_value(args_values.get('labels').index(new_value))


def on_change_slider(widget, args_values, new_value):
    from pyquibbler.refactor.quib.quib import Quib
    val = args_values.get('valinit')
    if isinstance(val, Quib):
        val.assign_value(new_value)


def on_change_checkbuttons(widget, args_values, new_value):
    from pyquibbler import Assignment
    from pyquibbler.refactor.quib.quib import Quib
    actives = args_values.get('actives')
    if isinstance(actives, Quib):
        buttons_checked = widget.get_status()
        labels = args_values.get('labels')
        new_value_index = labels.index(new_value)
        actives.assign(Assignment(value=buttons_checked[new_value_index],
                                  path=[PathComponent(indexed_cls=list, component=new_value_index)]))


def set_change_slider(res, callback):
    res.on_changed(callback)
    res.on_release = callback


@dataclass
class WidgetOverride(GraphicsOverride):

    on_change: Callable = None
    set_on_change: Callable = None

    def create_run_and_add_quib_supporting_callback(self, original_func: Callable):
        from pyquibbler.refactor.quib.utils import call_func_with_quib_values

        def _run(*args, **kwargs):
            with global_collecting.overridden_graphics_function():
                args_values = ArgsValues.from_function_call(func=original_func,
                                              args=args,
                                              kwargs=kwargs,
                                              include_defaults=False)
                widget = call_func_with_quib_values(original_func, args, kwargs)
                if self.on_change and self.set_on_change:
                    self.set_on_change(widget, functools.partial(self.on_change, widget, args_values))
                return widget

        return _run

    def override(self):
        setattr(self.module_or_cls, self.func_name,
                self.create_run_and_add_quib_supporting_callback(self.original_func))
        return super(WidgetOverride, self).override()


def widget_override(func, on_change=None, set_on_change=None):
    return WidgetOverride.from_func(func, module_or_cls=matplotlib.widgets,
                                              on_change=on_change,
                                              set_on_change=set_on_change,
                                              quib_creation_flags=dict(
                                                  call_func_with_quibs=True
                                              ))


def create_widget_overrides():
    return [
        widget_override(matplotlib.widgets.RadioButtons,
                        on_change=on_change_radio_buttons,
                        set_on_change=lambda res, callback: res.on_clicked(callback)),
        widget_override(matplotlib.widgets.Slider,
                        on_change=on_change_slider,
                        set_on_change=set_change_slider),
        widget_override(matplotlib.widgets.CheckButtons,
                        on_change=on_change_checkbuttons,
                        set_on_change=lambda res, callback: res.on_clicked(callback)),
    ]

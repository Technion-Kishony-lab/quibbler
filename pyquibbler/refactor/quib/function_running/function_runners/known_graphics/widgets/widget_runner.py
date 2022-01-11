from abc import abstractmethod

from pyquibbler.refactor.path import Path
from pyquibbler.refactor.quib.function_running import FunctionRunner

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


class WidgetRunner(FunctionRunner):

    @abstractmethod
    def on_change(self, widget):
        self.func_call.args_values

    def set_callback(self):
        pass


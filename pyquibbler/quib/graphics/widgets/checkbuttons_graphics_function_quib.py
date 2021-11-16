from typing import Optional, List, Any
from matplotlib.widgets import CheckButtons

from pyquibbler.quib import Quib
from pyquibbler.quib.assignment import Assignment, PathComponent
from pyquibbler.quib.utils import quib_method
from .single_on_change import set_func_callback_on_widget_one_time

from .widget_graphics_function_quib import WidgetGraphicsFunctionQuib


class CheckButtonsGraphicsFunctionQuib(WidgetGraphicsFunctionQuib):
    """
    A quib representing a matplotlib.widgets.CheckButtons. Will automatically add a listener and update the relevant
    quib
    """
    WIDGET_CLS = CheckButtons

    def _on_change(self, new_value: str):
        actives = self.get_args_values().get('actives')
        if isinstance(actives, Quib):
            widget = self.get_value()
            buttons_checked = widget.get_status()
            labels = self.get_args_values().get('labels')
            new_value_index = labels.index(new_value)
            actives.assign(Assignment(value=buttons_checked[new_value_index],
                                      path=[PathComponent(indexed_cls=list, component=new_value_index)]))
        else:
            # We only need to invalidate children if we didn't assign
            self.invalidate_and_redraw_at_path()

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        checkbuttons = super()._call_func(None)
        set_func_callback_on_widget_one_time(
            widget=checkbuttons,
            event_name="clicked",
            func=self._on_change,
            set_method_callback=checkbuttons.on_clicked
        )
        return checkbuttons

    @property
    @quib_method
    def get_status(self):
        return self.get_value().get_status()

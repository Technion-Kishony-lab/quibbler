from pyquibbler.quib import GraphicsFunctionQuib, Quib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.utils import quib_method


class CheckButtonsGraphicsFunctionQuib(GraphicsFunctionQuib):
    """
    A quib representing a matplotlib.widgets.CheckButtons. Will automatically add a listener and update the relevant quib
    """

    def _on_change(self, new_value: str):
        actives = self._kwargs.get('actives')
        if isinstance(actives, Quib):
            widget = self.get_value()
            buttons_checked = widget.get_status()
            labels = self._kwargs.get('labels')
            new_value_index = labels.index(new_value)
            actives.assign(Assignment(value=buttons_checked[new_value_index], paths=[new_value_index]))
        self.invalidate_and_redraw()

    def _call_func(self):
        checkbuttons = super(CheckButtonsGraphicsFunctionQuib, self)._call_func()
        checkbuttons.on_clicked(self._on_change)
        return checkbuttons

    def get_axeses(self):
        return {self.kwargs['ax']}

    @property
    @quib_method
    def get_status(self):
        return self.get_value().get_status()

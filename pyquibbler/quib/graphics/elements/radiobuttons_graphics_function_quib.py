from pyquibbler.quib import GraphicsFunctionQuib, Quib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.utils import quib_method


class RadioButtonsGraphicsFunctionQuib(GraphicsFunctionQuib):
    """
    A quib representing a matplotlib.widgets.RadioButtons. Will automatically add a listener and update the relevant quib
    """

    def _on_change(self, new_value: str):
        valindex = self._kwargs.get('active')
        if isinstance(valindex, Quib):
            labels = self._kwargs.get('labels')
            new_value_index = labels.index(new_value)
            valindex.assign(Assignment(value=new_value_index, path=[PathComponent(component=...,
                                                                                  indexed_cls=valindex.get_type())]))
        self.invalidate_and_redraw_at_path(path=[PathComponent(
            component=...,
            indexed_cls=self.value_selected.get_type()
        )])
        return valindex

    def _call_func(self):
        radiobuttons = super(RadioButtonsGraphicsFunctionQuib, self)._call_func()
        radiobuttons.on_clicked(self._on_change)
        return radiobuttons

    def get_axeses(self):
        return {self.kwargs['ax']}

    @property
    @quib_method
    def value_selected(self):
        return self.get_value().value_selected

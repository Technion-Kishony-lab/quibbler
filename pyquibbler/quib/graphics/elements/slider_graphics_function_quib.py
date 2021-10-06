from pyquibbler.quib import GraphicsFunctionQuib, Quib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.graphics import global_collecting


class SliderGraphicsFunctionQuib(GraphicsFunctionQuib):
    """
    A quib representing a slider. Will automatically add a listener and update the relevant quib
    """

    def _on_change(self, new_value: float):
        val = self._kwargs['valinit']
        if isinstance(val, Quib):
            val.assign(Assignment(value=new_value, paths=[...]))
        return val

    def _call_func(self):
        slider = super(SliderGraphicsFunctionQuib, self)._call_func()
        slider.on_changed(self._on_change)
        return slider

    def get_axeses(self):
        return {self.kwargs['ax']}

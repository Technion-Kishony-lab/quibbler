import functools

from pyquibbler.refactor.path import Path
from pyquibbler.refactor.quib.function_running import FunctionRunner


def _on_clicked(*args, **kwargs):
    pass


class RadioButtonsRunner(FunctionRunner):

    def _on_clicked(self, new_value):
        from pyquibbler.refactor.quib import Quib
        active = self.func_call.args_values.get('active')
        if isinstance(active, Quib):
            active.assign_value(self.func_call.args_values.get('labels').index(new_value))

    def _run_on_path(self, valid_path: Path):
        widget = super(RadioButtonsRunner, self)._run_on_path(valid_path)
        widget.on_clicked(self._on_clicked)
        return widget

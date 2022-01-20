from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.path import Path
from pyquibbler.translation.types import Source
from pyquibbler.translation.utils import copy_and_replace_sources_with_vals


class SourceFuncCall(FuncCall):

    SOURCE_OBJECT_TYPE = Source

    def run(self):
        """
        Calls a function with the specified args and kwargs while replacing quibs with their values.
        """
        new_args = (tuple(copy_and_replace_sources_with_vals(arg) for arg in self.args))
        new_kwargs = {name: copy_and_replace_sources_with_vals(val) for name, val in self.kwargs.items()}
        return self.func(*new_args, **new_kwargs)
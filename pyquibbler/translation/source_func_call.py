from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.path import Path


class SourceFuncCall(FuncCall):

    def get_value_valid_at_path(self, path: Path):
        raise NotImplementedError()

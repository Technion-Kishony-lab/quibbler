import matplotlib.image

from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.function_overriding.function_override import FuncOverride


def create_file_loading_overrides():
    return [FuncOverride(
        module_or_cls=matplotlib.image,
        func_name='imread',
        function_definition=create_func_definition(
            is_file_loading_func=True
        )
    )]

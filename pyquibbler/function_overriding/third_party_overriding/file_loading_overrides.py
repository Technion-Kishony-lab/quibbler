import matplotlib.image

from pyquibbler.function_definitions.function_definition import create_function_definition
from pyquibbler.function_overriding.function_override import FunctionOverride


def create_file_loading_overrides():
    return [FunctionOverride(
        module_or_cls=matplotlib.image,
        func_name='imread',
        function_definition=create_function_definition(
            is_file_loading_func=True
        )
    )]

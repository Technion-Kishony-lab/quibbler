from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.translation.types import Source


class SourceFuncCall(FuncCall):
    """
    A funccall with `Source` objects for any sources in the arguments
    """

    SOURCE_OBJECT_TYPE = Source

    def run(self):
        """
        Calls a function with the specified args and kwargs while replacing quibs with their values.
        """

        def _replace_source_with_value(source: Source):
            return source.value

        new_args, new_kwargs = self.transform_sources_in_args_kwargs(_replace_source_with_value,
                                                                     _replace_source_with_value)
        return self.func(*new_args, **new_kwargs)

from typing import Type, List, Optional

from pyquibbler.utilities.multiple_instance_runner import MultipleInstanceRunner, RunCondition
from pyquibbler.function_definitions.func_definition import FuncDefinition

from .translators import TypeTranslator
from .run_conditions import TypeTranslateRunCondition


class MultipleTypeTranslatorRunner(MultipleInstanceRunner):

    def __init__(self,
                 run_condition: TypeTranslateRunCondition,
                 func_definition: FuncDefinition,
                 data_arguments_types: Optional[List[Type]] = None):
        super().__init__(run_condition)
        self._func_definition = func_definition
        self._data_arguments_types = data_arguments_types

    def _get_all_runners(self) -> List[Type[TypeTranslator]]:
        return self._func_definition.result_type_or_type_translators

    def _get_exception_message(self):
        return self._func_definition.func

    def _run_runner(self, runner: Type[TypeTranslator]):
        translator = runner(
            func_definition=self._func_definition,
            data_arguments_types=self._data_arguments_types,
        )
        return translator.get_type()


def translate_type(
        run_condition: TypeTranslateRunCondition,
        func_definition: FuncDefinition,
        data_arguments_types: Optional[List[Type]] = None) -> Optional[Type]:
    """
    Try getting the type of the quib value without evaluating the function.
    Return None if type cannot be calculated.
    """
    return MultipleTypeTranslatorRunner(
        run_condition=run_condition,
        func_definition=func_definition,
        data_arguments_types=data_arguments_types,
                                       ).run()

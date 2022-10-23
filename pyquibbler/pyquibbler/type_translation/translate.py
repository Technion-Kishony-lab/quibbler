from typing import Type, List, Optional

from pyquibbler.utilities.multiple_instance_runner import MultipleInstanceRunner
from pyquibbler.function_definitions.func_definition import FuncDefinition

from .run_conditions import TypeTranslateRunCondition


def translate_type(
        run_condition: TypeTranslateRunCondition,
        func_definition: FuncDefinition,
        data_arguments_types: Optional[List[Type]] = None) -> Optional[Type]:
    """
    Try getting the type of the quib value without evaluating the function.
    Return None if type cannot be calculated.
    """
    return MultipleInstanceRunner(run_condition=run_condition,
                                  runner_types=func_definition.result_type_or_type_translators,
                                  func_definition=func_definition, data_arguments_types=data_arguments_types).run()

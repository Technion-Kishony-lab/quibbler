from dataclasses import dataclass

from pyquibbler.function_definitions.func_definition import FuncDefinition


@dataclass
class AttributeOverride:
    attribute: str
    func_definition: FuncDefinition


class MethodOverride(AttributeOverride):
    pass

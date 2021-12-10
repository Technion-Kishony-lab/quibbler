import operator
from dataclasses import dataclass
from operator import getitem

from typing import Callable, Set, List

from pyquibbler.overriding.definitions import OverrideDefinition
from pyquibbler.overriding.types import IndexArgument
from pyquibbler.quib.refactor.quib import Quib


@dataclass
class OperatorOverrideDefinition(OverrideDefinition):

    override_reverse_operator: bool = False

    def _get_wrapped_func(self):
        return getattr(operator, self.func_name)

    def override(self):
        super(OperatorOverrideDefinition, self).override()
        if self.override_reverse_operator:
            reverse_func = self._create_func_to_maybe_create_quib(
                lambda quib, other: self._get_wrapped_func()(other, quib)
            )
            rname = '__r' + self.func_name[2:]
            setattr(self.module_or_cls, rname, reverse_func)


def arithmetic_operator_definition(name, data_source_indexes: List = None, override_reverse_operator: bool = True):
    data_source_indexes = data_source_indexes or [0, 1]
    return OperatorOverrideDefinition(
        func_name=name,
        data_source_arguments={IndexArgument(i) for i in (data_source_indexes or [])},
        module_or_cls=Quib,
        override_reverse_operator=override_reverse_operator
    )


ARITHMETIC_OPERATORS_DEFINITIONS = [
    arithmetic_operator_definition('__add__'),
    arithmetic_operator_definition('__sub__'),
    arithmetic_operator_definition('__mul__'),
    arithmetic_operator_definition('__matmul__', [], override_reverse_operator=False),
    arithmetic_operator_definition('__truediv__'),
    arithmetic_operator_definition('__floordiv__'),
    arithmetic_operator_definition('__mod__'),
    arithmetic_operator_definition('__pow__'),
    arithmetic_operator_definition('__lshift__'),
    arithmetic_operator_definition('__rshift__'),
    arithmetic_operator_definition('__and__'),
    arithmetic_operator_definition('__xor__'),
    arithmetic_operator_definition('__or__'),
]

# operator_override('__add__', ElementWiseFunctionQuib),
# operator_override('__sub__', ElementWiseFunctionQuib),
# operator_override('__mul__', ElementWiseFunctionQuib),
# operator_override('__matmul__'),
# operator_override('__truediv__', ElementWiseFunctionQuib),
# operator_override('__floordiv__'),
# operator_override('__mod__', ElementWiseFunctionQuib),
# (DefaultFunctionQuib, '__divmod__', divmod),
# operator_override('__pow__', ElementWiseFunctionQuib),
# operator_override('__lshift__'),
# operator_override('__rshift__'),
# operator_override('__and__', ElementWiseFunctionQuib),
# operator_override('__xor__', ElementWiseFunctionQuib),
# operator_override('__or__', ElementWiseFunctionQuib),

OPERATOR_DEFINITIONS = [*ARITHMETIC_OPERATORS_DEFINITIONS]

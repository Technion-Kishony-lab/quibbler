from pyquibbler.function_overriding.operators.helpers import with_reverse_operator_overrides, operator_override, \
    with_reverse_elementwise_operator_overrides, elementwise_operator_override
from pyquibbler.function_overriding.third_party_overriding.numpy.helpers import get_inverter_for_func
from pyquibbler.function_overriding.third_party_overriding.numpy.overrides import create_numpy_overrides
from pyquibbler.inversion.inverters.getitem_inverter import GetItemInverter
from pyquibbler.translation.translators import BackwardsGetItemTranslator
from pyquibbler.translation.translators.transpositional.getitem_translator import ForwardsGetItemTranslator


def create_operator_overrides():
    # We need to create elementwise overrides to make sure we have inverters for our elementwise operators
    create_numpy_overrides()

    return [
        *with_reverse_elementwise_operator_overrides('__add__', [0, 1], [get_inverter_for_func('add')]),
        *with_reverse_elementwise_operator_overrides('__sub__', [0, 1], [get_inverter_for_func('subtract')]),
        *with_reverse_elementwise_operator_overrides('__mul__', [0, 1], [get_inverter_for_func('multiply')]),
        operator_override('__matmul__', []),
        *with_reverse_elementwise_operator_overrides('__truediv__', [0, 1], [get_inverter_for_func('divide')]),
        *with_reverse_operator_overrides('__floordiv__'),
        *with_reverse_operator_overrides('__mod__'),
        *with_reverse_elementwise_operator_overrides('__pow__', [0, 1], [get_inverter_for_func('power')]),
        *with_reverse_operator_overrides('__lshift__'),
        *with_reverse_operator_overrides('__rshift__'),
        *with_reverse_operator_overrides('__and__'),
        *with_reverse_operator_overrides('__xor__'),
        *with_reverse_operator_overrides('__or__'),

        operator_override('__neg__'),
        operator_override('__pos__'),
        operator_override('__abs__'),
        operator_override('__invert__'),

        elementwise_operator_override('__lt__'),
        elementwise_operator_override('__gt__'),
        elementwise_operator_override('__ge__'),

        operator_override('__round__', [0]),
        operator_override('__trunc__', [0]),
        operator_override('__floor__', [0]),
        operator_override('__ceil__', [0]),

        operator_override('__getitem__', [0], inverters=[GetItemInverter],
                          backwards_path_translators=[BackwardsGetItemTranslator],
                          forwards_path_translators=[ForwardsGetItemTranslator]
        )
    ]

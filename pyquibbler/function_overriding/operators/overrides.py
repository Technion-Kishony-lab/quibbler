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

        # Binary operators with reverse
        *(with_reverse_elementwise_operator_overrides(
            operator_name, [0, 1], inverters=get_inverter_for_func(inverter_from))[is_rev] \
          for is_rev in [0, 1] \
          for operator_name, inverter_from in (
            ('__add__',         'add'),
            ('__sub__',         'subtract'),
            ('__mul__',         'multiply'),
            ('__truediv__',     'true_divide'),
            ('__floordiv__',    'floor_divide'),
            ('__mod__',         'mod'),
            ('__pow__',         'power'),
            ('__lshift__',      'left_shift'),
            ('__rshift__',      'right_shift'),
            ('__and__',         'logical_and'),
            ('__xor__',         'logical_xor'),
            ('__or__',          'logical_or'),
          )),

        # Binary operators without reverse:
        *(elementwise_operator_override(
            operator_name, [0, 1], inverters=get_inverter_for_func(inverter_from))
          for operator_name, inverter_from in (
              ('__ne__',        'not_equal'),
              ('__lt__',        'less'),
              ('__gt__',        'greater'),
              ('__ge__',        'greater_equal'),
              ('__le__',         'less_equal'),
          )),

        operator_override('__matmul__', []),

        # Unary operators
        operator_override('__neg__'),
        operator_override('__pos__'),
        operator_override('__abs__'),
        operator_override('__invert__'),

        # Rounding operators
        operator_override('__round__', [0]),
        operator_override('__trunc__', [0]),
        operator_override('__floor__', [0]),
        operator_override('__ceil__', [0]),

        # Get item
        operator_override(
            '__getitem__', [0], inverters=[GetItemInverter],
            backwards_path_translators=[BackwardsGetItemTranslator],
            forwards_path_translators=[ForwardsGetItemTranslator]
        )
    ]

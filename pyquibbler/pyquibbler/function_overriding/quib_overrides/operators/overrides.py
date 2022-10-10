# flake8: noqa

from pyquibbler.function_overriding.quib_overrides.operators.helpers import operator_override, \
    binary_elementwise_operator_override, unary_elementwise_operator_override
from pyquibbler.function_overriding.third_party_overriding.numpy.helpers import get_inverse_funcs_for_func
from pyquibbler.function_overriding.third_party_overriding.numpy.overrides import create_numpy_overrides
from pyquibbler.inversion.inverters.getitem_inverter import GetItemInverter
from pyquibbler.translation.translators import BackwardsGetItemTranslator
from pyquibbler.translation.translators.getitem_translator import ForwardsGetItemTranslator


def create_operator_overrides():
    # We need to create elementwise overrides to make sure we have inverters for our elementwise operators
    create_numpy_overrides()

    return [

        # Binary operators with reverse
        *(binary_elementwise_operator_override(operator_name,
                                               inverse_funcs=get_inverse_funcs_for_func(inverter_from),
                                               is_reverse=is_rev)
          for is_rev in [False, True]
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
        *(binary_elementwise_operator_override(operator_name,
                                               inverse_funcs=get_inverse_funcs_for_func(inverter_from))
          for operator_name, inverter_from in (
              ('__ne__',        'not_equal'),
              ('__lt__',        'less'),
              ('__gt__',        'greater'),
              ('__ge__',        'greater_equal'),
              ('__le__',        'less_equal'),
          )),

        operator_override('__matmul__', []),

        # Unary operators
        *(unary_elementwise_operator_override(operator_name,
                                              inverse_funcs=get_inverse_funcs_for_func(inverter_from))
          for operator_name, inverter_from in (

            # arithmetics:
            ('__neg__',         'negative'),
            ('__pos__',         'positive'),
            ('__abs__',         'abs'),
            ('__invert__',      'invert'),

            # Rounding operators
            ('__round__',       'round'),
            ('__trunc__',       'trunc'),
            ('__floor__',       'floor'),
            ('__ceil__',        'ceil'),
        )),

        # Get item
        operator_override(
            '__getitem__', [0], inverters=[GetItemInverter],
            backwards_path_translators=[BackwardsGetItemTranslator],
            forwards_path_translators=[ForwardsGetItemTranslator]
        )
    ]

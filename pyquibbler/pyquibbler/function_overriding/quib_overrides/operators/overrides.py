# flake8: noqa

from pyquibbler.function_overriding.quib_overrides.operators.helpers import operator_override, \
    binary_operator_override, unary_operator_override
from pyquibbler.function_overriding.third_party_overriding.numpy.helpers import \
    get_unary_inverse_funcs_for_func, get_binary_inverse_funcs_for_func
from pyquibbler.function_overriding.third_party_overriding.numpy.overrides import create_numpy_overrides
from pyquibbler.inversion.inverters.getitem import GetItemInverter
from pyquibbler.path_translation.translators.transpositional import \
    TranspositionalBackwardsPathTranslator, TranspositionalForwardsPathTranslator
from pyquibbler.path_translation.translators.getitem import \
    GetItemBackwardsPathTranslator, GetItemForwardsPathTranslator


def create_operator_overrides():
    # We need to create elementwise overrides to make sure we have inverters for our elementwise operators
    create_numpy_overrides()

    return [

        # Binary operators with reverse, numeric operators
        *(binary_operator_override(operator_name, inverse_funcs=get_binary_inverse_funcs_for_func(inverter_from),
                                   is_reverse=is_rev, for_list=for_list)
          for is_rev in [False, True]
          for operator_name, inverter_from, for_list in (
            ('__add__',         'add',           True),  # translators for list addition will also be added
            ('__sub__',         'subtract',      False),
            ('__mul__',         'multiply',      True),  # translators for list multiplication will also be added
            ('__truediv__',     'true_divide',   False),
            ('__floordiv__',    'floor_divide',  False),
            ('__mod__',         'mod',           False),
            ('__pow__',         'power',         False),
            ('__lshift__',      'left_shift',    False),
            ('__rshift__',      'right_shift',   False),
            ('__and__',         'logical_and',   False),
            ('__xor__',         'logical_xor',   False),
            ('__or__',          'logical_or',    False),
          )),

        # Binary operators without reverse:
        *(binary_operator_override(operator_name, inverse_funcs=get_binary_inverse_funcs_for_func(inverter_from))
          for operator_name, inverter_from in (
              ('__ne__',        'not_equal'),
              ('__lt__',        'less'),
              ('__gt__',        'greater'),
              ('__ge__',        'greater_equal'),
              ('__le__',        'less_equal'),
          )),

        operator_override('__matmul__', []),

        # Unary operators
        *(unary_operator_override(operator_name,
                                  inverse_func=get_unary_inverse_funcs_for_func(inverter_from))
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
            backwards_path_translators=[GetItemBackwardsPathTranslator, TranspositionalBackwardsPathTranslator],
            forwards_path_translators=[GetItemForwardsPathTranslator, TranspositionalForwardsPathTranslator]
        )
    ]

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
        # Note that binary_operator_override has a special exception within for __add__ and __mul__
        *(binary_operator_override(operator_name, inverse_funcs=get_binary_inverse_funcs_for_func(inverter_from),
                                   is_reverse=is_rev)
          for is_rev in [False, True]
          for operator_name, inverter_from in (
            ('__add__',         'add'),         # translators for list addition will also be added
            ('__sub__',         'subtract'),
            ('__mul__',         'multiply'),    # translators for list multiplication will also be added
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

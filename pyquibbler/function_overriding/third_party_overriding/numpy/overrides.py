import math

import numpy as np
from numpy import pi

from pyquibbler.function_overriding.third_party_overriding.numpy.helpers import numpy_override, transpositional, \
    elementwise, single_arg_elementwise, many_to_one_elementwise, reduction, accumulation
from pyquibbler.function_overriding.third_party_overriding.numpy.vectorize_overrides import create_vectorize_overrides
from pyquibbler.quib.func_calling.func_calls.apply_along_axis_call import ApplyAlongAxisQuibFuncCall
from pyquibbler.translation.translators.apply_along_axis_translator import ApplyAlongAxisForwardsTranslator
from pyquibbler.translation.translators.elementwise.generic_inverse_functions import \
    create_inverse_func_from_indexes_to_funcs


def identity(x):
    return x


def create_numpy_overrides():

    return [
        # NUMPY

        # Reduction
        reduction('amin'), reduction('max'), reduction('amax'), reduction('min'),  # min/max
        reduction('argmin'), reduction('argmax'), reduction('nanargmin'), reduction('nanargmax'),  # arg-min/max
        reduction('sum'), reduction('prod'), reduction('nanprod'), reduction('nansum'),  # sum/prod
        reduction('any'), reduction('all'),  # logical
        reduction('average'), reduction('mean'), reduction('var'), reduction('std'), reduction('median'),  # statistics
        reduction('diff'), reduction('sort'),  # other

        # Accumulation
        accumulation('cumsum'), accumulation('cumprod'), accumulation('cumproduct'), accumulation('nancumsum'),
        accumulation('nancumprod'),

        # Elementwise
        elementwise('around', [0]),
        elementwise('ceil', [0]),
        elementwise('round', [0]),
        elementwise('rint', [0]),
        elementwise('add', [0, 1], create_inverse_func_from_indexes_to_funcs(
            {
                0: np.subtract,
                1: np.subtract
            }
        )),
        elementwise('subtract', [0, 1], create_inverse_func_from_indexes_to_funcs({
            0: np.add,
            1: lambda result, other: np.subtract(other, result)
        })),
        elementwise('divide', [0, 1], create_inverse_func_from_indexes_to_funcs(
            {
                0: np.multiply,
                1: lambda result, other: np.divide(other, result)
            }
        )),
        elementwise('multiply', [0, 1], create_inverse_func_from_indexes_to_funcs({
            0: np.divide,
            1: np.divide
        })),
        elementwise('power', [0, 1], create_inverse_func_from_indexes_to_funcs({
            0: lambda x, n: x ** (1 / n),
            1: lambda result, other: math.log(result, other)
        })),
        single_arg_elementwise('sqrt', np.square),
        single_arg_elementwise('arcsin', np.sin),
        single_arg_elementwise('arccos', np.cos),
        single_arg_elementwise('arctan', np.tan),
        single_arg_elementwise('arcsinh', np.sinh),
        single_arg_elementwise('arccosh', np.cosh),
        single_arg_elementwise('arctanh', np.tanh),
        single_arg_elementwise('ceil', identity),
        single_arg_elementwise('floor', identity),
        single_arg_elementwise('round', identity),
        single_arg_elementwise('exp', np.log),
        single_arg_elementwise('exp2', np.log2),
        single_arg_elementwise('expm1', np.log1p),
        single_arg_elementwise('log', np.exp),
        single_arg_elementwise('log2', np.exp2),
        single_arg_elementwise('log1p', np.expm1),
        single_arg_elementwise('log10', lambda x: 10 ** x),
        single_arg_elementwise('int', identity),
        single_arg_elementwise('float', identity),

        many_to_one_elementwise('sin', ((np.arcsin, 2 * pi), (lambda x: -np.arcsin(x) + np.pi, 2 * pi))),
        many_to_one_elementwise('cos', ((np.arccos, 2 * pi), (lambda x: -np.arccos(x), 2 * pi))),
        many_to_one_elementwise('tan', ((np.arctan, pi),)),
        many_to_one_elementwise('sinh', ((np.arcsinh, None),)),
        many_to_one_elementwise('cosh', ((np.arccosh, None), (lambda x: -np.arccosh(x), None))),
        many_to_one_elementwise('tanh', ((np.arctanh, None),)),
        many_to_one_elementwise('square', ((np.sqrt, None), (lambda x: -np.sqrt(x), None))),
        many_to_one_elementwise('abs', ((identity, None), (lambda x: -x, None))),

        # Transpositional
        transpositional("rot90", [0]), transpositional("concatenate", [0]), transpositional("repeat", [0]),
        transpositional("full", ['fill_value']), transpositional("reshape", [0]), transpositional("transpose", [0]),
        transpositional("array", [0]), transpositional("tile", [0]), transpositional("asarray", [0]),
        transpositional("squeeze", [0]), transpositional("expand_dims", [0]), transpositional("ravel", [0]),
        transpositional("squeeze", [0]),

        # Custom
        numpy_override('genfromtxt', is_file_loading_func=True),
        numpy_override('apply_along_axis', data_source_arguments=["arr"],
                       forwards_path_translators=[ApplyAlongAxisForwardsTranslator],
                       quib_function_call_cls=ApplyAlongAxisQuibFuncCall),
        *create_vectorize_overrides(),

        numpy_override('arange', []), numpy_override('polyfit', []), numpy_override('interp', []),
        numpy_override('linspace', []), numpy_override('polyval', []), numpy_override('corrcoef', []),

    ]

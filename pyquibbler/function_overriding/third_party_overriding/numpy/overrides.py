# flake8: noqa

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
        # Reduction
        *(reduction(func_name) for func_name in (
            # min/max:
            'amin',
            'max',
            'amax',
            'min',

            # arg-min/max:
            'argmin',
            'argmax',
            'nanargmin',
            'nanargmax',

            # sum/prod:
            'sum',
            'prod',
            'nanprod',
            'nansum',

            # logical:
            'any',
            'all',

            # statistics:
            'average',
            'mean',
            'var',
            'std',
            'median',

            # other:
            'diff',
            'sort',
        )),

        # Accumulation
        *(accumulation(func_name) for func_name in (
            'cumsum',
            'cumprod',
            'cumproduct',
            'nancumsum',
            'nancumprod',
        )),

        # Binary
        *(elementwise(func_name, [0, 1], create_inverse_func_from_indexes_to_funcs({0: invs[0], 1: invs[1]}))
          for func_name, invs in (
              ('add',       (np.subtract, np.subtract)),
              ('subtract',  (np.add, lambda result, other: np.subtract(other, result))),
              ('divide',    (np.multiply, lambda result, other: np.divide(other, result))),
              ('multiply',  (np.divide, np.divide)),
              ('power',     (lambda x, n: x ** (1 / n), lambda result, other: math.log(result, other))),
          )),

        # Single argument
        *(single_arg_elementwise(func_name, inverse_func) for func_name, inverse_func in (
            ('sqrt',    np.square),
            ('arcsin',  np.sin),
            ('arccos',  np.cos),
            ('arctan',  np.tan),
            ('arcsinh', np.sinh),
            ('arccosh', np.cosh),
            ('arctanh', np.tanh),
            ('ceil',    identity),
            ('floor',   identity),
            ('round',   identity),
            ('exp',     np.log),
            ('exp2',    np.log2),
            ('expm1',   np.log1p),
            ('log',     np.exp),
            ('log2',    np.exp2),
            ('log1p',   np.expm1),
            ('log10',   (lambda x: 10 ** x)),
            ('int',     identity),
            ('float',   identity),
            ('around',  identity),
            ('ceil',    identity),
            ('round',   identity),
            ('rint',    identity),
        )),

        # Periodic
        *(many_to_one_elementwise(func_name, params) for func_name, params in (
            ('sin',     ((np.arcsin,  2 * pi), (lambda x: -np.arcsin(x) + np.pi, 2 * pi))),
            ('cos',     ((np.arccos,  2 * pi), (lambda x: -np.arccos(x), 2 * pi))),
            ('tan',     ((np.arctan,  pi),)),
            ('sinh',    ((np.arcsinh, None),)),
            ('cosh',    ((np.arccosh, None),   (lambda x: -np.arccosh(x), None))),
            ('tanh',    ((np.arctanh, None),)),
            ('square',  ((np.sqrt,    None),   (lambda x: -np.sqrt(x), None))),
            ('abs',     ((identity,   None),   (lambda x: -x, None))),
        )),

        # Transpositional
        *(transpositional(func_name, data_sources) for func_name, data_sources in (
            ("rot90",       [0]),
            ("concatenate", [0]),
            ("repeat",      [0]),
            ("full",        ['fill_value']),
            ("reshape",     [0]),
            ("transpose",   [0]),
            ("array",       [0]),
            ("tile",        [0]),
            ("asarray",     [0]),
            ("squeeze",     [0]),
            ("expand_dims", [0]),
            ("ravel",       [0]),
            ("squeeze",     [0]),
        )),

        # Data-less
        *(numpy_override(func_name, []) for func_name in (
            'arange',
            'polyfit',
            'interp',
            'linspace',
            'polyval',
            'corrcoef'
        )),

        # Custom
        numpy_override('genfromtxt', is_file_loading_func=True),
        numpy_override('apply_along_axis', data_source_arguments=["arr"],
                       forwards_path_translators=[ApplyAlongAxisForwardsTranslator],
                       quib_function_call_cls=ApplyAlongAxisQuibFuncCall),
        *create_vectorize_overrides(),
    ]

# flake8: noqa

import math

import numpy as np
from numpy import pi

from pyquibbler.function_overriding.third_party_overriding.numpy.helpers import numpy_override, \
    numpy_override_random, numpy_override_read_file, \
    numpy_override_transpositional, numpy_override_reduction, numpy_override_accumulation, \
    elementwise, single_arg_elementwise
from pyquibbler.function_overriding.third_party_overriding.numpy.vectorize_overrides import create_vectorize_overrides
from pyquibbler.quib.func_calling.func_calls.apply_along_axis_call import ApplyAlongAxisQuibFuncCall
from pyquibbler.translation.translators.apply_along_axis_translator import ApplyAlongAxisForwardsTranslator
from pyquibbler.translation.translators.elementwise.generic_inverse_functions import \
    create_inverse_func_from_indexes_to_funcs
from pyquibbler.function_overriding.third_party_overriding.numpy.inverse_functions import \
    inv_sin, inv_cos, inv_tan, keep_sign

def identity(x):
    return x


def create_numpy_overrides():

    return [
        # Reduction
        *(numpy_override_reduction(func_name)
          for func_name in (
            # min / max:
            'min',
            'max',
            'amin',
            'amax',

            # arg-min / max:
            'argmin',
            'argmax',
            'nanargmin',
            'nanargmax',

            # sum / prod:
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
        *(numpy_override_accumulation(func_name)
          for func_name in (
            'cumsum',
            'cumprod',
            'cumproduct',
            'nancumsum',
            'nancumprod',
          )),

        # Binary
        *(elementwise(func_name, [0, 1], {0: invs[0], 1: invs[1]})
          for func_name, invs in (
            # Arithmetic
            ('add',           (np.subtract, np.subtract)),
            ('subtract',      (np.add, lambda result, other: np.subtract(other, result))),
            ('divide',        (np.multiply, lambda result, other: np.divide(other, result))),
            ('multiply',      (np.divide, np.divide)),
            ('power',         (lambda x, n: x ** (1 / n), lambda result, other: math.log(result, other))),
            ('true_divide',   (np.multiply, lambda result, other: np.divide(other, result))),

            # Integers
            ('left_shift',    (None, None)),  # TODO: write inverse
            ('right_shift',   (None, None)),  # TODO: write inverse
            ('floor_divide',  (None, None)),  # TODO: write inverse
            ('mod',           (None, None)),  # TODO: write inverse

            ('hypot',         (None, None)),  # TODO: write inverse
            ('float_power',   (None, None)),  # TODO: write inverse
            ('fmod',          (None, None)),  # TODO: write inverse
            ('remainder',     (None, None)),  # TODO: write inverse
            ('lcm',           (None, None)),
            ('gcd',           (None, None)),
            #('divmod',        (None, None)),  # TODO: return tuple, needs attention

            # min / max
            ('fmin',          (None, None)),  # TODO: write inverse
            ('fmax',          (None, None)),  # TODO: write inverse

            # logical
            ('logical_and',   (None, None)),  # TODO: write inverse
            ('logical_or',    (None, None)),  # TODO: write inverse
            ('logical_xor',   (None, None)),  # TODO: write inverse

            # comparison
            ('equal',         (None, None)),
            ('not_equal',     (None, None)),
            ('greater',       (None, None)),
            ('greater_equal', (None, None)),
            ('less',          (None, None)),
            ('less_equal',    (None, None)),
          )),

        # Single argument
        *(single_arg_elementwise(func_name, inverse_func)
          for func_name, inverse_func in (
            # square, sqrt
            ('sqrt',        np.square),
            ('square',      (np.sqrt, keep_sign(np.sqrt))),

            # trigonometric / inverse-trigonometric
            ('sin',         (np.arcsin,  inv_sin)),
            ('cos',         (np.arccos,  inv_cos)),
            ('tan',         (np.arctan,  inv_tan)),
            ('arcsin',      np.sin),
            ('arccos',      np.cos),
            ('arctan',      np.tan),

            # angles
            ('degrees',     np.radians),
            ('radians',     np.degrees),
            ('deg2rad',     np.rad2deg),
            ('rad2deg',     np.deg2rad),

            # complex numbers
            ('abs',         (identity, keep_sign(identity))),
            ('real',        (lambda new_y: new_y,      lambda new_y, x: np.imag(x) + new_y     )),
            ('imag',        (lambda new_y: new_y * 1j, lambda new_y, x: np.real(x) + new_y * 1j)),
            ('absolute',    (identity, keep_sign(identity))),
            ('angle',       (lambda a: np.cos(a) + 1j * np.sin(a), lambda a, c: (np.cos(a) + 1j * np.sin(a)) * np.abs(c))),
            ('conj',        np.conj),
            ('conjugate',   np.conjugate),
            ('sign',        lambda sgn, val: sgn * val),

            # hyperbolic / inverse-hyperbolic
            ('arcsinh',     np.sinh),
            ('arccosh',     np.cosh),
            ('arctanh',     np.tanh),
            ('sinh',        np.arcsinh),
            ('cosh',        (np.arccosh, keep_sign(np.arccosh))),
            ('tanh',        np.arctanh),

            # arithmetics
            ('reciprocal',  None),
            ('positive',    identity),
            ('negative',    np.negative),
            ('invert',      np.invert),
            ('modf',        None),

            # exponentials / logs
            ('exp',         np.log),
            ('exp2',        np.log2),
            ('expm1',       np.log1p),
            ('log',         np.exp),
            ('log2',        np.exp2),
            ('log1p',       np.expm1),
            ('log10',       lambda x: 10 ** x),

            # rounding
            ('ceil',        identity),
            ('floor',       identity),
            ('round',       identity),
            ('around',      identity),
            ('rint',        identity),
            ('fix',         identity),
            ('trunc',       identity),

            # casting
            #('int32',        identity),  # causes problems with specifying dtype=np.int32
            #('int64',        identity),  # causes problems with specifying dtype=np.int64
            #('int',         identity),  # DeprecationWarning: `np.int` is a deprecated alias for the builtin `int`.
            #('float',       identity),  # DeprecationWarning: `np.float` is a deprecated alias for the builtin `float`.

            # other
            ('i0',          None),
            ('sinc',        None),
          )),

        # Transpositional
        *(numpy_override_transpositional(func_name, data_sources)
          for func_name, data_sources in (
            ("rot90",       [0]),
            ("concatenate", [0]),
            ("repeat",      [0]),
            ("full",        ['fill_value']),
            ("reshape",     [0]),
            ("transpose",   [0]),
            ("array",       [0]),
            ("swapaxes",    [0]),
            ("tile",        [0]),
            ("asarray",     [0]),
            ("squeeze",     [0]),
            ("expand_dims", [0]),
            ("ravel",       [0]),
            ("squeeze",     [0]),
          )),

        # Shape-only, data-independent
        # TODO: need to implement correct translators
        *(numpy_override(func_name)
          for func_name in (
            'ones_like',
            'zeros_like',
            'shape',
          )),

        # Data-less
        *(numpy_override(func_name)
          for func_name in (
            'arange',
            'polyfit',
            'interp',
            'linspace',
            'polyval',
            'corrcoef',
            'array2string',
            'zeros',
            'ones',
            'eye',
            'identity',
          )),

        # Read from files
        *(numpy_override_read_file(func_name)
          for func_name in (
            'genfromtxt',
            'load',
            'loadtxt',
          )),

        # Random
        *(numpy_override_random(func_name)
          for func_name in (
            'rand',
            'randn',
            'randint'
          )),

        # Custom:
        # apply_along_axis
        numpy_override('apply_along_axis', data_source_arguments=["arr"],
                       forwards_path_translators=[ApplyAlongAxisForwardsTranslator],
                       quib_function_call_cls=ApplyAlongAxisQuibFuncCall),

        # vectorize
        *create_vectorize_overrides(),
    ]

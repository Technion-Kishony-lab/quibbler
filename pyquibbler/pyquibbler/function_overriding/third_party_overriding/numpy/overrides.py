# flake8: noqa

import math
import numpy as np

from pyquibbler.function_definitions.types import DataArgumentDesignation, PositionalArgument
from pyquibbler.quib.func_calling.func_calls.apply_along_axis_call import ApplyAlongAxisQuibFuncCall
from pyquibbler.path_translation.translators.apply_along_axis import ApplyAlongAxisForwardsPathTranslator
from .inverse_functions import inv_sin, inv_cos, inv_tan, keep_sign, inv_power
from .vectorize_overrides import create_vectorize_overrides
from .helpers import numpy_override, numpy_override_random, numpy_override_read_file, \
  numpy_override_transpositional_one_to_many, numpy_override_transpositional_one_to_one, \
  numpy_override_reduction, numpy_override_accumulation, numpy_override_axis_wise, \
  binary_elementwise, unary_elementwise, numpy_override_shape_only, numpy_array_override


def identity(x):
    return x


nd = np.ndarray


def create_numpy_overrides():

    return [
        # Axis-Reduction
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
          )),

        # Axis-Accumulation
        *(numpy_override_accumulation(func_name, result_type_or_type_translators=nd)
          for func_name in (
            'cumsum',
            'cumprod',
            'cumproduct',
            'nancumsum',
            'nancumprod',
          )),

        # Axis-wise (any function along an axis)
        *(numpy_override_axis_wise(func_name, result_type_or_type_translators=nd)
          for func_name in (
            'diff',  # TODO: need to write more specific translators that only invalidate/request neighbouring elements
            'sort',
          )),

        # Elementwise - Binary (two arguments)
        # For each function we provide a tuple specifying the RawInverseFunc for each of the two arguments.
        # namely, for y = func(x1, x2), we provide:
        # (new_x1 = inv_func1(new_y, x2), new_x2 = inv_func2(new_y, x1))
        #
        # Note: When inverting many-to-one functions (specifically, the power function with an even power),
        # an element of the tuple can itself be a tuple specifying the nominal and input-dependent inverse functions:
        #  (
        #   new_x1 = inv_func1_nominal(new_y, x2),
        #   new_x1 = inv_func1_based_on_previous_value(new_y, x2, previous_x1)
        #  )
        #
        *(binary_elementwise(func_name, raw_inverse_funcs)
          for func_name, raw_inverse_funcs in (
            # Arithmetic
            ('add',           (np.subtract, np.subtract)),
            ('subtract',      (np.add, lambda result, other: np.subtract(other, result))),
            ('divide',        (np.multiply, lambda result, other: np.divide(other, result))),
            ('multiply',      (np.divide, np.divide)),
            ('power',         ((lambda new_y, n: new_y ** (1 / n), inv_power), lambda result, other: math.log(result, other))),
            ('true_divide',   (np.multiply, lambda result, other: np.divide(other, result))),

            # trigonometric
            ('arctan2',       (lambda a, x: x * np.tan(a), lambda a, y: y / np.tan(a))),

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

        # Elementwise - Single argument
        # Note: When inverting many-to-one functions, we provide a tuple specifying
        # the nominal and input-dependent inverse functions:
        #  (
        #   new_x1 = inv_func1_nominal(new_y),
        #   new_x1 = inv_func1_based_on_previous_value(new_y, previous_x1)
        #  )
        #
        *(unary_elementwise(func_name, inverse_func)
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
            ('log10',       lambda new_y: 10 ** new_y),

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
        # np.array is special because we need to check for dtype=object
        *(numpy_array_override(func_name, data_source_arguments=data_sources, result_type_or_type_translators=nd)
            for func_name, data_sources in (
            ('array', [0]),
          )),

        # Other Transpositional
        *(numpy_override_transpositional_one_to_one(func_name,
                                                    data_source_arguments=data_sources,
                                                    result_type_or_type_translators=result_type)
          for func_name, data_sources, result_type in (
            ('rot90',       [0],  nd),
            ('reshape',     [0],  nd),
            ('transpose',   [0],  nd),
            ('swapaxes',    [0],  nd),
            ('asarray',     [0],  nd),
            ('squeeze',     [0],  nd),
            ('expand_dims', [0],  nd),
            ('ravel',       [0],  nd),
            ('diagonal',    [0],  nd),
            ('flip',        [0],  []),

            # np.concatenate has an argument that contains multiple data arguments:
            ('concatenate', [DataArgumentDesignation(PositionalArgument(0), is_multi_arg=True)], nd),
          )),

        *(numpy_override_transpositional_one_to_many(func_name,
                                                     data_source_arguments=data_sources,
                                                     result_type_or_type_translators=result_type)
          for func_name, data_sources, result_type in (
            ('repeat',      [0],  nd),
            ('full',        ['fill_value'], nd),
            ('tile',        [0],  nd),
            ('broadcast_to', [0], nd),
          )),

        # Shape-only, data-independent
        *(numpy_override_shape_only(func_name, result_type_or_type_translators=result_type)
          for func_name, result_type in (
            ('ones_like',    nd),
            ('zeros_like',   nd),
            ('shape',        tuple),
            ('size',         int),
            ('ndim',         int),
          )),

        # Data-less
        *(numpy_override(func_name, result_type_or_type_translators=result_type)
          for func_name, result_type in (
            ('arange',       nd),
            ('polyfit',      nd),
            ('interp',       nd),
            ('linspace',     nd),
            ('polyval',      nd),
            ('corrcoef',     nd),
            ('array2string', str),
            ('zeros',        nd),
            ('ones',         nd),
            ('eye',          nd),
            ('identity',     nd),
            ('ptp',          []),
            ('nonzero',   tuple),  # TODO: needs specifically tailored path translators
            ('trace',        []),  # TODO: needs specifically tailored path translators
          )),

        # Read from files
        *(numpy_override_read_file(func_name, result_type_or_type_translators=nd)
          for func_name in (
            'genfromtxt',
            'load',
            'loadtxt',
          )),

        # Random
        *(numpy_override_random(func_name, result_type_or_type_translators=nd)
          for func_name in (
            'rand',
            'randn',
            'randint'
          )),

        # apply_along_axis
        numpy_override('apply_along_axis',
                       data_source_arguments=["arr"],
                       result_type_or_type_translators=nd,
                       is_graphics=None,
                       allowed_kwarg_flags=('is_random', 'is_file_loading', 'is_graphics', 'pass_quibs', 'lazy'),
                       forwards_path_translators=[ApplyAlongAxisForwardsPathTranslator],
                       quib_function_call_cls=ApplyAlongAxisQuibFuncCall),

        # vectorize
        *create_vectorize_overrides(),
    ]

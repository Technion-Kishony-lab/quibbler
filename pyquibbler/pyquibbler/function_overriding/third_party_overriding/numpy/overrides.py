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


def _reduction(func_name):
    return numpy_override_reduction(func_name)


def _accumulation(func_name):
    return numpy_override_accumulation(func_name, result_type_or_type_translators=nd)


def _axiswise(func_name):
    return numpy_override_axis_wise(func_name, result_type_or_type_translators=nd)


def _array(func_name, data_sources, result_type):
    return numpy_array_override(func_name,
                                data_source_arguments=data_sources,
                                result_type_or_type_translators=result_type)


def _one2one(func_name, data_sources, result_type):
    return numpy_override_transpositional_one_to_one(func_name,
                                                     data_source_arguments=data_sources,
                                                     result_type_or_type_translators=result_type)


def _one2many(func_name, data_sources, result_type):
    return numpy_override_transpositional_one_to_many(func_name,
                                                      data_source_arguments=data_sources,
                                                      result_type_or_type_translators=result_type)


def _shapeonly(func_name, data_sources, result_type):
    return numpy_override_shape_only(func_name,
                                     data_source_arguments=data_sources,
                                     result_type_or_type_translators=result_type)


def _dataless(func_name, result_type):
    return numpy_override(func_name, result_type_or_type_translators=result_type)


def _fileloading(func_name):
    return numpy_override_read_file(func_name, result_type_or_type_translators=nd)


def _random(func_name):
    return numpy_override_random(func_name, result_type_or_type_translators=nd)


RAW_ENTRIES = [
    # min / max:
    ('min',         _reduction),
    ('max',         _reduction),
    ('amin',        _reduction),
    ('amax',        _reduction),

    # agr- min / max:
    ('argmin',      _reduction),
    ('argmax',      _reduction),
    ('nanargmin',   _reduction),
    ('nanargmax',   _reduction),

    # sum / prod
    ('sum',         _reduction),
    ('prod',        _reduction),
    ('nanprod',     _reduction),
    ('nansum',      _reduction),

    # logical
    ('any',         _reduction),
    ('all',         _reduction),

    # statistics
    ('average',     _reduction),
    ('mean',        _reduction),
    ('var',         _reduction),
    ('std',         _reduction),
    ('median',      _reduction),
    ('ptp',         _reduction),

    # cumulative
    ('cumsum',      _accumulation),
    ('cumprod',     _accumulation),
    ('cumproduct',  _accumulation),
    ('nancumsum',   _accumulation),
    ('nancumprod',  _accumulation),

    # axis-wise any function
    ('diff',        _axiswise),  # TODO: need to write more specific translators that only invalidate/request neighbouring elements
    ('sort',        _axiswise),

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

    # Arithmetic
    ('add',         binary_elementwise, (np.subtract, np.subtract)),
    ('subtract',    binary_elementwise, (np.add, lambda result, other: np.subtract(other, result))),
    ('divide',      binary_elementwise, (np.multiply, lambda result, other: np.divide(other, result))),
    ('multiply',    binary_elementwise, (np.divide, np.divide)),
    ('power',       binary_elementwise, ((lambda new_y, n: new_y ** (1 / n), inv_power), lambda result, other: math.log(result, other))),
    ('true_divide', binary_elementwise, (np.multiply, lambda result, other: np.divide(other, result))),

    # trigonometric
    ('arctan2',     binary_elementwise, (lambda a, x: x * np.tan(a), lambda a, y: y / np.tan(a))),

    # Integers
    ('left_shift',  binary_elementwise, (None, None)),  # TODO: write inverse
    ('right_shift', binary_elementwise, (None, None)),  # TODO: write inverse
    ('floor_divide',binary_elementwise, (None, None)),  # TODO: write inverse
    ('mod',         binary_elementwise, (None, None)),  # TODO: write inverse

    ('hypot',       binary_elementwise, (None, None)),  # TODO: write inverse
    ('float_power', binary_elementwise, (None, None)),  # TODO: write inverse
    ('fmod',        binary_elementwise, (None, None)),  # TODO: write inverse
    ('remainder',   binary_elementwise, (None, None)),  # TODO: write inverse
    ('lcm',         binary_elementwise, (None, None)),
    ('gcd',         binary_elementwise, (None, None)),
    # ('divmod',    binary_elementwise, (None, None)),  # TODO: return tuple, needs attention

    # min / max
    ('fmin',        binary_elementwise, (None, None)),  # TODO: write inverse
    ('fmax',        binary_elementwise, (None, None)),  # TODO: write inverse

    # logical
    ('logical_and', binary_elementwise, (None, None)),  # TODO: write inverse
    ('logical_or',  binary_elementwise, (None, None)),  # TODO: write inverse
    ('logical_xor', binary_elementwise, (None, None)),  # TODO: write inverse

    # comparison
    ('equal',       binary_elementwise, (None, None)),
    ('not_equal',   binary_elementwise, (None, None)),
    ('greater',     binary_elementwise, (None, None)),
    ('greater_equal', binary_elementwise, (None, None)),
    ('less',        binary_elementwise, (None, None)),
    ('less_equal',  binary_elementwise, (None, None)),

    # Elementwise - Single argument
    # Note: When inverting many-to-one functions, we provide a tuple specifying
    # the nominal and input-dependent inverse functions:
    #  (
    #   new_x1 = inv_func1_nominal(new_y),
    #   new_x1 = inv_func1_based_on_previous_value(new_y, previous_x1)
    #  )
    #
    # square, sqrt
    ('sqrt',        unary_elementwise, np.square),
    ('square',      unary_elementwise, (np.sqrt, keep_sign(np.sqrt))),

    # trigonometric / inverse-trigonometric
    ('sin',         unary_elementwise, (np.arcsin, inv_sin)),
    ('cos',         unary_elementwise, (np.arccos, inv_cos)),
    ('tan',         unary_elementwise, (np.arctan, inv_tan)),
    ('arcsin',      unary_elementwise, np.sin),
    ('arccos',      unary_elementwise, np.cos),
    ('arctan',      unary_elementwise, np.tan),

    # angles
    ('degrees',     unary_elementwise, np.radians),
    ('radians',     unary_elementwise, np.degrees),
    ('deg2rad',     unary_elementwise, np.rad2deg),
    ('rad2deg',     unary_elementwise, np.deg2rad),

    # complex numbers
    ('abs',         unary_elementwise, (identity, keep_sign(identity))),
    ('real',        unary_elementwise, (lambda new_y: new_y, lambda new_y, x: np.imag(x) + new_y)),
    ('imag',        unary_elementwise, (lambda new_y: new_y * 1j, lambda new_y, x: np.real(x) + new_y * 1j)),
    ('absolute',    unary_elementwise, (identity, keep_sign(identity))),
    ('angle',       unary_elementwise, (lambda a: np.cos(a) + 1j * np.sin(a), lambda a, c: (np.cos(a) + 1j * np.sin(a)) * np.abs(c))),
    ('conj',        unary_elementwise, np.conj),
    ('conjugate',   unary_elementwise, np.conjugate),
    ('sign',        unary_elementwise, lambda sgn, val: sgn * val),

    # hyperbolic / inverse-hyperbolic
    ('arcsinh',     unary_elementwise, np.sinh),
    ('arccosh',     unary_elementwise, np.cosh),
    ('arctanh',     unary_elementwise, np.tanh),
    ('sinh',        unary_elementwise, np.arcsinh),
    ('cosh',        unary_elementwise, (np.arccosh, keep_sign(np.arccosh))),
    ('tanh',        unary_elementwise, np.arctanh),

    # arithmetics
    ('reciprocal',  unary_elementwise, None),
    ('positive',    unary_elementwise, identity),
    ('negative',    unary_elementwise, np.negative),
    ('invert',      unary_elementwise, np.invert),
    ('modf',        unary_elementwise, None),

    # exponentials / logs
    ('exp',         unary_elementwise, np.log),
    ('exp2',        unary_elementwise, np.log2),
    ('expm1',       unary_elementwise, np.log1p),
    ('log',         unary_elementwise, np.exp),
    ('log2',        unary_elementwise, np.exp2),
    ('log1p',       unary_elementwise, np.expm1),
    ('log10',       unary_elementwise, lambda new_y: 10 ** new_y),

    # rounding
    ('ceil',        unary_elementwise, identity),
    ('floor',       unary_elementwise, identity),
    ('round',       unary_elementwise, identity),
    ('around',      unary_elementwise, identity),
    ('rint',        unary_elementwise, identity),
    ('fix',         unary_elementwise, identity),
    ('trunc',       unary_elementwise, identity),

    # casting
    # ('int32',     unary_elementwise, identity),  # causes problems with specifying dtype=np.int32
    # ('int64',     unary_elementwise, identity),  # causes problems with specifying dtype=np.int64
    # ('int',       unary_elementwise, identity),  # DeprecationWarning: `np.int` is a deprecated alias for the builtin `int`.
    # ('float',     unary_elementwise, identity),  # DeprecationWarning: `np.float` is a deprecated alias for the builtin `float`.

    # other
    ('i0', unary_elementwise, None),
    ('sinc', unary_elementwise, None),

    # Transpositional
    ('array',       _array,         [0],    nd),  # np.array is special because we need to check for dtype=object
    ('rot90',       _one2one,       [0],    nd),
    ('reshape',     _one2one,       [0],    nd),
    ('transpose',   _one2one,       [0],    nd),
    ('swapaxes',    _one2one,       [0],    nd),
    ('asarray',     _one2one,       [0],    nd),
    ('squeeze',     _one2one,       [0],    nd),
    ('expand_dims', _one2one,       [0],    nd),
    ('ravel',       _one2one,       [0],    nd),
    ('diagonal',    _one2one,       [0],    nd),
    ('flip',        _one2one,       [0],    []),
    ('concatenate', _one2one,       [DataArgumentDesignation(PositionalArgument(0), is_multi_arg=True)], nd),

    ('repeat',      _one2many,      [0],    nd),
    ('full',        _one2many,      [1],    nd),
    ('tile',        _one2many,      [0],    nd),
    ('broadcast_to',_one2many,      [0],    nd),

    ('ones_like',   _shapeonly,     [0],    nd),
    ('zeros_like',  _shapeonly,     [0],    nd),
    ('empty_like',  _shapeonly,     [0],    nd),
    ('full_like',   _one2many,      [1],    nd),
    ('shape',       _shapeonly,     [0],    tuple),
    ('size',        _shapeonly,     [0],    int),
    ('ndim',        _shapeonly,     [0],    int),

    ('arange',      _dataless,      nd),
    ('polyfit',     _dataless,      nd),
    ('interp',      _dataless,      nd),
    ('linspace',    _dataless,      nd),
    ('polyval',     _dataless,      nd),
    ('corrcoef',    _dataless,      nd),
    ('array2string',_dataless,      str),
    ('zeros',       _dataless,      nd),
    ('ones',        _dataless,      nd),
    ('eye',         _dataless,      nd),
    ('identity',    _dataless,      nd),
    ('nonzero',     _dataless,      tuple),  # TODO: needs specifically tailored path translators
    ('trace',       _dataless,      []),     # TODO: needs specifically tailored path translators

    ('genfromtxt',  _fileloading),
    ('load',        _fileloading),
    ('loadtxt',     _fileloading),

    ('rand',        _random),
    ('randn',       _random),
    ('randint',     _random),
    ]


def create_numpy_overrides():

    overrides = [entry[1](entry[0], *entry[2:]) for entry in RAW_ENTRIES]
    special_overrides = [

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

    return overrides + special_overrides

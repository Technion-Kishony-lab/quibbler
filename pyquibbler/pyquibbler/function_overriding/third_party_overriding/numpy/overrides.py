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

# Elementwise - Single argument
# Note: When inverting many-to-one functions, we provide a tuple specifying
# the nominal and input-dependent inverse functions:
#  (
#   new_x1 = inv_func1_nominal(new_y),
#   new_x1 = inv_func1_based_on_previous_value(new_y, previous_x1)
#  )
#

RAW_ENTRIES = [
    # Array creation routines
    # https://numpy.org/doc/stable/reference/routines.array-creation.html
    # -------------------------------------------------------------------
    ('empty',       _dataless,      nd),
    ('empty_like',  _shapeonly,     [0],    nd),
    ('eye',         _dataless,      nd),
    ('identity',    _dataless,      nd),
    ('ones',        _dataless,      nd),
    ('ones_like',   _shapeonly,     [0],    nd),
    ('zeros',       _dataless,      nd),
    ('zeros_like',  _shapeonly,     [0],    nd),
    ('full',        _one2many,      [1],    nd),
    ('full_like',   _one2many,      [1],    nd),
    ('array',       _array,         [0],    nd),  # np.array is special because we need to check for dtype=object
    # asarray
    # asanyarray
    # ascontiguousarray
    # asmatrix
    # copy
    # frombuffer
    # from_dlpack
    # fromfile
    # fromfunction
    # fromiter
    # fromstring
    # loadtxt [BELOW]
    # core.records.array
    # core.records.fromarrays
    # core.records.fromrecords
    # core.records.fromstring
    # core.records.fromfile
    # core.defchararray.array
    # core.defchararray.asarray
    ('arange',      _dataless,      nd),
    ('linspace',    _dataless,      nd),
    ('logspace',    _dataless,      nd),
    ('geomspace',   _dataless,      nd),
    ('meshgrid',    _dataless,      []),
    ('mgrid',       _dataless,      []),
    ('ogrid',       _dataless,      []),
    ('diag',        _one2one,       [0],    nd),
    ('diagflat',    _one2one,       [0],    nd),
    ('tri',         _dataless,      nd),
    ('tril',        unary_elementwise,  None),  # TODO: need a specialized inverter
    ('triu',        unary_elementwise,  None),  # TODO: need a specialized inverter
    ('vander',      _dataless,      nd),
    # mat
    # bmat

    # Array manipulation routines
    # https://numpy.org/doc/stable/reference/routines.array-manipulation.html
    # -----------------------------------------------------------------------
    # copyto
    ('shape',       _shapeonly,     [0],    tuple),
    ('reshape',     _one2one,       [0],    nd),
    ('ravel',       _one2one,       [0],    nd),
    # ndarray.flat
    # ndarray.flatten
    ('moveaxis',    _one2one,       [0],    nd),
    ('rollaxis',    _one2one,       [0],    nd),
    ('swapaxes',    _one2one,       [0],    nd),
    # ndarray.T
    ('transpose',   _one2one,       [0],    nd),
    ('atleast_1d',  _one2one,       [0],    nd),
    ('atleast_2d',  _one2one,       [0],    nd),
    ('atleast_3d',  _one2one,       [0],    nd),
    # broadcast
    ('broadcast_to',_one2many,      [0],    nd),
    # broadcast_arrays
    ('expand_dims', _one2one,       [0],    nd),
    ('squeeze',     _one2one,       [0],    nd),
    ('asarray',     _one2one,       [0],    nd),
    # asanyarray
    # asmatrix
    # asfarray
    # asfortranarray
    # ascontiguousarray
    # asarray_chkfinite
    # require
    ('concatenate', _one2one,       [DataArgumentDesignation(PositionalArgument(0), is_multi_arg=True)], nd),
    # stack
    # block
    # vstack
    # hstack
    # dstack
    # column_stack
    # row_stack
    # split
    # array_split
    # dsplit
    # hsplit
    # vsplit
    ('tile',        _one2many,      [0],    nd),
    ('repeat',      _one2many,      [0],    nd),
    # delete
    # insert
    # append
    # resize
    # trim_zeros
    # unique
    ('flip',        _one2one,       [0],    []),
    # fliplr
    # flipud
    # reshape
    # roll
    ('rot90',       _one2one,       [0],    nd),

    # Binary operations
    # https://numpy.org/doc/stable/reference/routines.bitwise.html
    # ------------------------------------------------------------
    # bitwise_and
    # bitwise_or
    # bitwise_xor
    ('invert',      unary_elementwise, np.invert),
    ('left_shift',  binary_elementwise, (None, None)),  # TODO: write inverse
    ('right_shift', binary_elementwise, (None, None)),  # TODO: write inverse
    # packbits
    # unpackbits
    # binary_repr

    # Datetime Support Functions
    # https://numpy.org/doc/stable/reference/routines.datetime.html
    # -------------------------------------------------------------
    # datetime_as_string
    # datetime_data
    # busdaycalendar
    # is_busday
    # busday_offset
    # busday_count

    # Data type routines
    # https://numpy.org/doc/stable/reference/routines.dtype.html
    # ----------------------------------------------------------
    # can_cast
    # promote_types
    # min_scalar_type
    # result_type
    # common_type
    # obj2sctype
    # dtype
    # format_parser
    # finfo
    # iinfo
    # issctype
    # issubdtype
    # issubsctype
    # issubclass_
    # find_common_type
    # typename
    # sctype2char
    # mintypecode
    # maximum_sctype

    # Discrete Fourier Transform ( numpy.fft )
    # https://numpy.org/doc/stable/reference/routines.fft.html
    # --------------------------------------------------------
    # fft.fft
    # fft.ifft
    # fft.fft2
    # fft.ifft2
    # fft.fftn
    # fft.ifftn
    # fft.rfft
    # fft.irfft
    # fft.rfft2
    # fft.irfft2
    # fft.rfftn
    # fft.irfftn
    # fft.hfft
    # fft.ihfft
    # fft.fftfreq
    # fft.rfftfreq
    # fft.fftshift
    # fft.ifftshift

    # Functional programming
    # https://numpy.org/doc/stable/reference/routines.functional.html
    # ---------------------------------------------------------------
    # apply_along_axis [DONE]
    # apply_over_axes
    # vectorize [DONE]
    # frompyfunc
    # piecewise

    # Input and output
    # https://numpy.org/doc/stable/reference/routines.io.html
    # -------------------------------------------------------
    ('load',        _fileloading),
    # save
    # savez
    # savez_compressed
    ('loadtxt',     _fileloading),
    # savetxt
    ('genfromtxt',  _fileloading),
    # fromregex
    # fromstring
    # ndarray.tofile
    # ndarray.tolist
    ('array2string',_dataless,      str),
    # array_repr
    # array_str
    # format_float_positional
    # format_float_scientific
    # memmap
    # lib.format.open_memmap
    # set_printoptions
    # get_printoptions
    # set_string_function
    # printoptions
    # binary_repr
    # base_repr
    # DataSource
    # lib.format

    # Linear algebra ( numpy.linalg )
    # https://numpy.org/doc/stable/reference/routines.linalg.html
    # -----------------------------------------------------------
    # dot
    # linalg.multi_dot
    # vdot
    # inner
    # outer
    # matmul
    # tensordot
    # einsum
    # einsum_path
    # linalg.matrix_power
    # kron
    # linalg.cholesky
    # linalg.qr
    # linalg.svd
    # linalg.eig
    # linalg.eigh
    # linalg.eigvals
    # linalg.eigvalsh
    # linalg.norm
    # linalg.cond
    # linalg.det
    # linalg.matrix_rank
    # linalg.slogdet
    ('trace',       _dataless,      []),     # TODO: needs specifically tailored path translators
    # linalg.solve
    # linalg.tensorsolve
    # linalg.lstsq
    # linalg.inv
    # linalg.pinv
    # linalg.tensorinv
    # linalg.LinAlgError

    # Logic functions
    # https://numpy.org/doc/stable/reference/routines.logic.html
    # ----------------------------------------------------------
    ('all',         _reduction),
    ('any',         _reduction),
    # isfinite
    # isinf
    # isnan
    # isnat
    # isneginf
    # isposinf
    # iscomplex
    # iscomplexobj
    # isfortran
    # isreal
    # isrealobj
    # isscalar
    ('logical_and', binary_elementwise, (None, None)),  # TODO: write inverse
    ('logical_or',  binary_elementwise, (None, None)),  # TODO: write inverse
    # logical_not
    ('logical_xor', binary_elementwise, (None, None)),  # TODO: write inverse
    # allclose
    # isclose
    # array_equal
    # array_equiv
    ('greater',     binary_elementwise, (None, None)),
    ('greater_equal', binary_elementwise, (None, None)),
    ('less',        binary_elementwise, (None, None)),
    ('less_equal',  binary_elementwise, (None, None)),
    ('equal',       binary_elementwise, (None, None)),
    ('not_equal',   binary_elementwise, (None, None)),

    # Mathematical functions
    # https://numpy.org/doc/stable/reference/routines.math.html
    # ---------------------------------------------------------
    # -- Trigonometric / inverse-trigonometric --
    ('sin',         unary_elementwise, (np.arcsin, inv_sin)),
    ('cos',         unary_elementwise, (np.arccos, inv_cos)),
    ('tan',         unary_elementwise, (np.arctan, inv_tan)),
    ('arcsin',      unary_elementwise, np.sin),
    ('arccos',      unary_elementwise, np.cos),
    ('arctan',      unary_elementwise, np.tan),
    # angles
    ('hypot',       binary_elementwise, (None, None)),  # TODO: write inverse
    ('arctan2',     binary_elementwise, (lambda a, x: x * np.tan(a), lambda a, y: y / np.tan(a))),
    ('degrees',     unary_elementwise, np.radians),
    ('radians',     unary_elementwise, np.degrees),
    # unwrap
    ('deg2rad',     unary_elementwise, np.rad2deg),
    ('rad2deg',     unary_elementwise, np.deg2rad),

    # -- Hyperbolic / inverse-hyperbolic --
    ('sinh',        unary_elementwise, np.arcsinh),
    ('cosh',        unary_elementwise, (np.arccosh, keep_sign(np.arccosh))),
    ('tanh',        unary_elementwise, np.arctanh),
    ('arcsinh',     unary_elementwise, np.sinh),
    ('arccosh',     unary_elementwise, np.cosh),
    ('arctanh',     unary_elementwise, np.tanh),

    # -- Rounding --
    ('around',      unary_elementwise, identity),
    ('round',       unary_elementwise, identity),  # Added alias
    ('rint',        unary_elementwise, identity),
    ('fix',         unary_elementwise, identity),
    ('floor',       unary_elementwise, identity),
    ('ceil',        unary_elementwise, identity),
    ('trunc',       unary_elementwise, identity),

    # -- Sums, products, differences --
    ('prod',        _reduction),
    ('product',     _reduction),  # Added alias
    ('sum',         _reduction),
    ('nanprod',     _reduction),
    ('nansum',      _reduction),
    ('cumprod',     _accumulation),
    ('cumproduct',  _accumulation),  # Added alias
    ('cumsum',      _accumulation),
    ('nancumprod',  _accumulation),
    ('nancumsum',   _accumulation),
    ('diff',        _axiswise),  # TODO: write more specific translators that only invalidate/request neighbouring elements
    ('ediff1d',     _dataless,  nd),  # TODO: write more specific translators
    # gradient
    # cross
    # trapz

    # -- Exponents and logarithms --
    ('exp',         unary_elementwise, np.log),
    ('expm1',       unary_elementwise, np.log1p),
    ('exp2',        unary_elementwise, np.log2),
    ('log',         unary_elementwise, np.exp),
    ('log10',       unary_elementwise, lambda new_y: 10 ** new_y),
    ('log2',        unary_elementwise, np.exp2),
    ('log1p',       unary_elementwise, np.expm1),
    # logaddexp
    # logaddexp2

    # -- Other special functions --
    ('i0',          unary_elementwise, None),
    ('sinc',        unary_elementwise, None),

    # -- Floating point routines --
    # signbit
    # copysign
    # frexp
    # ldexp
    # nextafter
    # spacing

    # -- Rational routines --
    ('lcm',         binary_elementwise, (None, None)),
    ('gcd',         binary_elementwise, (None, None)),

    # -- Arithmetic operations --
    ('add',         binary_elementwise, (np.subtract, np.subtract)),
    ('reciprocal',  unary_elementwise, None),
    ('positive',    unary_elementwise, identity),
    ('negative',    unary_elementwise, np.negative),
    ('multiply',    binary_elementwise, (np.divide, np.divide)),
    ('divide',      binary_elementwise, (np.multiply, lambda result, other: np.divide(other, result))),
    ('power',       binary_elementwise, ((lambda new_y, n: new_y ** (1 / n), inv_power), lambda result, other: math.log(result, other))),
    ('subtract',    binary_elementwise, (np.add, lambda result, other: np.subtract(other, result))),
    ('true_divide', binary_elementwise, (np.multiply, lambda result, other: np.divide(other, result))),
    ('floor_divide',binary_elementwise, (None, None)),  # TODO: write inverse
    ('float_power', binary_elementwise, (None, None)),  # TODO: write inverse
    ('fmod',        binary_elementwise, (None, None)),  # TODO: write inverse
    ('mod',         binary_elementwise, (None, None)),  # TODO: write inverse
    ('modf',        unary_elementwise, None),
    ('remainder',   binary_elementwise, (None, None)),  # TODO: write inverse
    # ('divmod',    binary_elementwise, (None, None)),  # TODO: return tuple, needs attention

    # -- Handling complex numbers --
    ('angle',       unary_elementwise, (lambda a: np.cos(a) + 1j * np.sin(a), lambda a, c: (np.cos(a) + 1j * np.sin(a)) * np.abs(c))),
    ('real',        unary_elementwise, (lambda new_y: new_y, lambda new_y, x: np.imag(x) + new_y)),
    ('imag',        unary_elementwise, (lambda new_y: new_y * 1j, lambda new_y, x: np.real(x) + new_y * 1j)),
    ('conj',        unary_elementwise, np.conj),
    ('conjugate',   unary_elementwise, np.conjugate),

    # -- Extrema Finding --
    ('maximum',     binary_elementwise, (None, None)),  # TODO: write inverse
    ('fmax',        binary_elementwise, (None, None)),  # TODO: write inverse
    ('amax',        _reduction),
    ('max',         _reduction),  # Added Alias
    ('nanmax',      _reduction),
    ('minimum',     binary_elementwise, (None, None)),  # TODO: write inverse
    ('fmin',        binary_elementwise, (None, None)),  # TODO: write inverse
    ('amin',        _reduction),
    ('min',         _reduction),  # Added Alias
    ('nanmin',      _reduction),

    # -- Miscellaneous --
    # convolve
    # clip
    ('sqrt',        unary_elementwise, np.square),
    # cbrt
    ('square',      unary_elementwise, (np.sqrt, keep_sign(np.sqrt))),
    ('absolute',    unary_elementwise, (identity, keep_sign(identity))),
    ('abs',         unary_elementwise, (identity, keep_sign(identity))),  # added Alias
    # fabs
    ('sign',        unary_elementwise, lambda sgn, val: sgn * val),
    # heaviside
    # nan_to_num
    # real_if_close
    ('interp',      _dataless, nd),


    # Matrix library ( numpy.matlib )
    # https://numpy.org/doc/stable/reference/generated/numpy.matlib.zeros.html
    # ------------------------------------------------------------------------
    # matlib.empty
    # matlib.zeros
    # matlib.ones
    # matlib.eye
    # matlib.identity
    # matlib.repmat
    # matlib.rand
    # matlib.randn

    # Padding Arrays
    # https://numpy.org/doc/stable/reference/routines.padding.html
    # ------------------------------------------------------------
    # pad

    # Poly1d
    # https://numpy.org/doc/stable/reference/routines.polynomials.poly1d.html
    # -----------------------------------------------------------------------
    # poly1d
    ('polyval',     _dataless,      nd),
    # poly
    # roots
    ('polyfit',     _dataless,      nd),
    # polyder
    # polyint
    # polyadd
    # polydiv
    # polymul
    # polysub
    # RankWarning

    # Functions in numpy.random
    # https://numpy.org/doc/stable/reference/random/legacy.html#functions-in-numpy-random
    # -----------------------------------------------------------------------------------
    # beta(a, b[, size]) Draw samples from a Beta distribution.
    # binomial(n, p[, size]) Draw samples from a binomial distribution.
    # bytes(length) Return random bytes.
    # chisquare(df[, size]) Draw samples from a chi-square distribution.
    # choice(a[, size, replace, p]) Generates a random sample from a given 1-D array
    # dirichlet(alpha[, size]) Draw samples from the Dirichlet distribution.
    # exponential([scale, size]) Draw samples from an exponential distribution.
    # f(dfnum, dfden[, size]) Draw samples from an F distribution.
    # gamma(shape[, scale, size]) Draw samples from a Gamma distribution.
    # geometric(p[, size]) Draw samples from the geometric distribution.
    # get_state([legacy]) Return a tuple representing the internal state of the generator.
    # gumbel([loc, scale, size]) Draw samples from a Gumbel distribution.
    # hypergeometric(ngood, nbad, nsample[, size]) Draw samples from a Hypergeometric distribution.
    # laplace([loc, scale, size]) Draw samples from the Laplace or double exponential distribution with specified location (or mean) and scale (decay).
    # logistic([loc, scale, size]) Draw samples from a logistic distribution.
    # lognormal([mean, sigma, size]) Draw samples from a log-normal distribution.
    # logseries(p[, size]) Draw samples from a logarithmic series distribution.
    # multinomial(n, pvals[, size]) Draw samples from a multinomial distribution.
    # multivariate_normal(mean, cov[, size, ...]) Draw random samples from a multivariate normal distribution.
    # negative_binomial(n, p[, size]) Draw samples from a negative binomial distribution.
    # noncentral_chisquare(df, nonc[, size]) Draw samples from a noncentral chi-square distribution.
    # noncentral_f(dfnum, dfden, nonc[, size]) Draw samples from the noncentral F distribution.
    # normal([loc, scale, size]) Draw random samples from a normal (Gaussian) distribution.
    # pareto(a[, size]) Draw samples from a Pareto II or Lomax distribution with specified shape.
    # permutation(x) Randomly permute a sequence, or return a permuted range.
    # poisson([lam, size]) Draw samples from a Poisson distribution.
    # power(a[, size]) Draws samples in [0, 1] from a power distribution with positive exponent a - 1.
    # rand(d0, d1, ..., dn) Random values in a given shape.
    ('rand',        _random),
    # randint(low[, high, size, dtype]) Return random integers from low (inclusive) to high (exclusive).
    ('randint',     _random),
    # randn(d0, d1, ..., dn) Return a sample (or samples) from the "standard normal" distribution.
    ('randn',       _random),
    # random([size]) Return random floats in the half-open interval [0.0, 1.0).
    # random_integers(low[, high, size]) Random integers of type np.int_ between low and high, inclusive.
    # random_sample([size]) Return random floats in the half-open interval [0.0, 1.0).
    # ranf This is an alias of random_sample.
    # rayleigh([scale, size]) Draw samples from a Rayleigh distribution.
    # sample This is an alias of random_sample.
    # seed([seed]) Reseed the singleton RandomState instance.
    # set_state(state) Set the internal state of the generator from a tuple.
    # shuffle(x) Modify a sequence in-place by shuffling its contents.
    # standard_cauchy([size]) Draw samples from a standard Cauchy distribution with mode = 0.
    # standard_exponential([size]) Draw samples from the standard exponential distribution.
    # standard_gamma(shape[, size]) Draw samples from a standard Gamma distribution.
    # standard_normal([size]) Draw samples from a standard Normal distribution (mean=0, stdev=1).
    # standard_t(df[, size]) Draw samples from a standard Student's t distribution with df degrees of freedom.
    # triangular(left, mode, right[, size]) Draw samples from the triangular distribution over the interval [left, right].
    # uniform([low, high, size]) Draw samples from a uniform distribution.
    # vonmises(mu, kappa[, size]) Draw samples from a von Mises distribution.
    # wald(mean, scale[, size]) Draw samples from a Wald, or inverse Gaussian, distribution.
    # weibull(a[, size]) Draw samples from a Weibull distribution.
    # zipf(a[, size]) Draw samples from a Zipf distribution.


    # Set routines
    # https://numpy.org/doc/stable/reference/routines.set.html
    # --------------------------------------------------------
    # lib.arraysetops
    # unique
    # in1d
    # intersect1d
    # isin
    # setdiff1d
    # setxor1d
    # union1d

    # Sorting, searching, and counting
    # https://numpy.org/doc/stable/reference/routines.sort.html
    # ---------------------------------------------------------

    # -- Sorting --
    ('sort',        _axiswise),
    # lexsort
    ('argsort',     _axiswise),
    # ndarray.sort
    # sort_complex
    # partition
    # argpartition

    # -- Searching --
    ('argmax',      _reduction),
    ('nanargmax',   _reduction),
    ('argmin',      _reduction),
    ('nanargmin',   _reduction),
    ('argwhere',    _dataless,      nd),
    ('nonzero',     _dataless,      tuple),  # TODO: needs specifically tailored path translators
    ('flatnonzero', _dataless,      tuple),
    ('where',       _dataless,      nd),
    ('searchsorted',_dataless,      []),
    ('extract',     _dataless,      nd),

    # -- Counting --
    ('count_nonzero', _reduction),

    # Statistics
    # https://numpy.org/doc/stable/reference/routines.statistics.html
    # ---------------------------------------------------------------

    # -- Order statistics --
    ('ptp',         _reduction),
    ('percentile',  _dataless,      nd),  # TODO: need to write specialized along-axis translators
    ('nanpercentile', _dataless,    nd),  # TODO: need to write specialized along-axis translators
    ('quantile',  _dataless,        nd),  # TODO: need to write specialized along-axis translators
    ('nanquantile', _dataless,      nd),  # TODO: need to write specialized along-axis translators

    # -- Averages and variances --
    ('median',      _reduction),
    ('average',     _reduction),
    ('mean',        _reduction),
    ('std',         _reduction),
    ('var',         _reduction),
    ('nanmedian',   _reduction),
    ('nanmean',     _reduction),
    ('nanstd',      _reduction),
    ('nanvar',      _reduction),

    # -- Correlating --
    ('corrcoef',    _dataless,      nd),
    ('correlate',   _dataless,      nd),
    ('cov',         _dataless,      nd),

    # -- Histograms --
    ('histogram',   _dataless,      tuple),
    ('histogram2d', _dataless,      tuple),
    ('histogramdd', _dataless,      tuple),
    ('bincount',    _dataless,      nd),
    ('histogram_bin_edges',    _dataless,      nd),
    ('digitize',    _dataless,      nd),

    # Window functions
    # https://numpy.org/doc/stable/reference/routines.window.html
    # -----------------------------------------------------------
    ('bartlett',    _dataless,      nd),
    ('blackman',    _dataless,      nd),
    ('hamming',     _dataless,      nd),
    ('hanning',     _dataless,      nd),
    ('kaiser',      _dataless,      nd),

    # -- Casting --
    # ('int32',     unary_elementwise, identity),  # causes problems with specifying dtype=np.int32
    # ('int64',     unary_elementwise, identity),  # causes problems with specifying dtype=np.int64
    # ('int',       unary_elementwise, identity),  # DeprecationWarning: `np.int` is a deprecated alias for the builtin `int`.
    # ('float',     unary_elementwise, identity),  # DeprecationWarning: `np.float` is a deprecated alias for the builtin `float`.

    #
    # Indexing routines
    # https://numpy.org/doc/stable/reference/arrays.indexing.html
    # -----------------------------------------------------------
    # c_
    # r_
    # s_
    # nonzero
    # where
    # indices
    # ix_
    # ogrid
    # ravel_multi_index
    # unravel_index
    # diag_indices
    # diag_indices_from
    # mask_indices
    # tril_indices
    # tril_indices_from
    # triu_indices
    # triu_indices_from
    # take
    # take_along_axis
    # choose
    # compress
    # diag
    ('diagonal',    _one2one, [0], nd),
    # select
    # lib.stride_tricks.sliding_window_view
    # lib.stride_tricks.as_strided
    # place
    # put
    # put_along_axis
    # putmask
    # fill_diagonal
    # nditer
    # ndenumerate
    # ndindex
    # nested_iters
    # flatiter
    # lib.Arrayterator
    # iterable

    # Not listed as np funcs in docs:
    ('size',        _shapeonly,     [0],    int),
    ('ndim',        _shapeonly,     [0],    int),
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

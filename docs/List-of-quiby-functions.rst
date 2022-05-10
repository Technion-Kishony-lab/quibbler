List of quiby functions
-----------------------

Quiby functions are functions modified to work directly on quib
arguments. When a quiby function is applied on quiby arguments, it
creates a new quib whose function is to perform the original function on
the value of its quib arguments.

To test if a given function is quiby, use ``is_quiby``:

Import
^^^^^^

.. code:: python

    import pyquibbler as qb
    from pyquibbler import iquib
    qb.override_all()
    import numpy as np

.. code:: python

    qb.is_quiby(np.sin)




.. code:: none

    True



.. code:: python

    qb.is_quiby(int)




.. code:: none

    False



Note though that any non-quiby functions, like ``int``, or any user
function can be converted be a quiby function using the ``quiby``
method. See :doc:`User-defined-functions`.

List of all built-in quiby functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To see all available quiby functiuons, use ``list_quiby_funcs()``:

.. code:: python

    qb.list_quiby_funcs()




.. code:: none

    ['None: <function identity_function at 0x7f8ae1178670>',
     'None: <function proxy at 0x7f8ae1178ee0>',
     'Quib: __add__',
     'Quib: __sub__',
     'Quib: __mul__',
     'Quib: __truediv__',
     'Quib: __floordiv__',
     'Quib: __mod__',
     'Quib: __pow__',
     'Quib: __lshift__',
     'Quib: __rshift__',
     'Quib: __and__',
     'Quib: __xor__',
     'Quib: __or__',
     'Quib: __radd__',
     'Quib: __rsub__',
     'Quib: __rmul__',
     'Quib: __rtruediv__',
     'Quib: __rfloordiv__',
     'Quib: __rmod__',
     'Quib: __rpow__',
     'Quib: __rlshift__',
     'Quib: __rrshift__',
     'Quib: __rand__',
     'Quib: __rxor__',
     'Quib: __ror__',
     'Quib: __ne__',
     'Quib: __lt__',
     'Quib: __gt__',
     'Quib: __ge__',
     'Quib: __le__',
     'Quib: __matmul__',
     'Quib: __neg__',
     'Quib: __pos__',
     'Quib: __abs__',
     'Quib: __invert__',
     'Quib: __round__',
     'Quib: __trunc__',
     'Quib: __floor__',
     'Quib: __ceil__',
     'Quib: __getitem__',
     'Axes: plot',
     'Axes: imshow',
     'Axes: text',
     'Axes: bar',
     'Axes: hist',
     'Axes: pie',
     'Axes: legend',
     'Axes: _sci',
     'Axes: matshow',
     'Axes: scatter',
     'Axes: set_xticks',
     'Axes: set_yticks',
     'Axes: set_xticklabels',
     'Axes: set_yticklabels',
     'Axes: set_xlabel',
     'Axes: set_ylabel',
     'Axes: set_title',
     'Axes: set_visible',
     'Axes: set_facecolor',
     'Axes: set_xlim',
     'Axes: set_ylim',
     'matplotlib.widgets: RadioButtons',
     'matplotlib.widgets: Slider',
     'matplotlib.widgets: CheckButtons',
     'matplotlib.widgets: RectangleSelector',
     'matplotlib.widgets: TextBox',
     'matplotlib.image: imread',
     'numpy: amin',
     'numpy: amax',
     'numpy: argmin',
     'numpy: argmax',
     'numpy: nanargmin',
     'numpy: nanargmax',
     'numpy: sum',
     'numpy: prod',
     'numpy: nanprod',
     'numpy: nansum',
     'numpy: any',
     'numpy: all',
     'numpy: average',
     'numpy: mean',
     'numpy: var',
     'numpy: std',
     'numpy: median',
     'numpy: diff',
     'numpy: sort',
     'numpy: cumsum',
     'numpy: cumprod',
     'numpy: cumproduct',
     'numpy: nancumsum',
     'numpy: nancumprod',
     'numpy: add',
     'numpy: subtract',
     'numpy: true_divide',
     'numpy: multiply',
     'numpy: power',
     'numpy: left_shift',
     'numpy: right_shift',
     'numpy: floor_divide',
     'numpy: remainder',
     'numpy: hypot',
     'numpy: float_power',
     'numpy: fmod',
     'numpy: lcm',
     'numpy: gcd',
     'numpy: fmin',
     'numpy: fmax',
     'numpy: logical_and',
     'numpy: logical_or',
     'numpy: logical_xor',
     'numpy: equal',
     'numpy: not_equal',
     'numpy: greater',
     'numpy: greater_equal',
     'numpy: less',
     'numpy: less_equal',
     'numpy: sqrt',
     'numpy: square',
     'numpy: sin',
     'numpy: cos',
     'numpy: tan',
     'numpy: arcsin',
     'numpy: arccos',
     'numpy: arctan',
     'numpy: degrees',
     'numpy: radians',
     'numpy: deg2rad',
     'numpy: rad2deg',
     'numpy: absolute',
     'numpy: real',
     'numpy: imag',
     'numpy: angle',
     'numpy: conjugate',
     'numpy: sign',
     'numpy: arcsinh',
     'numpy: arccosh',
     'numpy: arctanh',
     'numpy: sinh',
     'numpy: cosh',
     'numpy: tanh',
     'numpy: reciprocal',
     'numpy: positive',
     'numpy: negative',
     'numpy: invert',
     'numpy: modf',
     'numpy: exp',
     'numpy: exp2',
     'numpy: expm1',
     'numpy: log',
     'numpy: log2',
     'numpy: log1p',
     'numpy: log10',
     'numpy: ceil',
     'numpy: floor',
     'numpy: round',
     'numpy: around',
     'numpy: rint',
     'numpy: fix',
     'numpy: trunc',
     'numpy: i0',
     'numpy: sinc',
     'numpy: rot90',
     'numpy: concatenate',
     'numpy: repeat',
     'numpy: full',
     'numpy: reshape',
     'numpy: transpose',
     'numpy: array',
     'numpy: swapaxes',
     'numpy: tile',
     'numpy: asarray',
     'numpy: squeeze',
     'numpy: expand_dims',
     'numpy: ravel',
     'numpy: squeeze',
     'numpy: ones_like',
     'numpy: zeros_like',
     'numpy: shape',
     'numpy: arange',
     'numpy: polyfit',
     'numpy: interp',
     'numpy: linspace',
     'numpy: polyval',
     'numpy: corrcoef',
     'numpy: array2string',
     'numpy: zeros',
     'numpy: ones',
     'numpy: eye',
     'numpy: identity',
     'numpy: genfromtxt',
     'numpy: load',
     'numpy: loadtxt',
     'numpy.random: rand',
     'numpy.random: randn',
     'numpy.random: randint',
     'numpy: apply_along_axis',
     'numpy: vectorize',
     'Quib: get_override_mask']




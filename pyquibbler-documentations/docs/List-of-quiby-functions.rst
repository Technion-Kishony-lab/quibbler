List of quiby functions
-----------------------

Quiby functions are functions that have been modified to work directly
on quib arguments. When a quiby function is applied on quib arguments,
it creates a new quib, whose function is to perform the original
function on the *value* of its quib arguments.

.. code:: python

    # Imports
    import pyquibbler as qb
    from pyquibbler import iquib
    qb.initialize_quibbler()
    import numpy as np

Checking if a function is ‘quiby’:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To check whether a given function is quiby, use ``is_quiby``.

For example, ``np.sin`` is a quiby function:

.. code:: python

    qb.is_quiby(np.sin)




.. code:: none

    True



We can therefore use it directly on quib arguments:

.. code:: python

    x = iquib(1.5)
    np.sin(x)



.. code:: none

    VBox(children=(Label(value='sin(x)'), HBox(children=(HBox(children=(ToggleButton(value=False, description='Val…




.. raw:: html

    



On the other hand, ``int`` is not a quiby function:

.. code:: python

    qb.is_quiby(int)




.. code:: none

    False



Applying ``int`` directly on a quib argument will raise an exception.

Note though that any non-quiby functions, like ``int``, or any user
function can be converted be a quiby function using the function
``quiby``. See :doc:`User-defined-functions`.

List of all built-in quiby functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To see all available quiby functiuons, use ``list_quiby_funcs()``:

.. code:: python

    qb.list_quiby_funcs()




.. code:: none

    ['None: <function identity_function at 0x10bc95480>',
     'None: <function proxy at 0x10bc957e0>',
     'None: <function identity_function_obj2quib at 0x10c0fb250>',
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
     'Axes: scatter',
     'Arc: __new__',
     'Arrow: __new__',
     'ArrowStyle: __new__',
     'BoxStyle: __new__',
     'Circle: __new__',
     'CirclePolygon: __new__',
     'ConnectionPatch: __new__',
     'ConnectionStyle: __new__',
     'Ellipse: __new__',
     'FancyArrow: __new__',
     'FancyArrowPatch: __new__',
     'FancyBboxPatch: __new__',
     'Patch: __new__',
     'RegularPolygon: __new__',
     'Axes: acorr',
     'Axes: angle_spectrum',
     'Axes: annotate',
     'Axes: arrow',
     'Axes: axhline',
     'Axes: axhspan',
     'Axes: axline',
     'Axes: axvline',
     'Axes: axvspan',
     'Axes: bar',
     'Axes: barbs',
     'Axes: barh',
     'Axes: boxplot',
     'Axes: broken_barh',
     'Axes: cohere',
     'Axes: contour',
     'Axes: contourf',
     'Axes: csd',
     'Axes: errorbar',
     'Axes: eventplot',
     'Axes: fill',
     'Axes: fill_between',
     'Axes: fill_betweenx',
     'Axes: hexbin',
     'Axes: hist',
     'Axes: hist2d',
     'Axes: hlines',
     'Axes: imshow',
     'Axes: legend',
     'Axes: loglog',
     'Axes: magnitude_spectrum',
     'Axes: matshow',
     'Axes: pcolor',
     'Axes: pcolormesh',
     'Axes: phase_spectrum',
     'Axes: pie',
     'Axes: plot_date',
     'Axes: psd',
     'Axes: quiver',
     'Axes: semilogx',
     'Axes: semilogy',
     'Axes: specgram',
     'Axes: spy',
     'Axes: stackplot',
     'Axes: stairs',
     'Axes: stem',
     'Axes: step',
     'Axes: streamplot',
     'Axes: table',
     'Axes3D: text2D',
     'Axes: tricontour',
     'Axes: tricontourf',
     'Axes: tripcolor',
     'Axes: triplot',
     'Axes: violinplot',
     'Axes: vlines',
     'Axes: xcorr',
     'Axes: set_alpha',
     'Axes: set_aspect',
     'Axes: set_facecolor',
     'Axes: set_fc',
     'Axes: set_position',
     'Axes: set_title',
     'Axes: set_visible',
     'Axes: set_xlabel',
     'Axes: set_xscale',
     'Axes: set_xticklabels',
     'Axes: set_xticks',
     'Axes: set_ylabel',
     'Axes: set_yscale',
     'Axes: set_yticklabels',
     'Axes: set_yticks',
     'Axes: grid',
     'Axes: bar_label',
     'Axes: set_xlim',
     'Axes: set_ylim',
     'Axes3D: acorr',
     'Axes3D: arrow',
     'Axes3D: axhline',
     'Axes3D: axhspan',
     'Axes3D: axis',
     'Axes3D: axline',
     'Axes3D: axvline',
     'Axes3D: axvspan',
     'Axes3D: bar',
     'Axes3D: bar3d',
     'Axes3D: barbs',
     'Axes3D: barh',
     'Axes3D: boxplot',
     'Axes3D: broken_barh',
     'Axes3D: bxp',
     'Axes3D: contour3D',
     'Axes3D: contourf3D',
     'Axes3D: csd',
     'Axes3D: errorbar',
     'Axes3D: eventplot',
     'Axes3D: fill',
     'Axes3D: fill_between',
     'Axes3D: fill_betweenx',
     'Axes3D: hist',
     'Axes3D: hist2d',
     'Axes3D: hlines',
     'Axes3D: imshow',
     'Axes3D: legend',
     'Axes3D: loglog',
     'Axes3D: matshow',
     'Axes3D: pie',
     'Axes3D: plot3D',
     'Axes3D: plot_date',
     'Axes3D: plot_surface',
     'Axes3D: plot_trisurf',
     'Axes3D: plot_wireframe',
     'Axes3D: quiver3D',
     'Axes3D: scatter3D',
     'Axes3D: secondary_xaxis',
     'Axes3D: secondary_yaxis',
     'Axes3D: semilogx',
     'Axes3D: semilogy',
     'Axes3D: stackplot',
     'Axes3D: stairs',
     'Axes3D: stem3D',
     'Axes3D: text3D',
     'Axes3D: tricontour',
     'Axes3D: tricontourf',
     'Axes3D: tripcolor',
     'Axes3D: triplot',
     'Axes3D: tunit_cube',
     'Axes3D: tunit_edges',
     'Axes3D: violin',
     'Axes3D: violinplot',
     'Axes3D: vlines',
     'Axes3D: voxels',
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
     'numpy: cumsum',
     'numpy: cumprod',
     'numpy: cumproduct',
     'numpy: nancumsum',
     'numpy: nancumprod',
     'numpy: diff',
     'numpy: sort',
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
     'numpy: array',
     'numpy: rot90',
     'numpy: reshape',
     'numpy: transpose',
     'numpy: swapaxes',
     'numpy: asarray',
     'numpy: squeeze',
     'numpy: expand_dims',
     'numpy: ravel',
     'numpy: diagonal',
     'numpy: flip',
     'numpy: concatenate',
     'numpy: repeat',
     'numpy: full',
     'numpy: tile',
     'numpy: broadcast_to',
     'numpy: ones_like',
     'numpy: zeros_like',
     'numpy: shape',
     'numpy: size',
     'numpy: ndim',
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
     'numpy: ptp',
     'numpy: nonzero',
     'numpy: trace',
     'numpy: genfromtxt',
     'numpy: load',
     'numpy: loadtxt',
     'numpy.random: rand',
     'numpy.random: randn',
     'numpy.random: randint',
     'numpy: apply_along_axis',
     'numpy: vectorize',
     'Quib: get_override_mask',
     'Quib: get_quiby_name',
     'np.ndarray.T',
     'np.ndarray.imag',
     'np.ndarray.real',
     'np.ndarray.ndim',
     'np.ndarray.shape',
     'np.ndarray.size',
     'np.ndarray.all',
     'np.ndarray.any',
     'np.ndarray.argmax',
     'np.ndarray.argmin',
     'np.ndarray.conj',
     'np.ndarray.conjugate',
     'np.ndarray.cumprod',
     'np.ndarray.cumsum',
     'np.ndarray.diagonal',
     'np.ndarray.flatten',
     'np.ndarray.max',
     'np.ndarray.mean',
     'np.ndarray.min',
     'np.ndarray.nonzero',
     'np.ndarray.prod',
     'np.ndarray.ptp',
     'np.ndarray.ravel',
     'np.ndarray.repeat',
     'np.ndarray.reshape',
     'np.ndarray.round',
     'np.ndarray.squeeze',
     'np.ndarray.std',
     'np.ndarray.sum',
     'np.ndarray.swapaxes',
     'np.ndarray.tolist',
     'np.ndarray.trace',
     'np.ndarray.transpose',
     'np.ndarray.var']




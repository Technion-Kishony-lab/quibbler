User-defined functions
----------------------

While many *Python*, *NumPy* and *Matplotlib* functions are
pre-programmed to work directly with quib arguments (see
:doc:`List-of-quiby-functions`), occasionally we need to create quibs that
implement other, currently non-quiby functions, either functions of
external packages, or user-defined function.

*Quibbler* allows several ways for creating quibs that represent any
arbitrary function. Below we explain and demonstrate these different
ways of implementating user-defined functions.

Import
^^^^^^

.. code:: ipython3

    import pyquibbler as qb
    from pyquibbler import q, quiby, quiby_function, iquib, Quib
    qb.override_all()
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.widgets as widgets
    %matplotlib tk

An example function
^^^^^^^^^^^^^^^^^^^

We consider as an example the following user-defined function that we
want to implement as a quib, with quib arguments:

.. code:: ipython3

    def add(a, b):
        print(f'function add called with {a}, {b}')
        return a + b

Our task is to implement this function on the value of two quibs:

.. code:: ipython3

    x = iquib(np.array([1, 2, 3]))
    y = iquib(100)

The q-syntax
~~~~~~~~~~~~

The *Quibbler* function :py:func:`~pyquibbler.q` creates a function quib representing
any given function call. The syntax ``q(func, *args, **kwargs)`` returns
a quib that implement ``func(*args, **kwargs)``.

For the example function above, we will implement:

.. code:: ipython3

    w1 = q(add, x, y)

.. code:: ipython3

    w1.get_value()


.. parsed-literal::

    function add called with [1 2 3], 100




.. parsed-literal::

    array([101, 102, 103])



The quiby syntax
~~~~~~~~~~~~~~~~

The *Quibbler* function :py:func:`~pyquibbler.quiby` converts any function to a quiby
function - namely to a function that can work directly on quib arguments
to create a quib.

For the example function above, we will implement:

.. code:: ipython3

    w2 = quiby(add)(x, y)

.. code:: ipython3

    w2.get_value()


.. parsed-literal::

    function add called with [1 2 3], 100




.. parsed-literal::

    array([101, 102, 103])



The advatage of ``quiby`` is that it also allows specifying properties
of the quiby function, including ``lazy``, ``pass_quibs``,
``is_random``, ``is_graphics``, ``is_file_loading``. See documentation
of :py:func:`~pyquibbler.quiby`).

``quiby`` can also be used as a decorator, or to more easily specify
function properties with a decorator, use the :py:func:`~pyquibbler.quiby_function`
decorator.

The quiby_function decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *Quibbler* decorator :py:func:`~pyquibbler.quiby_function` converts any function to
a quiby function, while allowing easy way to specify function propeties.

For the example function above, we will implement:

.. code:: ipython3

    @quiby_function(is_graphics=False)
    def add(a, b):
        print(f'function add called with {a}, {b}')
        return a + b

.. code:: ipython3

    w3 = add(x, y)

.. code:: ipython3

    w3.get_value()


.. parsed-literal::

    function add called with [1 2 3], 100




.. parsed-literal::

    array([101, 102, 103])



The pass_quibs property
~~~~~~~~~~~~~~~~~~~~~~~

Normally, as above, a quib calls its function with any quibs in its
arguments replaced by their values. Sometimes, we may want to send the
quib objects themselves to the implemented function. Transferring quibs
to the function is controlled by the :py:attr:`~pyquibbler.Quib.pass_quibs` property.

Passing quibs as arguments is particularly warranted if we wish to
implement inverse assignments from graphics created within the function
into upstream quibs outside the function.

The following example demonstrates such use of ``pass_quibs=True``
functions. Setting ``pass_quibs=True``, the user defined function will
see actual quib arguments. Thereby, graphics built by the function can
inverse assign to upstream quibs outside the function. Note that, as
demonstrated, the function can also execute ``get_value`` on its quib
arguments.

.. code:: ipython3

    # Define axes:
    fig = plt.figure(figsize=(4, 5))
    axs = fig.gca()
    axs.axis('equal')
    axs.axis('square')
    axs.axis([0.5, 5.5, 0.5, 5.5])
    
    # Define a function that can make two alternative plots of the data.
    @quiby_function(is_graphics=True, pass_quibs=True)
    def plot_draggable_points(y: Quib, transpose: Quib):
        x = range(1, len(y.get_value()) + 1)
        if transpose:
            axs.plot(y, x, marker='o', picker=True)
        else:
            axs.plot(x, y, marker='o', picker=True)
            
    y = iquib([1., 3., 4., 2., 1.])
    is_transpose = iquib(False)
    
    plot_draggable_points(y, is_transpose)
    
    axs_widget = fig.add_axes([0.2, 0.02, 0.4, 0.16])
    axs_widget.axis('off')
    widgets.CheckButtons(ax=axs_widget, labels=['Transpose'], actives=[is_transpose]);

[[images/User-defined-functions-pass-quibs.gif]]

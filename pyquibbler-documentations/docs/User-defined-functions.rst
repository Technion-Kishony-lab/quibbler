User-defined functions
----------------------

While many *Python*, *NumPy* and *Matplotlib* functions are
pre-programmed to work directly with quib arguments (see
:doc:`List-of-quiby-functions`), occasionally we need to create quibs that
implement other, currently non-quiby functions, either functions of
external packages, or user-defined function.

*Quibbler* allows several ways for creating quibs that represent any
arbitrary function. Below we explain and demonstrate these different
ways of implementing user-defined functions.

The implementations described here are for functions that work on quib
values as a whole. *Quibbler* also supports implementing user-defined
functions that work consecutively on parts of arrays, using the *NumPy*
syntax of ``np.vectorize``, ``np.apply_along_axis`` (see
:doc:`Diverged-evaluation`).

Import
^^^^^^

.. code:: python

    import pyquibbler as qb
    from pyquibbler import q, quiby, iquib, Quib
    qb.initialize_quibbler()
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.widgets as widgets
    %matplotlib tk

An example function
'''''''''''''''''''

We consider as an example the following user-defined function that we
want to implement as a quib, with quib arguments:

.. code:: python

    def add(a, b):
        print(f'function add called with {a}, {b}')
        return a + b

Our task is to implement this function on the value of two quibs:

.. code:: python

    x = iquib(np.array([1, 2, 3]))
    y = iquib(100)

The q-syntax
~~~~~~~~~~~~

The *Quibbler* function :py:func:`~pyquibbler.q` creates a function quib representing
any given function call. The syntax ``q(func, *args, **kwargs)`` returns
a quib that implement ``func(*args, **kwargs)``.

For the example function above, we will implement:

.. code:: python

    w1 = q(add, x, y)

.. code:: python

    w1.get_value()


.. code:: none

    function add called with [1 2 3], 100




.. code:: none

    array([101, 102, 103])



The quiby syntax
~~~~~~~~~~~~~~~~

The *Quibbler* function :py:func:`~pyquibbler.quiby` converts any function to a quiby
function - namely to a function that can work directly on quib arguments
to create a quib.

For the example function above, we will implement:

.. code:: python

    w2 = quiby(add)(x, y)

.. code:: python

    w2.get_value()


.. code:: none

    function add called with [1 2 3], 100




.. code:: none

    array([101, 102, 103])



The advatage of ``quiby`` is that it can also be used as a decorator and
it allows specifying properties of the quiby function, including
``lazy``, ``pass_quibs``, ``is_random``, ``is_graphics``,
``is_file_loading``. See documentation of :py:func:`~pyquibbler.quiby`).

Using quiby as a decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~

For the example above, we can implement the function ``add`` as a quiby
function, using ``quiby`` as a decorator:

.. code:: python

    @quiby(is_graphics=False)
    def add(a, b):
        print(f'function add called with {a}, {b}')
        return a + b

.. code:: python

    w3 = add(x, y)

.. code:: python

    w3.get_value()


.. code:: none

    function add called with [1 2 3], 100




.. code:: none

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

.. code:: python

    # Define axes:
    fig = plt.figure(figsize=(4, 5))
    axs = fig.gca()
    axs.axis('equal')
    axs.axis('square')
    axs.axis([0.5, 5.5, 0.5, 5.5])
    
    # Define a function that can make two alternative plots of the data.
    @quiby(is_graphics=True, pass_quibs=True)
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

.. image:: images/User_defined_functions_pass_quibs.gif

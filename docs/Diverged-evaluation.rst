Diverged evaluation
-------------------

Rationale
^^^^^^^^^

Data analysis pipelines can have *diverged* processing steps, where a
specific function is applied repeatedly to each of many individual data
items (e.g., enhancing each image in a stack of images). In such
diverged steps, the calculation of each data item could be done
independently, and we may only want to calculate some and not all of the
items at a given time. Furthermore, changes to upstream parameters may
only affect the calculations of some of the data items while any cached
calculations of other items remain valid (e.g., changing an enhancement
parameter specific for one image will require repeating the processing
of this image alone). We therefore need ways to independently calculate,
cache and track the validity of each data item in such diverged analysis
steps. In *Quibbler*, such independent processing and tracking is
automatically enabled when we use the *NumPy* syntax of
:doc:`vectorize<https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html>`
and
:doc:`apply_along_axis<https://numpy.org/doc/stable/reference/generated/numpy.apply_along_axis.html>`.
Applying such *NumPy* vectorized functions to quib arguments creates a
*vectorized function quib* whose output array is calculated, cached and
invalidated not as a whole but rather element-by-element, or slice by
slice.

Quickly reviewing the standard behavior of np.vectorize
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*NumPy*\ ’s ``np.vectorize`` provides a standard syntax to *vectorize* a
given function such that when applied to array arguments it creates a
new array by acting repeatedly on each element of the array arguments
(or across slices thereof, see the ``signature`` kwarg).

For example:

.. code:: ipython3

    # Imports
    import pyquibbler as qb
    from pyquibbler import iquib, q
    qb.override_all()
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.widgets import RectangleSelector, Slider
    from matplotlib.patches import Arrow
    %matplotlib tk

.. code:: ipython3

    def my_sqr(x):
        print(f'calculating my_sqr of x = {x}')
        return x ** 2
    
    
    v_my_sqr = np.vectorize(my_sqr, otypes=[int])

In this example, ``v_my_sqr`` is the vectorized form of ``my_sqr``; when
``v_my_sqr`` is applied to an array, it executes the underlying function
``my_sqr`` on each element of the input array:

.. code:: ipython3

    v_my_sqr(np.array([0, 1, 2, 3, 4]))


.. parsed-literal::

    calculating my_sqr of x = 0
    calculating my_sqr of x = 1
    calculating my_sqr of x = 2
    calculating my_sqr of x = 3
    calculating my_sqr of x = 4




.. parsed-literal::

    array([ 0,  1,  4,  9, 16])



Applying a vectorized function to quib arguments creates a vectorized function quib
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In analogy to the standard behavior above, applying a vectorized
function to quib arguments creates a vectorized function quib that
calculates its output by calling the underlying function on each element
of the output of its quib arguments. As with other function quibs, this
definion is declarative (``lazy`` by default), so no calculations are
initially performed:

.. code:: ipython3

    x = iquib(np.array([0, 1, 2, 3, 4]))
    x_sqr = v_my_sqr(x).setp(cache_mode='on')

Calculations are only performed once we request the output of the
function quib:

.. code:: ipython3

    x_sqr.get_value()


.. parsed-literal::

    calculating my_sqr of x = 0
    calculating my_sqr of x = 1
    calculating my_sqr of x = 2
    calculating my_sqr of x = 3
    calculating my_sqr of x = 4




.. parsed-literal::

    array([ 0,  1,  4,  9, 16])



Vectorized quibs independently calculate and cache specifically requested array elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As the output of vectorized function quibs is calculated
element-by-element, there is no need to calculate the entire array if
only specific elements are requested. Indeed, an ``np.vectorize`` quib
knows to only calculate the array elements specifically needed to
provide a requested output.

For example, let’s repeat the simple code above, but only ask for the
value of ``x_sqr`` at a specific element. *Quibbler* will only evaluate
the function at the requested position:

.. code:: ipython3

    x = iquib(np.array([0, 1, 2, 3, 4]))
    x_sqr = v_my_sqr(x).setp(cache_mode='on')
    x_sqr[3].get_value()


.. parsed-literal::

    calculating my_sqr of x = 3




.. parsed-literal::

    9



These calculated values resulting from each call to the underlying
fucntion are indepdnently cached, so further requests for array output
only calculate the parts of the array not yet calculated:

.. code:: ipython3

    x_sqr[2:].get_value()


.. parsed-literal::

    calculating my_sqr of x = 2
    calculating my_sqr of x = 4




.. parsed-literal::

    array([ 4,  9, 16])



.. code:: ipython3

    x_sqr.get_value()


.. parsed-literal::

    calculating my_sqr of x = 0
    calculating my_sqr of x = 1




.. parsed-literal::

    array([ 0,  1,  4,  9, 16])



Vectorized quibs track validity of individual array elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Not only array elements of vectorized function quibs are individually
calculated and cached, their validity is also independently tracked upon
upstream changes.

When upstream value changes, such changes only invalidate the
specifically affected array elements. Only the calculation of these
elements is then repeated when the output is requested:

.. code:: ipython3

    x[3] = 10

.. code:: ipython3

    x_sqr.get_value()


.. parsed-literal::

    calculating my_sqr of x = 10




.. parsed-literal::

    array([  0,   1,   4, 100,  16])



Using vectorize for graphic functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Vectorized function quibs readily facilitate creating multiple instances
of similar graphic elements. This is done simply by vectorizing an
underlying function that create graphics and setting
``Quib.is_graphics=True`` in the vectorize command.

Here is a simple example:

.. code:: ipython3

    from functools import partial
    
    # define graphics vectorize function
    @partial(np.vectorize, is_graphics=True, signature='(),(2),(2),()->()')
    def draw_arrow(ax, xy0, dxy, w):
        xy1 = xy0 + dxy
        ax.plot([xy0[0], xy1[0]], [xy0[1], xy1[1]], 'r-')
        phi = np.pi + np.arctan2(dxy[1], dxy[0])
        phi1 = phi - 0.3
        phi2 = phi + 0.3
        ax.plot([xy1[0], xy1[0] + w*np.cos(phi1)], [xy1[1], xy1[1] + w*np.sin(phi1)], 'r')
        ax.plot([xy1[0], xy1[0] + w*np.cos(phi2)], [xy1[1], xy1[1] + w*np.sin(phi2)], 'r')
    
    # prepare figure
    plt.figure()
    ax = plt.gca()
    ax.axis('square')
    ax.axis([0, 50, 0, 50])
    
    # define quibs:
    xy = iquib(np.array([[10, 10], [20, 20], [30, 30], [40, 40]]))
    xy_tail = xy[0:-1]
    xy_head = xy[1:]
    dxy = xy_head - xy_tail
    w = iquib(4.)
    
    # draw
    draw_arrow(ax, xy_tail, dxy, w);
    plt.plot(xy[:,0], xy[:,1], 'ob', markersize=4, picker=True);

Passing quibs as arguments to allows inverse assignment from vectorized quibs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the examples above, when the vectorized function quib gets quib
arguments it sends to the underlying function the output value of these
quibs at given array positions. The underlying function deals with
regular, non-quib, arguments. Alternatively, it is also possible to send
the underlying function quib arguments which reference the vectorize
quib arguments at the corresponding indices. This behavior is controlled
by the ``pass_quibs`` kwarg of ``np.vectorize``. Setting
``pass_quibs=True`` will pass quib as arguments thus enabling some
additional functionality including in particular the ability to inverse
assign from graphics created within the function.

See this example:

.. code:: ipython3

    xy_default = iquib(np.array([10, 20, 10, 20]))
    n = iquib(5).setp(assignment_template=(1, 8))
    xy = np.tile(xy_default, (n, 1))
    xy.setp(allow_overriding=True, assigned_quibs={xy})
    
    @partial(np.vectorize, signature='(),(4)->()', is_graphics=True, pass_quibs=True)
    def rectselect(ax, ext):
        RectangleSelector(ax=ax, extents=ext)
        return
    
    
    ax = plt.gca()
    plt.axis('square')
    plt.axis([0, 100, 0, 100])
    rectselect(ax, xy)
    plt.text(5, 95, q(str, xy), va='top');
    Slider(ax=plt.axes([0.4, 0.2, 0.3, 0.05]), label='n', valmin=1, valmax=8, valinit=n);




.. parsed-literal::

    QSlider(ax=<Axes:>, label='n', valmin=1, valmax=8, valinit=n)



.. image:: images/divergence_gif/Divergence_passquibs.gif

Additional demos
^^^^^^^^^^^^^^^^

For additional examples, see:

-  :doc:`examples/quibdemo_compare_images`

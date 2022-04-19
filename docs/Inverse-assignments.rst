Assignments
-----------

Rationale
~~~~~~~~~

Data analysis pipelines are often heavily parametrized, necessitating
means to identify and change parameters easily, transparently, and
interactively. Typically, though, interactive parameter specification is
challenging, as underlying input parameters are often transformed into
various different downstream forms through a range of functional
operations (changing units, shifting between linear and log scales,
extracting specific parameters out of larger data structures, combining
parameters, etc.). Further, such transformed versions of the parameters
can then be presented graphically in various forms. In *Quibbler*, these
multiple downstream representations of an upstream parameter are all
inherently linked: changing any downsteam representation of a given
parameter automatically change its source value and all other
representations.

This behavior is achieved through the process of *inverse assignment*,
in which an assignment to a downstream function quib is propagated
backwards and ultimately actualized as a change in an upstream quib,
typically the source input quib. This upstream change then propagates
downstream to affect all other representations of this same parameter.
This behavior allows readily building sophisticated, yet inherently
interactive, data analysis pipelines.

Below, we cover how the value of input quibs can change either simply by
direct assignments or through the process of inverting assignments made
to downstream function quibs. Please also consult with the chapter on
:doc:`Overriding-default-functionality` for assignments actualized as
exceptions to function quibs.

Making quib assignments
~~~~~~~~~~~~~~~~~~~~~~~

Quib assignments are made using standard *Python* assignment syntax.

For example:

.. code:: ipython3

    # Imports
    import pyquibbler as qb
    from pyquibbler import iquib, q
    qb.override_all()
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Slider, CheckButtons
    %matplotlib tk

.. code:: ipython3

    words = iquib(['We', 'love', 'big', 'data'])
    words.get_value()




.. parsed-literal::

    ['We', 'love', 'big', 'data']



.. code:: ipython3

    words[2] = 'huge'
    words.get_value()




.. parsed-literal::

    ['We', 'love', 'huge', 'data']



Deep-level assignments are also supported:

.. code:: ipython3

    x = iquib([1, [2, 3], 4])
    x[1][1] = 0
    x.get_value()




.. parsed-literal::

    [1, [2, 0], 4]



Whole-object assignments
^^^^^^^^^^^^^^^^^^^^^^^^

If we want to completely replace the whole value of a quib, we use the
``assign()`` method. For example, suppose we want to assign the *NumPy*
array ``np.array([10, 20, 30])`` into the quib ``x`` above. The syntax
``x = np.array([10, 20, 30])`` cannot work as it simply sets ``x`` to
*be* the *NumPy* array rather than setting the existing quib’s value to
the array. To perform such whole-object assignments, we can use the
``assign()`` method:

.. code:: ipython3

    x.assign(np.array([10, 20, 30]))
    x.get_value()




.. parsed-literal::

    array([10, 20, 30])



Inverse assignments: an assignment into a function quib is inverted backwards to affect the corresponding upstream input quib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, assignments to functional quibs are propagated backwards to
alter upstream quibs. This process of upstream assignment propagation is
termed *inverse assignment*. Inverse assignment proceeds upstream until
it reaches a quib, typically an i-quib, in which the assignment is
ultimately *actualized* (for assignments actualized at intermediate
f-quibs, see :doc:`Overriding-default-functionality`).

For example, suppose ``z`` is an i-quib and ``z10`` is an f-quib that
depends on ``z``:

.. code:: ipython3

    z = iquib(np.array([11, 12, 13]))
    z10 = z + 10
    z10.get_value()




.. parsed-literal::

    array([21, 22, 23])



Then, making an assignment into ``z10`` is propagated backwards,
reaching the i-quib ``z`` where the assignment is actualized:

.. code:: ipython3

    z10[2] = 100;
    z.get_value()




.. parsed-literal::

    array([11, 12, 90])



.. code:: ipython3

    z10.get_value()




.. parsed-literal::

    array([ 21,  22, 100])



Such inverse assignment can transverse multiple levels and many types of
functional operations including arithmetic functions, type casting,
concatenation, array-reordering, array referencing and more.

For example, consider a series of functional operations starting with a
given i-quib:

.. code:: ipython3

    xy_list = iquib(np.array([[8, 1], [16, 2], [2, 4]]))
    xy_list.get_value()




.. parsed-literal::

    array([[ 8,  1],
           [16,  2],
           [ 2,  4]])



.. code:: ipython3

    xy0 = xy_list[0] # -> [8, 1]
    xy2 = xy_list[2] # -> [2, 4]
    x0 = xy0[[0]] # -> [8]
    y2 = xy2[[1]] # -> [4]
    x0y2 = np.concatenate([x0, y2]) # -> [8, 4]
    x0y2_log = np.log2(x0y2) # -> [3, 2]
    x0y2_log_plus10 = 10 + x0y2_log # -> [13, 12]
    x0y2_log_plus10.get_value()




.. parsed-literal::

    array([13., 12.])



then, assigning to the downstream f-quib:

.. code:: ipython3

    x0y2_log_plus10[1] = 16

is translated into upstream changes in the corresponding indeces of the
relevant source i-quibs:

.. code:: ipython3

    xy_list.get_value()




.. parsed-literal::

    array([[ 8,  1],
           [16,  2],
           [ 2, 64]])



Combining inverse assignments with graphics-driven assignments readily creates interactive GUI for parameter specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By combining inverse assignment with :doc:`Graphics` we can easily create
intuitive and interactive graphical user interface for parameter
specification. This combination is particularly powerful in cases where
an upstream parameter is transformed into one or more different, yet
inherently dependent, representations. In such cases, changing any of
these representations will affect the source parameter, by inverse
assignment, and thereby affect all other dependent representations.

Consider the following example, in which we choose parameters for
analysis of Electronic Health Records. In this example, we need to
translate from date of birth (dob) to age and backwards, from height in
foot to centimeters, and from individual Boolean parameters to a Boolean
array that can be presented as check-boxes:

.. code:: ipython3

    params = iquib({
        'dob': [1950, 2010], 
        'Smoking': True, 
        'Diabetic': False, 
        'max_height_foot': 5.5
    })
    
    dob = params['dob']
    dob = np.array(dob)
    current_year = iquib(2022)
    age = -dob + current_year
    smoking = params['Smoking']
    diab = params['Diabetic']
    max_height_cm = params['max_height_foot'] * 30.48
    
    plt.figure()
    plt.axes([0.2, 0.7, 0.6, 0.05])
    plt.axis([0, 100, -1, 1])
    plt.plot(age, [0, 0], 'v', markersize=18, picker=True)
    plt.xlabel('Age')
    plt.yticks([])
    
    bools = np.array([smoking, diab])
    ax = plt.axes([0.2, 0.3, 0.2, 0.2])
    CheckButtons(ax=ax, labels=['Smoking', 'Diabetic'], 
                 actives=bools)
    
    ax = plt.axes([0.2, 0.1, 0.6, 0.05])
    Slider(ax=ax, label='Height (cm)', 
           valinit=max_height_cm, valmax=200, valmin=50);

For additional examples, see:

-  :doc:`examples/quibdemo_LotkaVolterra`
-  :doc:`examples/quibdemo_same_data_in_many_forms`

Inverse assignments of many-to-one functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To allow natural powerful behavior, inverse assignment is defined in
*Quibbler* not only for one-to-one functions, but also for many-to-one
functions. In gerenral, such inversions are based on the original
upstream value onto which the assignment is inverted. This functionality
creates the naturally expected behaviors for the following type of
functions:

**Casting.** *Quibbler* will adequately inverse casting functions like
``float``, ``int`` and ``str`` (note that these functions are not
overridded, yet we can apply them using the ``q`` syntax).

For example:

.. code:: ipython3

    i = iquib(5)
    f = q(float, i)
    s = q(str, f)
    s.get_value()

.. code:: ipython3

    s.assign('7.2')
    i.get_value()




.. parsed-literal::

    7



**Rounding.** In *Quibbler*, the inverse of rounding functions, like
``round``, ``ceil``, ``floor`` is simply defined as the identify
function. So, while the inverse of round(10) can be any number between
9.5 and 10.5, *Quibbler* uses the value 10 for the inversion:

.. code:: ipython3

    f = iquib(np.array([-3.2, 3.2, -3.7, 3.7]))
    f_round = np.round(f)
    f_round[:] = 10
    f.get_value()




.. parsed-literal::

    array([10., 10., 10., 10.])



**Periodic functions.** Periodic functions have multiple inversion
solutions. *Quibbler* automatically chooses the solution closet to the
current value of the assigned quib. For example:

.. code:: ipython3

    phi = iquib(np.array([0., 180., 360., -360., 3600.]))
    sin_phi = np.sin(phi / 360 * 2 * np.pi) # <- [0., 0., 0., 0., 0.]
    sin_phi[0:5] = 0.5
    phi.get_value()




.. parsed-literal::

    array([30., 30., 30., 30., 30.])



**Other many-to-one functions.** As with periodic functions, in other
functions where multiple solutions exist, inverse assignments assumes
the solution closest to the current value:

.. code:: ipython3

    r = iquib(np.array([-3., 3.]))
    r2 = np.square(r)
    r2[:] = 16
    r.get_value()




.. parsed-literal::

    array([4., 4.])



Inverse assignment of binary operators with two quib arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As a convention, in binary operators, inverse assignment is defined to
target the first quib argument.

This definition allows specifying the upstream target for assignment
inversion.

Consider for example the different in behavior of the following two code
snippets:

.. code:: ipython3

    x = iquib([3, 4])
    s = x[0] + x[1]
    s.assign(10)
    x.get_value()




.. parsed-literal::

    [6, 4]



.. code:: ipython3

    x = iquib([3, 4])
    s = x[1] + x[0]
    s.assign(10)
    x.get_value()




.. parsed-literal::

    [3, 7]



These two codes differ only in the order in which ``x[0]`` and ``x[1]``
are added. In the first case, when we use ``s = x[0] + x[1]``, the first
quib is ``x[0]`` and the assignment into ``s`` is inverted to affect
``x[0]``. Conversely, in the second case, when we use
``s = x[1] + x[0]``, the first quib is ``x[1]`` and the assignment into
``s`` is inverted to affect ``x[1]``.

This behavior allows controlling the desired behavior of inverse
assignment when a given change can be satisfied in more than one way. As
an illustrating example, see: \*
:doc:`examples/quibdemo_drag_whole_object_vs_individual_points`

Inverse assignment of binary operators with two dependent quib arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As indicated above, when binary operators acting on two quibs are
inverted, inversion is set to always target the first quib. When these
two quibs are independent, the resulted upstream assignment will satisfy
the downstream assignment we have made (as seen in the example above).
However, when the two quibs are dependent, we can get upstream
assignments that do not necessarily satisfy the downstream assignments
we made. Formally speaking, inverse assignment is not meant to ‘solve’
an equation, rather as a function that propagate downstream assignments
to desired upstream changes. This is perhaps best exemplified in the
following simple code which allows adding a given value to specified
quib:

.. code:: ipython3

    xy = iquib(np.array([2, 3]))
    dxy = xy - xy

.. code:: ipython3

    dxy[1] = 4
    xy.get_value()




.. parsed-literal::

    array([2, 7])



.. code:: ipython3

    dxy[:] = [3, -1]
    xy.get_value()




.. parsed-literal::

    array([5, 6])



This behavior can be used, for example, to graphically control the
position of one object by “dragging” another fixed object. See:

-  :doc:`examples/quibdemo_dragging_fixed_object`

Upstream type casting can be used to restrict the value of downstream results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The value of downstream functional quibs could be restricted due to
specific type of upstream quibs.

In the following example, ``a`` is an integer and thereby ``b = 10 * a``
must be divisible by 10. Assigning a value of 33 to ``b`` assigns 3.3 to
``a``, but since ``a`` is an array of integers, it changes to 3 thereby
changing ``b`` to 30 (rather than the assigned value of 33):

.. code:: ipython3

    a = iquib(np.array([7]))
    b = 10 * a
    b[0] = 33
    b[0].get_value()




.. parsed-literal::

    30



This natural behavior can be used in applications where we need to
restrict the possible values of specific function quibs. See for
example:

-  :doc:`examples/quibdemo_drag_fixed_values`

Graphics-driven assignments
~~~~~~~~~~~~~~~~~~~~~~~~~~~

As we have seen in the :doc:`Quickstart` page, applying a graphics function
to a quib generates “live” graphics that changes when the quib is
changed; and conversely, making changes to quib graphics can be
interpreted as assignments to its source quib arguments. Such
graphics-driven assignments are enabled when we use a quib as the
value-setting kwarg of *Matplotlib* widgets, or when we indicate
``picker=True`` for plt.plot with quib arguments (see :doc:`Graphics`).

Combining inverse assignments with graphics driven assignments

When the red or green triangles are moved, Quibbler attempts to assign
to Threshold1 or Threshold2, respectively. Then, using inverse
assignment, these assignments are propagated backwards to the specific
indices of the Thresholds vector.

Undo/Redo assignments
~~~~~~~~~~~~~~~~~~~~~

Quibbler tracks all assignments (either graphics-driven as above, or
through the command line), allowing Undo/Redo functionality. Undo/Redo
can be done using the Undo/Redo buttons of the quibapp, or
programatically using ``qb.undo()``, ``qb.redo()``.

TODO

The assignment_template is used to restrict assigned values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Depending on the application, we may need to assure and verify that the
user only assign specific data types and values to a given quib. This is
achieved using the ``assignment_template`` property. When ``None``,
there are no restrictions on assignments. Otherwise, the following
options are available:

TODO

Saving quib assignments to files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The assignments of each quib can be saved into quib-associated files.
TODO: methods. For details, see :doc:`Project-save-load`.

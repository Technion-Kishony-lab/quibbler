The quib name
-------------

Quibs have both a static user-defined name (the :py:attr:`~pyquibbler.Quib.assigned_name`
property) and a dynamic automatic name representing their function (the
:py:attr:`~pyquibbler.Quib.functional_representation` property). These names do not
determine or affect the function of the quib. Instead, they are only
useful for annotating and clarifying what each quib is doing as well as
for naming linked input files for saving any quib assignments.

The ``assigned_name`` and the ``functional_representation`` of a quib
are indicated by its repr representation. Consider the following
example:

.. code:: python

    # Imports
    import pyquibbler as qb
    from pyquibbler import iquib
    qb.override_all()
    import numpy as np

.. code:: python

    n = iquib(6)
    numbers = np.arange(n**2)
    total = np.sum(numbers)
    total




.. parsed-literal::

    total = sum(numbers)



The string to the left of the equal sign is the ``assigned_name`` of the
quib (in this case, ‘total’), and the string to the right of the equal
sign is the ``functional_representation`` (in this case,
‘sum(numbers)’).

The ‘functional_representation’ property
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The property :py:attr:`~pyquibbler.Quib.functional_representation` is a read-only property
automatically assigned to a quib to represent its function and
arguments. This automatically assigned string is displayed after the
equal sign in the quib repr and can also be accessed directly through
the ``functional_representation`` property:

.. code:: python

    n.functional_representation




.. parsed-literal::

    'iquib(6)'



.. code:: python

    numbers.functional_representation




.. parsed-literal::

    'arange(n ** 2)'



.. code:: python

    total.functional_representation




.. parsed-literal::

    'sum(numbers)'



The ‘assgined_name’ property
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:attr:`~pyquibbler.Quib.assigned_name` property is a string indicating the name of
the quib as assigned by the user. The ``assigned_name`` is set either by
explicit assignment, or by inference according to the name of the
variable to which the quib is assigned. This assigned name is displayed
before the equal sign in the quib repr and can also be accessed by the
``assigned_name`` property:

.. code:: python

    numbers.assigned_name




.. parsed-literal::

    'numbers'



The quib’s assigned_name can be different than the name of the variable of the quib.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, upon creation of a new quib, its ``assigned_name`` is
automatically set as the name of the variable of the quib (e.g., the
statement ``numbers = np.arange(n**2 + 1)`` above, created a quib
``numbers`` and assigned the name ‘numbers’ as its ``assigned_name``. In
general though, a quib name does not need to be the same as the name of
the variable holding the quib. To begin with, while each quib has a
single ``assigned_name``, it can be pointed to by multiple different
variables with different names (for example, if we set
``numbers_copy = numbers``, then ``numbers_copy.assigned_name`` will
equal ‘numbers’ not ‘numbers_copy’). Furthermore, at the practical
level, it is often useful to use different assigned_names and variable
names. For example, assigning a comprehensive description of the quib as
the ``assigned_name``, which can also include spaces, and assigning a
shorter, more compact, name for the variable pointing to it.

In the above example, the user may choose for instance to rename
numbers:

.. code:: python

    numbers.assigned_name = 'numbers from zero to sqr_n minus one'
    numbers.assigned_name




.. parsed-literal::

    'numbers from zero to sqr_n minus one'



The quib’s assigned_name is also used to name quib-associated files.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Note that besides providing a comprehensive description of the quib, the
quib’s ``assigned_name`` is also used to define the name of the quib’s
linked input file if any (see :doc:`Project-save-load`).

Quibs without an assigned_name represent an intermediate analysis step.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Quibs do not need to be named; they can have their
``assigned_name=None``, indicating unnamed quibs. Unnamed quibs
typically represent intermediate analysis steps.

For example, when we defined ``numbers = np.arange(n**2)``, an
intermediate quib ``n**2`` was created:

.. code:: python

    numbers.parents




.. parsed-literal::

    {n ** 2}



This intermediate quib has no assigned ``assigned_name``:

.. code:: python

    n2 = next(iter(numbers.parents))
    print(n2.assigned_name)


.. parsed-literal::

    None


The ‘name’ property
~~~~~~~~~~~~~~~~~~~

The :py:attr:`~pyquibbler.Quib.name` property of a quib is defined as its ``assigned_name``
if specified, or as its ``functional_representation`` if
``assigned_name`` is ``None``.

.. code:: python

    total.name




.. parsed-literal::

    'total'



.. code:: python

    total.set_assigned_name(None)
    total.name




.. parsed-literal::

    'sum(numbers from zero to sqr_n minus one)'



Setting the ``name`` property is equivalent to setting the
``assigned_name`` property.

The ‘functional_representation’ of a quib changes dynamically.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``functional_representation`` of a quib is a dynamic property that
changes to reflect changes in the names of quib arguments, recursively.

For example, if we set ``numbers`` to as un-named:

.. code:: python

    total.assigned_name = None

then the name of the downstream quib ``total`` is updated:

.. code:: python

    total.name




.. parsed-literal::

    'sum(arange(n ** 2))'



Changing the name of ``n`` will now also be reflected downstream:

.. code:: python

    n.name = 'number_of_values'
    total.name




.. parsed-literal::

    'sum(arange(number_of_values ** 2))'



See also:
^^^^^^^^^

:py:attr:`~pyquibbler.Quib.name`, :py:attr:`~pyquibbler.Quib.assigned_name`,
:py:attr:`~pyquibbler.Quib.functional_representation`

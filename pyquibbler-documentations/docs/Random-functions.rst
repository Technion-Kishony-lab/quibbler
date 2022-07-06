Random functions
----------------

Random functions can be implemented in *Quibbler* using *random* quibs.
Random quibs are function quibs that call random functions, specified
with ``is_random`` property. Defining a quib running a random function
automatically caches its output, so that multiple requests for its value
give the same random realization (quenched randomness). Then, to refresh
randomization, we invalidate the cached values of these random quibs.
Such re-randomization can be done either centrally for all random quibs,
or individually for each given random quib. Such invalidation of random
quibs will then invalidate any downstream calculations that depend on
these random values, causing re-evaluated of the random function upon
downstream output request.


Import
~~~~~~

.. code:: python

    import pyquibbler as qb
    from pyquibbler import iquib
    qb.initialize_quibbler()
    import numpy as np

Quibs calling *NumPy* random functions are automatically defined as random quibs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, all standard *NumPy* functions that generate random output
are automatically implemented as random function quibs. We can therefore
define random quibs simply by calling *NumPy* random functions with quib
arguments.

For example,

.. code:: python

    n = iquib(3)
    rand_numbers = np.random.rand(n)
    rand_numbers.get_value()




.. code:: none

    array([0.24936599, 0.49959145, 0.70940961])



.. code:: python

    rand_numbers.is_random




.. code:: none

    True



Random quibs always cache their results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Random quibs always cache their results, so repeated calls for their
value yields the same randomization:

.. code:: python

    rand_numbers.get_value()




.. code:: none

    array([0.24936599, 0.49959145, 0.70940961])



Because the randomization is fixed, mathematical trivialities hold true:

.. code:: python

    rand_numbers_plus_1 = rand_numbers + 1
    should_equal_zero = np.sum(rand_numbers_plus_1 - rand_numbers) - n
    should_equal_zero.get_value()




.. code:: none

    0.0



Refreshing randomization
~~~~~~~~~~~~~~~~~~~~~~~~

The cache of the random quibs can be invalidated either centrally for
all random quibs, or individually for a given specific random quib. Upon
invalidation, all downstream dependent quibs are also invalidated.
Requesting the value of such downstream calculations will then lead to
recalculation of the random function (re-randomization).

**Central re-randomization of all random quibs.** To simply refresh
randomization of all the random quibs in an entire analysis pipeline, we
use the ``reset_random_quibs`` function. All downstream results are also
invalidated and upon request for their value, new randomization will be
calculated:

.. code:: python

    rand_numbers_plus_1.get_value()




.. code:: none

    array([1.24936599, 1.49959145, 1.70940961])



.. code:: python

    qb.reset_random_quibs()
    rand_numbers_plus_1.get_value()




.. code:: none

    array([1.76673854, 1.29385858, 1.72750647])



**Quib-specific re-randomization.** To specifically refresh the
randomization of a given chosen random quib, we can invalidate its cache
using the ``invalidate`` method. Any function quibs downstream of this
specific quib will thereby also invalidate. Request the value of such
downstream results will lead to new randomization:

.. code:: python

    rand_numbers.invalidate()
    rand_numbers_plus_1.get_value()




.. code:: none

    array([1.44229483, 1.94557109, 1.37758801])



User-defined randmon functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To implement quibs that call user defined random functions, we can set
the ``is_random`` property of the function to ``True``, when converting
it to a quiby function using the :py:func:`~pyquibbler.quiby` decorator:

.. code:: python

    @qb.quiby(is_random=True)
    def sum_of_dice(n: int):
        return np.sum(np.random.randint(1, 7, n))
    
    num_dice = iquib(4)
    sum_dice = sum_of_dice(n)
    sum_dice.get_value()




.. code:: none

    13



.. code:: python

    sum_dice.get_value()




.. code:: none

    13



.. code:: python

    qb.reset_random_quibs()
    sum_dice.get_value()




.. code:: none

    11



Examples
~~~~~~~~

For an example of an *Quibbler* app with random quibs, see:

-  :doc:`examples/quibdemo_fft`
-  :doc:`examples/quibdemo_random_quibs_dice`

from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Any, Optional, Type

from pyquibbler.env import SAFE_MODE
from pyquibbler.exceptions import PyQuibblerException


# Exceptions:

class BaseRunnerFailedException(PyQuibblerException, ABC):
    """
    A base class of exceptions runners should raise if they do not manage to perform their job.
    These exceptions are caught by MultipleInstanceRunner.
    """


@dataclass
class RunnerFailedException(BaseRunnerFailedException):
    """
    A generic exception runners should raise if they do not manage to perform their job.
    """

    message: Any

    def __str__(self):
        return f"Runner failed performing job.\n{self.message}"


class NoRunnerWorkedException(PyQuibblerException):
    """
    An exception raised by Multiple InstanceRunner if no runners were successful.
    """
    def __str__(self):
        return 'No runner managed to do the work.'


# Run condition, and conditional runner:

class RunCondition(Enum):
    """
    Defines the condition of a run.
    """
    pass


class ConditionalRunner(ABC):
    """
    A runner that runs only when:
    (a) the run_condition matches the runner's list of RUN_CONDITIONS.
    (b) the runner returns True when asked if it can_try.
    """

    # Define the list of run condition at which the runner should be asked whether it wants to try.
    # [] to run only if the run_condition is None.
    # None to run at all conditions.
    RUN_CONDITIONS: Optional[List[RunCondition]] = None

    @classmethod
    def is_matching_run_condition(cls, run_condition: RunCondition) -> bool:
        return run_condition is None \
               or cls.RUN_CONDITIONS is None \
               or run_condition in cls.RUN_CONDITIONS

    def can_try(self) -> bool:
        """
        Assuming RUN_CONDITIONS are met, perform additional tests to decide if runner can try running.
        """
        return True

    @abstractmethod
    def try_run(self):
        """
        Try running. Return the result if possible. If not, raise an instance of BaseRunnerFailedException.
        Or, call _raise_run_failed_exception().
        """
        pass

    def _raise_run_failed_exception(self, message: Any = ''):
        """
        Should be called to terminate try_run without success.
        """
        raise RunnerFailedException(message)


# multiple instance runner:

class MultipleInstanceRunner:
    """
    Attempting to backward translate paths, type or shape, or to invert, we are taking an escalating approach.
    We try to see if we can do this without shape and type, and if not, we add more information which may ultimately
    require us to evaluate the quib function, which we do at last resort.

    The MultipleInstanceRunner takes care of this escalating trying approach. It gets the run condition and
    tries to sequentially run all the runners that can work in this condition. If nothing works, the condition is
    escalated.

    A runner is elected to do the job in three steps:
    (1) To get created, its RUN_CONDITIONS list must include the RunCondition.
    (2) Once created, it's can_try() function is called. Based on the data it can decide whether it wants to
    try running.
    (3) try_run is then called. If during the call the runner sees conditions that preclude completing the job,
    it can raise BaseRunnerFailedException.

    If no runners managed to run successfully, we raise NoRunnerWorkedException, and we should then be called again
    with a higher RunCondition state.
    """

    def __init__(self, run_condition: Optional[RunCondition],
                 runner_types: List[Type[ConditionalRunner]], *args, **kwargs):
        # Run only runners matching run_condition and whose can_try returns True.
        # run_condition=None will run all runners.
        self._run_condition = run_condition
        self._runner_types = runner_types

        # args/kwargs to transfer to the runner:
        self._args = args
        self._kwargs = kwargs

    def run(self):
        """
        Call all the matching runners until one of them succeeds.
        """
        for runner_type in self._runner_types:
            if runner_type.is_matching_run_condition(self._run_condition):
                runner = runner_type(*self._args, **self._kwargs)
                if runner.can_try():
                    try:
                        return runner.try_run()
                    except BaseRunnerFailedException:
                        pass
                    except Exception as e:
                        if SAFE_MODE:
                            pass
                        else:
                            raise e

        raise NoRunnerWorkedException()

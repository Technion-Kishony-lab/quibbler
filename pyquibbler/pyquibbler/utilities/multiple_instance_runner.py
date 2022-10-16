import dataclasses
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Any, Optional, Type

from pyquibbler.exceptions import PyQuibblerException


# Exceptions:

class BaseRunnerFailedException(PyQuibblerException, ABC):
    """
    A base class of exceptions runners should raise if they do not manage to perform their job.
    These exceptions are caught by MultipleInstanceRunner.
    """


class RunnerCannotRunException(BaseRunnerFailedException):
    """
    A base class of exceptions runners should raise if they do not manage to perform their job.
    """
    def __str__(self):
        return "Conditions were not met for runner to run."


@dataclasses.dataclass
class RunnerFailedException(BaseRunnerFailedException):
    """
    A base class of exceptions runners should raise if they do not manage to perform their job.
    """

    message: Any

    def __str__(self):
        return f"Conditions were not met for runner to run.\n{self.message}"


class NoRunnerWorkedException(PyQuibblerException):
    """
    An exception raised if no runners were successful.
    """
    def __str__(self):
        return 'No runner managed to do the work.'


# Run condition, and conditional runner:

class RunCondition(Enum):
    """
    Defines the condition at which a runner can run.
    """
    pass


class ConditionalRunner(ABC):
    """
    A runner that runs only when the run_condition of the MultipleInstanceRunner matches the list of RUN_CONDITIONS
    of the runner.
    """

    # Define the list of run condition at which the runner should run.
    # [] to not run at all
    # None to run at all conditions.
    RUN_CONDITIONS: Optional[List[RunCondition]] = None

    def can_try(self) -> bool:
        """
        Perform additional tests, beyond RunCondition, to decide if runner can try running.
        """
        return True

    @abstractmethod
    def try_run(self):
        pass

    def _raise_run_failed_exception(self, message: Any = ''):
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

    def _get_runner_types_matching_condition(self) -> List[Type[ConditionalRunner]]:
        """
        Returns the list of relevant runners matching the run condition
        """
        if self._run_condition is None:
            return self._runner_types
        return [runner for runner in self._runner_types
                if runner.RUN_CONDITIONS is None or self._run_condition in runner.RUN_CONDITIONS]

    def run(self):
        for runner_type in self._get_runner_types_matching_condition():
            runner = runner_type(*self._args, **self._kwargs)
            if runner.can_try():
                try:
                    return runner_type(*self._args, **self._kwargs).try_run()
                except BaseRunnerFailedException:
                    pass
        raise NoRunnerWorkedException()

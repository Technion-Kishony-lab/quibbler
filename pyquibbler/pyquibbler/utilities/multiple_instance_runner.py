import dataclasses
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Any, Optional, Type

from pyquibbler.exceptions import PyQuibblerException


class RunnerFailedException(PyQuibblerException, ABC):
    """
    A base class of exceptions runners should raise if they do not manage to perform their job.
    """
    pass


@dataclasses.dataclass
class NoRunnerWorkedException(PyQuibblerException):
    """
    An exception raised if no runners were successful.
    """
    message: Any

    def __str__(self):
        return f'No runner managed to do the work.\n{self.message}'


class RunCondition(Enum):
    """
    Defines the condition at which a runner can run.
    """
    pass


class ConditionalRunner:
    """
    A runner that runs only when the run_condition of the MultipleInstanceRunner matches the list of RUN_CONDITIONS
    of the runner.
    """

    # Define the list of run condition at which the runner should run.
    # [] to not run at all
    # None to run at all conditions.
    RUN_CONDITIONS: Optional[List[RunCondition]] = None


class MultipleInstanceRunner(ABC):
    """
    Attempting to backward translate paths, type or shape, or to invert, we are taking an escalating approach.
    We try to see if we can do this without shape and type, and if not, we add more information which may ultimately
    require us to evaluate the quib function, which we do at last resort.

    The MultipleInstanceRunner takes care of this escalating trying approach. It gets the run condition and
    trying ot sequentially run all the runners that can work in this condition. If nothing works, the condition is
    escalated.

    A runner that cannot do the translation job should raise RunnerFailedException.
    Note that a runner can elect to run in more than one condition, raising RunnerFailedException the first time
    it is called to be called again with more data.

    If no runners managed to run successfully, we raise NoRunnerWorkedException.
    """

    def __init__(self, run_condition: Optional[RunCondition]):
        # Run only runners matching run_condition.
        # run_condition=None will run all runners.
        self._run_condition = run_condition

    @abstractmethod
    def _get_all_runners(self) -> List[Type[ConditionalRunner]]:
        """
        Returns the list of all runners
        """
        pass

    def _get_runners_matching_condition(self) -> List[Type[ConditionalRunner]]:
        """
        Returns the list of relevant runners matching the run condition
        """
        all_runners = self._get_all_runners()
        if self._run_condition is None:
            return all_runners
        return [runner for runner in all_runners
                if runner.RUN_CONDITIONS is None or self._run_condition in runner.RUN_CONDITIONS]

    @abstractmethod
    def _get_exception_message(self):
        pass

    @abstractmethod
    def _run_runner(self, runner: Any):
        pass

    def run(self):
        for runner in self._get_runners_matching_condition():
            try:
                return self._run_runner(runner)
            except RunnerFailedException:
                pass
        raise NoRunnerWorkedException(self._get_exception_message())

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional, Callable, Any, Set, Mapping, List, Tuple, Type

from pyquibbler import Assignment
from pyquibbler.iterators import iter_objects_of_type_in_object_shallowly
from pyquibbler.path_translators.exceptions import CannotInvertException, NoInvertersFoundException
from pyquibbler.path_translators.inversal_types import ArgumentWithValue, Source, SourceType
from pyquibbler.quib.function_quibs.utils import ArgsValues, FuncWithArgsValues
from pyquibbler.overriding.overriding import get_definition_for_function


class Inverter(ABC):

    SUPPORTING_FUNCS: Set[Callable] = set()
    PRIORITY = 0

    def __init__(self,
                 func_with_args_values: FuncWithArgsValues,
                 assignment: Assignment,
                 previous_result: Any
                 ):
        self._func_with_args_values = func_with_args_values
        self._assignment = assignment
        self._previous_result = previous_result

    def supports_func(self, func: Callable):
        return func in self.SUPPORTING_FUNCS

    @property
    def func(self):
        return self._func_with_args_values.func

    @property
    def args_values(self):
        return self._func_with_args_values.args_values

    @property
    def _args(self):
        return self.args_values.args

    @property
    def _kwargs(self):
        return self.args_values.kwargs

    @property
    def func_definition(self):
        return get_definition_for_function(self.func)

    def _get_data_source_arguments_with_values(self) -> List[ArgumentWithValue]:
        return [
            ArgumentWithValue(argument=argument, value=self.args_values[argument])
            for argument in self.func_definition.data_source_arguments
        ]

    @lru_cache()
    def _get_data_sources(self) -> Set[Source]:
        return set(iter_objects_of_type_in_object_shallowly(Source, [
            self.args_values[argument] for argument in self.func_definition.data_source_arguments
        ]))

    @abstractmethod
    def get_inversals(self):
        pass


def invert(func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any], assignment: Assignment, previous_result):
    from pyquibbler.path_translators.translators import INVERTERS
    # TODO test multiple scenarios with choosing inverters
    potential_inverter_classes = [cls for cls in INVERTERS if func.__name__ in [f.__name__ for f in cls.SUPPORTING_FUNCS]]
    potential_inverter_classes = list(sorted(potential_inverter_classes, key=lambda c: c.PRIORITY))
    if len(potential_inverter_classes) == 0:
        raise NoInvertersFoundException(func)
    while True:
        cls = potential_inverter_classes.pop()
        inverter = cls(
            func_with_args_values=FuncWithArgsValues.from_function_call(
                func=func,
                args=args,
                kwargs=kwargs,
                include_defaults=True
            ),
            assignment=assignment,
            previous_result=previous_result
        )
        try:
            return inverter.get_inversals()
        except CannotInvertException:
            pass

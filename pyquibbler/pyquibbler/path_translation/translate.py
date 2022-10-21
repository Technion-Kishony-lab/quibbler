from typing import Type, Dict, Optional

from pyquibbler.utilities.multiple_instance_runner import MultipleInstanceRunner
from pyquibbler.path import Path, Paths

from .source_func_call import SourceFuncCall
from .base_translators import BackwardsTranslationRunCondition
from .types import Source
from ..function_definitions import SourceLocation
from ..utilities.general_utils import Shape


def backwards_translate(run_condition: BackwardsTranslationRunCondition,
                        func_call: SourceFuncCall,
                        path: Path,
                        shape: Optional[Shape] = None,
                        type_: Optional[Type] = None,
                        **kwargs) -> Dict[Source, Path]:
    """
    Backwards translate a path given a func_call
    This gives a mapping of sources to paths that were referenced in given path in the result of the function
    """
    return MultipleInstanceRunner(run_condition=run_condition,
                                  runner_types=func_call.func_definition.backwards_path_translators,
                                  func_call=func_call, path=path, shape=shape, type_=type_, **kwargs).run()


def forwards_translate(func_call: SourceFuncCall, source: Source, source_location: SourceLocation,
                       path: Path, shape: Optional[Shape] = None, type_: Optional[Type] = None,
                       **kwargs) -> Paths:
    """
    Forwards translate a mapping of sources to paths through a function, giving for each source a list of paths that
    were affected by the given path for the source
    """
    return MultipleInstanceRunner(run_condition=None, runner_types=func_call.func_definition.forwards_path_translators,
                                  func_call=func_call, source=source, source_location=source_location, path=path,
                                  shape=shape, type_=type_, **kwargs).run()

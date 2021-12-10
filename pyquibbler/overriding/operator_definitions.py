import operator
from operator import getitem

from pyquibbler.overriding.definitions import OverrideDefinition
from pyquibbler.overriding.types import IndexArgument

OPERATOR_DEFINITIONS = [OverrideDefinition(
    func_name='getitem',
    module_or_cls=operator,
    data_source_arguments={IndexArgument(0)}
)]


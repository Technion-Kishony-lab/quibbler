from .transpositional.transpositional_path_translator import ForwardsTranspositionalTranslator, \
    BackwardsTranspositionalTranslator
from .transpositional.getitem_translator import BackwardsGetItemTranslator
from .axeswise import ReductionAxiswiseForwardsPathTranslator, ReductionAxiswiseBackwardsPathTranslator, \
    AccumulationForwardsPathTranslator, AccumulationBackwardsPathTranslator
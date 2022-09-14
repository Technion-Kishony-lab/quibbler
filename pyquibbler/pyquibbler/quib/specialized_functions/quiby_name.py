from pyquibbler.translation.translators.quiby_name.quiby_name import \
    BackwardsQuibyNameTranslator, ForwardsQuibyNameTranslator
from pyquibbler.utilities.decorators import assign_func_name
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.func_calling.quiby_name_func_call import QuibyNameFuncCall


@assign_func_name('quiby_name')  # For the pretty functional_representation
def get_quiby_name(quib: Quib):
    return quib.name


quiby_name_definition = create_func_definition(
    is_graphics=False,
    is_random=False,
    lazy=True,
    raw_data_source_arguments=[0],
    backwards_path_translators=[BackwardsQuibyNameTranslator],
    forwards_path_translators=[ForwardsQuibyNameTranslator],
    quib_function_call_cls=QuibyNameFuncCall,
)


def quiby_name(quib: Quib) -> Quib:
    """
    Returns a quib representing the name of an input quib.

    Parameters
    ----------
    quib : Quib
        The quib whose name to represent.

    Returns
    -------
    Quib

    See Also
    --------
    q, quiby, Quib.name, Quib.assigned_name
    """

    return create_quib(
        func=get_quiby_name,
        args=(quib,),
    )


add_definition_for_function(func=get_quiby_name,
                            func_definition=quiby_name_definition,
                            quib_creating_func=quiby_name)

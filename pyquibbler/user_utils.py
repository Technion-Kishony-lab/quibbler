from pyquibbler.quib import DefaultFunctionQuib

q = lambda func, *args, **kwargs: DefaultFunctionQuib.create(func=func, func_args=args, func_kwargs=kwargs)

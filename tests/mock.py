from six import wraps

from .fixtures import customer, staff_user


class Default(object):
    pass


class QuadeMock:

    """
    Monkey patch the FixtureManager's registry, and automatically unapply the patch afterwards.
    """

    def __init__(self, mdle, funcs=Default):
        self.module = mdle
        if funcs == Default:
            funcs = [customer, staff_user]
        self.funcs = funcs

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            original_registry = self.module.manager._registry
            # Monkey patch the registry.
            self.module.manager._registry = {func.__name__: func for func in self.funcs}

            try:
                # Run the wrapped function (e.g. a test).
                wrapped_fn_return_value = fn(*args, **kwargs)
            except:
                raise
            else:
                return wrapped_fn_return_value
            finally:
                # Restore the original registry.
                self.module.manager._registry = original_registry

        return wrapper

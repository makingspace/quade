from six import wraps

from .fixtures import customer, staff_user


class QaMock:

    """
    Monkey patch the FixtureManager's registry, and automatically unapply the patch afterwards.
    """

    def __init__(self, mdle):
        self.module = mdle

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            original_registry = self.module.manager._registry
            # Monkey patch the registry.
            self.module.manager._registry = {
                'customer': customer,
                'staff_user': staff_user,
            }

            # Run the wrapped function (e.g. a test).
            wrapped_fn_return_value = fn(*args, **kwargs)

            # Restore the original registry.
            self.module.manager._registry = original_registry

            return wrapped_fn_return_value

        return wrapper

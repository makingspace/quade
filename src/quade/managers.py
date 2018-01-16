from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import str as text
import importlib

from django.conf import settings
from django.db import transaction


class ConfigurationError(Exception):
    """
    A test configuration tried to execute a function that is not registered.
    """
    def __init__(self, unregistered_functions):
        self.unregistered_functions = unregistered_functions


class FixtureManager:
    def __init__(self):
        self._registry = {}

    def register(self, func):
        self._registry[func.__name__] = func

    @property
    def registry(self):
        return self._registry

    def setup(self):
        importlib.import_module(settings.QUADE.fixtures_file)

    def execute(self, config):
        instructions = []
        for step in config:
            func_name, kwargs = step
            func = self._registry[func_name]
            output = func(**kwargs)
            instructions.append(text(output))
        return '\n'.join(instructions)

    def validate(self, config):
        """
        :return: raises or None
        """
        func_names = set(step[0] for step in config)
        registered_funcs = set(self._registry.keys())
        unregistered_funcs = func_names - registered_funcs
        if unregistered_funcs:
            raise ConfigurationError(unregistered_funcs)


manager = FixtureManager()  # Singleton pattern.


def register(func):
    """
    Register a function with the FixtureManager. Also wraps the function in an atomic transaction.
    """
    func = transaction.atomic(func)
    manager.register(func)
    return func

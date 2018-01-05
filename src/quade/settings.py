# This module is inspired by and indebted to Hypothesis' _settings module.
# https://github.com/HypothesisWorks/hypothesis-python/blob/master/src/hypothesis/_settings.py
from collections import Iterable
from inspect import cleandoc

from attr import attrib, attrs
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from six import with_metaclass


__all__ = [
    'AllEnvs',
    'DebugEnvs',
    'Settings',
    'is_superuser',
]


@attrs
class Setting(object):
    """A descriptor that prevents deletion and provides a docstring."""
    name = attrib()
    default = attrib()
    default_description = attrib(default='')
    description = attrib(default='')
    validator = attrib(default=None)

    def __get__(self, obj, objtype=None):
        if obj is None:  # pragma: no cover
            return self
        else:
            try:
                return obj.__dict__[self.name]
            except KeyError:  # pragma: no cover
                raise AttributeError(self.name)

    def __set__(self, obj, value):
        obj.__dict__[self.name] = value

    def __delete__(self, obj):
        raise AttributeError('Cannot delete attribute {}'.format(self.name))

    @property
    def __doc__(self):
        return "{}\n\nDefault: {}".format(
            cleandoc(self.description),
            self.default_description or '``{}``'.format(self.default)
        )


class AllEnvs(object):
    """Enable Quade unconditionally."""
    @staticmethod
    def func(_): return True


class DebugEnvs(object):
    """Enable Quade if the environment has DEBUG = True."""
    @staticmethod
    def func(s): return s.DEBUG


def is_superuser(view):
    """Allow access to the view if the requesting user is a superuser."""
    return view.request.user.is_superuser


all_settings = {}


def validate_allowed_envs(val):
    if any([val in [AllEnvs, DebugEnvs], callable(val), isinstance(val, Iterable)]):
        return val
    else:
        raise TypeError


def validate_access_test_func(val):
    if callable(val):
        return val
    else:
        raise TypeError


class SettingsMeta(type):

    def __new__(cls, name, bases, dct):
        obj = super(SettingsMeta, cls).__new__(cls, name, bases, dct)
        obj.define_setting(
            name='fixtures_file',
            default='quade.fixtures',
            description="""A dotted path to the location of your fixtures.""",
        )
        obj.define_setting(
            name='allowed_envs',
            default=DebugEnvs,
            default_description=""":class:`.DebugEnvs`""",
            description="""Controls which environments Quade can run on.

            Allowed values are:

            - :class:`.DebugEnvs`

            - :class:`.AllEnvs`

            - a string -- your ``django.conf.settings.ENV`` is compared exactly to this string

            - an iterable -- your ``django.conf.settings.ENV`` is checked exactly for membership in
              the iterable

            - any callable that accepts one argument, the Django settings object

            If Quade is not enabled, fixtures will not be loaded, but views will be available to
            users with appropriate access, application models and tables can be accessed, etc.
            """,
            validator=validate_allowed_envs,
        )
        obj.define_setting(
            name='access_test_func',
            default=is_superuser,
            default_description=""":func:`.is_superuser`""",
            description="""A callable that restricts access to Quade's views. The callable should
            accept one argument (a Django view class).""",
            validator=validate_access_test_func
        )
        return obj


class Settings(with_metaclass(SettingsMeta)):

    _WHITELISTED_PROPERTIES = ['_construction_complete']

    def __init__(self, **kwargs):
        self._construction_complete = False
        for setting in all_settings.values():
            val = kwargs.pop(setting.name, setting.default)
            if setting.validator:
                try:
                    val = setting.validator(val)
                except:
                    raise ImproperlyConfigured(
                        "{} is not a valid value for Quade setting {}".format(val, setting.name)
                    )
            setattr(self, setting.name, val)
        if kwargs:
            suffix = '' if len(kwargs) == 1 else 's'
            raise AttributeError("No such setting{}: '{}'".format(suffix, "', '".join(kwargs.keys())))
        self._construction_complete = True

    @classmethod
    def define_setting(cls, name, **kwargs):
        s = Setting(name, **kwargs)
        all_settings[name] = s
        setattr(cls, name, s)

    @property
    def allowed(self):
        """Based on the settings, determine if scenarios are allowed to run on this environment."""
        if self.allowed_envs in [AllEnvs, DebugEnvs]:
            func = self.allowed_envs.func
        elif callable(self.allowed_envs):
            func = self.allowed_envs
        elif isinstance(self.allowed_envs, six.string_types):
            def func(s): return s.ENV == self.allowed_envs
        elif isinstance(self.allowed_envs, Iterable):
            def func(s): return s.ENV in self.allowed_envs

        if func(settings):
            return True
        else:
            return False

    def __setattr__(self, key, value):
        if key in self._WHITELISTED_PROPERTIES:
            return super(Settings, self).__setattr__(key, value)
        elif key in all_settings:
            if self._construction_complete:
                raise RuntimeError('Quade settings may not be modified during runtime.')
            else:
                return super(Settings, self).__setattr__(key, value)
        else:  # pragma: no cover
            raise AttributeError('No such setting {}'.format(key))

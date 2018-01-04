from collections import Iterable

from attr import attrib, attrs
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import six


__all__ = [
    'AllEnvs',
    'DebugEnvs',
    'Settings',
]


@attrs
class Setting(object):
    name = attrib()
    default = attrib()
    validator = attrib(default=None)


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


def define_setting(name, **kwargs):
    s = Setting(name, **kwargs)
    all_settings[name] = s
    return s


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


define_setting(name='fixtures_file', default='quade.fixtures')
define_setting(name='allowed_envs', default=DebugEnvs, validator=validate_allowed_envs)
define_setting(name='access_test_func', default=is_superuser, validator=validate_access_test_func)


class Settings(object):

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

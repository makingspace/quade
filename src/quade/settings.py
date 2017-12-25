from collections import Iterable

from attr import attrib, attrs
from django.conf import settings
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


class AllEnvs(object):
    """Enable Quade unconditionally."""
    @staticmethod
    def func(_): return True


class DebugEnvs(object):
    """Enable Quade if the environment has DEBUG = True."""
    @staticmethod
    def func(s): return s.DEBUG


all_settings = {}


def define_setting(name, **kwargs):
    s = Setting(name, **kwargs)
    all_settings[name] = s
    return s


define_setting(name='fixtures_file', default='quade.fixtures')
define_setting(name='allowed_envs', default=DebugEnvs)


class Settings(object):

    _WHITELISTED_PROPERTIES = ['_construction_complete']

    def __init__(self, **kwargs):
        self._construction_complete = False
        for setting in all_settings.values():
            val = kwargs.pop(setting.name, setting.default)
            setattr(self, setting.name, val)
        if kwargs:
            suffix = '' if len(kwargs) == 1 else 's'
            raise AttributeError("No such setting{}: '{}'".format(suffix, "', '".join(kwargs.keys())))
        self._modify_installed_apps()
        self._construction_complete = True

    def _modify_installed_apps(self):
        """Based on the settings, possibly modify INSTALLED_APPS to activate Quade."""
        if self.allowed_envs in [AllEnvs, DebugEnvs]:
            func = self.allowed_envs.func
        elif callable(self.allowed_envs):
            func = self.allowed_envs
        elif isinstance(self.allowed_envs, six.string_types):
            def func(s): return s.ENV == self.allowed_envs
        elif isinstance(self.allowed_envs, Iterable):
            def func(s): return s.ENV in self.allowed_envs
        else:
            raise TypeError("Value '{}' for 'allowed_envs' is an unexpected type".format(
                    self.allowed_envs)
            )

        if func(settings):
            settings.INSTALLED_APPS += ['quade']
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

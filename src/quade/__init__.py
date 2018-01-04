from __future__ import unicode_literals

from .settings import AllEnvs, DebugEnvs, Settings


__all__ = [
    'AllEnvs',
    'DebugEnvs',
    'Settings',
]


__version__ = '0.0.1'
default_app_config = 'quade.apps.QuadeConfig'

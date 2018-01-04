from __future__ import absolute_import, division, print_function, unicode_literals

from django.apps import AppConfig
from django.conf import settings

from .managers import manager


class QaConfig(AppConfig):
    name = 'quade'

    def ready(self):
        if settings.QUADE.allowed:
            manager.setup()

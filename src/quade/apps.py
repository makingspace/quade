from __future__ import absolute_import, division, print_function, unicode_literals

from django.apps import AppConfig

from .managers import manager


class QaConfig(AppConfig):
    name = 'quade'

    def ready(self):
        manager.setup()
